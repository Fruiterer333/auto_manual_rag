from time import perf_counter

from app.core.config import Settings
from app.core.logger import get_logger
from app.data.schemas.models import RetrievedChunk
from app.rag.retrievers.bm25_retriever import BM25Retriever
from app.rag.retrievers.chunk_filters import (
    deduplicate_chunks_by_content,
    filter_retrieval_chunks,
)
from app.rag.retrievers.chroma_retriever import ChromaRetriever


logger = get_logger(__name__)


class HybridRetriever:
    """Dense/BM25 retriever with RRF fusion."""

    VALID_MODES = {"dense", "bm25", "hybrid"}

    def __init__(
        self,
        settings: Settings,
        dense_retriever: ChromaRetriever | None = None,
        bm25_retriever: BM25Retriever | None = None,
    ) -> None:
        self.settings = settings
        self.dense_retriever = dense_retriever or ChromaRetriever(settings)
        self.bm25_retriever = bm25_retriever or BM25Retriever(settings)
        self.last_debug_info: dict = {}

    def search(
        self,
        question: str,
        query_embedding: list[float],
        top_k: int,
        candidate_k: int,
        retrieval_mode: str | None = None,
    ) -> list[RetrievedChunk]:
        mode = retrieval_mode or self.settings.RETRIEVAL_MODE
        if mode not in self.VALID_MODES:
            raise ValueError(f"Invalid retrieval_mode: {mode}")

        start_time = perf_counter()
        dense_results: list[RetrievedChunk] = []
        bm25_results: list[RetrievedChunk] = []
        if mode in {"dense", "hybrid"}:
            dense_results = self.dense_retriever.search(
                query_embedding=query_embedding,
                top_k=max(candidate_k, self.settings.DENSE_CANDIDATE_K),
            )
            dense_results = self._annotate_rank(dense_results, "dense")
            dense_results, dense_filter_summary = filter_retrieval_chunks(
                dense_results,
                stage="hybrid_pre_fusion_dense" if mode == "hybrid" else "dense_search_post",
            )
        else:
            dense_filter_summary = {}
        if mode in {"bm25", "hybrid"}:
            bm25_results = self.bm25_retriever.search(
                query=question,
                top_k=max(candidate_k, self.settings.SPARSE_CANDIDATE_K),
            )
            bm25_results = self._annotate_rank(bm25_results, "bm25")
            bm25_results, bm25_filter_summary = filter_retrieval_chunks(
                bm25_results,
                stage="hybrid_pre_fusion_bm25" if mode == "hybrid" else "bm25_search_post",
            )
        else:
            bm25_filter_summary = {}

        if mode == "dense":
            fused = self._mark_source(dense_results, "dense")[:top_k]
        elif mode == "bm25":
            fused = self._mark_source(bm25_results, "bm25")[:top_k]
        else:
            fused = self._rrf_fuse(
                dense_results=dense_results,
                bm25_results=bm25_results,
                top_k=max(top_k, self.settings.HYBRID_FUSION_TOP_K),
            )
        fused, fused_filter_summary = filter_retrieval_chunks(
            fused,
            stage="hybrid_post_fusion",
        )
        fused, fused_dedup_summary = deduplicate_chunks_by_content(
            fused,
            stage="hybrid_post_fusion",
        )
        fused = fused[:top_k]
        self.last_debug_info = {
            "retrieval_mode": mode,
            "dense_filter_summary": dense_filter_summary,
            "bm25_filter_summary": bm25_filter_summary,
            "fused_filter_summary": fused_filter_summary,
            "fused_dedup_summary": fused_dedup_summary,
            **getattr(self.bm25_retriever, "last_debug_info", {}),
        }

        logger.info(
            "Hybrid retrieval completed: mode=%s dense_count=%s bm25_count=%s fused_count=%s dense_filter=%s bm25_filter=%s fused_filter=%s fused_dedup=%s top_chunk_ids=%s elapsed=%.2fs",
            mode,
            len(dense_results),
            len(bm25_results),
            len(fused),
            dense_filter_summary,
            bm25_filter_summary,
            fused_filter_summary,
            fused_dedup_summary,
            [item.chunk.chunk_id for item in fused[:5]],
            perf_counter() - start_time,
        )
        return fused

    def find_neighbor_chunks(self, *args, **kwargs):
        return self.dense_retriever.find_neighbor_chunks(*args, **kwargs)

    def _annotate_rank(self, results: list[RetrievedChunk], source: str) -> list[RetrievedChunk]:
        annotated: list[RetrievedChunk] = []
        for rank, item in enumerate(results, start=1):
            chunk = item.chunk
            metadata = dict(chunk.metadata)
            if source == "dense":
                metadata.update(
                    {
                        "dense_rank": rank,
                        "dense_score": item.score,
                        "retrieval_source": "dense",
                    }
                )
            else:
                metadata.update(
                    {
                        "bm25_rank": rank,
                        "bm25_score": item.score,
                        "retrieval_source": "bm25",
                    }
                )
            annotated.append(item.model_copy(update={"chunk": chunk.model_copy(update={"metadata": metadata})}))
        return annotated

    def _mark_source(self, results: list[RetrievedChunk], source: str) -> list[RetrievedChunk]:
        return [
            item.model_copy(
                update={
                    "chunk": item.chunk.model_copy(
                        update={"metadata": {**item.chunk.metadata, "retrieval_source": source}}
                    )
                }
            )
            for item in results
        ]

    def _rrf_fuse(
        self,
        dense_results: list[RetrievedChunk],
        bm25_results: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        by_id: dict[str, RetrievedChunk] = {}
        rrf_scores: dict[str, float] = {}

        for source, results in (("dense", dense_results), ("bm25", bm25_results)):
            for rank, item in enumerate(results, start=1):
                chunk_id = item.chunk.chunk_id
                rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + 1.0 / (
                    self.settings.RRF_K + rank
                )
                current = by_id.get(chunk_id)
                by_id[chunk_id] = self._merge_result(current, item, source, rank)

        fused: list[RetrievedChunk] = []
        for chunk_id, item in by_id.items():
            rrf_score = rrf_scores[chunk_id]
            metadata = {
                **item.chunk.metadata,
                "retrieval_source": "hybrid",
                "rrf_score": rrf_score,
            }
            fused.append(
                item.model_copy(
                    update={
                        "score": rrf_score,
                        "chunk": item.chunk.model_copy(update={"metadata": metadata}),
                    }
                )
            )

        fused.sort(key=lambda item: item.score if item.score is not None else 0.0, reverse=True)
        return fused[:top_k]

    def _merge_result(
        self,
        current: RetrievedChunk | None,
        item: RetrievedChunk,
        source: str,
        rank: int,
    ) -> RetrievedChunk:
        base = current or item
        metadata = dict(base.chunk.metadata)
        if source == "dense":
            metadata["dense_rank"] = rank
            metadata["dense_score"] = item.score
            distance = item.distance
        else:
            metadata["bm25_rank"] = rank
            metadata["bm25_score"] = item.score
            for key, value in item.chunk.metadata.items():
                if key.startswith("bm25_"):
                    metadata[key] = value
            distance = base.distance
        return base.model_copy(
            update={
                "distance": distance,
                "chunk": base.chunk.model_copy(update={"metadata": metadata}),
            }
        )
