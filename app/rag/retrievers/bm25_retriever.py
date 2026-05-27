import pickle
from pathlib import Path
from statistics import mean
from time import perf_counter
from typing import Any

from app.core.config import Settings
from app.core.logger import get_logger
from app.data.schemas.models import Chunk, RetrievedChunk
from app.rag.retrievers.chunk_filters import filter_index_chunks, filter_retrieval_chunks
from app.rag.retrievers.tokenizer import (
    extract_coverage_terms,
    filter_query_tokens,
    tokenize_for_bm25,
    tokenize_query_for_bm25,
)


logger = get_logger(__name__)


class BM25Retriever:
    """Persistent BM25 retriever over manual chunks."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.index_path = Path(settings.BM25_INDEX_PATH)
        self.bm25: Any | None = None
        self.chunks: list[Chunk] = []
        self.filtered_chunks: list[Chunk] = []
        self.last_debug_info: dict[str, Any] = {}

    def build_index(self, chunks: list[Chunk]) -> None:
        start_time = perf_counter()
        logger.info("BM25 index build started: raw_chunks=%s", len(chunks))
        from rank_bm25 import BM25Okapi

        indexed_chunks, filter_summary = filter_index_chunks(chunks, stage="bm25_build")
        indexed_ids = {chunk.chunk_id for chunk in indexed_chunks}
        self.filtered_chunks = [
            self._with_inspection_metadata(chunk)
            for chunk in chunks
            if chunk.chunk_id not in indexed_ids
        ]
        if not indexed_chunks:
            logger.warning("BM25 index has no chunks after filtering: summary=%s", filter_summary)
            raise ValueError("BM25 index has no chunks after TOC/noise filtering")
        if len(indexed_chunks) < max(10, int(len(chunks) * 0.2)):
            logger.warning(
                "BM25 indexed chunk count is unexpectedly low: raw=%s indexed=%s",
                len(chunks),
                len(indexed_chunks),
            )

        tokenized_corpus = [tokenize_for_bm25(chunk.text) for chunk in indexed_chunks]
        token_lengths = [len(tokens) for tokens in tokenized_corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self.chunks = indexed_chunks
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with self.index_path.open("wb") as file:
            pickle.dump(
                {
                    "bm25": self.bm25,
                    "chunks": [chunk.model_dump() for chunk in indexed_chunks],
                    "filtered_chunks": [chunk.model_dump() for chunk in self.filtered_chunks],
                    "filter_summary": filter_summary,
                },
                file,
            )
        logger.info(
            "BM25 index build finished: raw_chunks=%s indexed_chunks=%s filtered_chunks=%s filter_reasons=%s token_min=%s token_max=%s token_avg=%.1f path=%s elapsed=%.2fs",
            len(chunks),
            len(indexed_chunks),
            len(chunks) - len(indexed_chunks),
            filter_summary.get("filter_reason_counts", {}),
            min(token_lengths) if token_lengths else 0,
            max(token_lengths) if token_lengths else 0,
            mean(token_lengths) if token_lengths else 0.0,
            self.index_path,
            perf_counter() - start_time,
        )

    def load_index(self) -> None:
        if not self.index_path.exists():
            raise FileNotFoundError(
                f"BM25 index not found: {self.index_path}. Run ingest with --rebuild first."
            )
        with self.index_path.open("rb") as file:
            data = pickle.load(file)
        self.bm25 = data["bm25"]
        self.chunks = [Chunk(**chunk_data) for chunk_data in data["chunks"]]
        self.filtered_chunks = [
            Chunk(**chunk_data)
            for chunk_data in data.get("filtered_chunks", [])
        ]
        logger.info("BM25 index loaded: chunks=%s path=%s", len(self.chunks), self.index_path)

    def search(self, query: str, top_k: int = 10) -> list[RetrievedChunk]:
        start_time = perf_counter()
        if self.bm25 is None:
            self.load_index()
        if self.bm25 is None or not self.chunks:
            return []

        raw_query_tokens = tokenize_for_bm25(query)
        query_tokens = tokenize_query_for_bm25(query)
        _, filtered_terms = filter_query_tokens(raw_query_tokens)
        coverage_terms = extract_coverage_terms(query, query_tokens)
        scores = self.bm25.get_scores(query_tokens)
        coverage_infos = [
            self._coverage_info(self.chunks[index], coverage_terms)
            for index in range(len(self.chunks))
        ]
        adjusted_scores = [
            self._apply_coverage_penalty(float(score), coverage_infos[index]["coverage_ratio"])
            for index, score in enumerate(scores)
        ]
        ranked_indices = sorted(
            range(len(adjusted_scores)),
            key=lambda index: adjusted_scores[index],
            reverse=True,
        )[: max(top_k * 3, top_k)]

        results: list[RetrievedChunk] = []
        max_score = max((float(adjusted_scores[index]) for index in ranked_indices), default=0.0)
        for rank, index in enumerate(ranked_indices, start=1):
            raw_score = float(scores[index])
            adjusted_score = float(adjusted_scores[index])
            if adjusted_score <= 0:
                continue
            score = adjusted_score / max_score if max_score > 0 else adjusted_score
            penalty_applied = adjusted_score < raw_score
            coverage_info = coverage_infos[index]
            chunk = self.chunks[index].model_copy(
                update={
                    "metadata": {
                        **self.chunks[index].metadata,
                        "retrieval_source": "bm25",
                        "bm25_rank": rank,
                        "bm25_score": score,
                        "bm25_query_tokens_raw": ",".join(raw_query_tokens),
                        "bm25_query_tokens_filtered": ",".join(query_tokens),
                        "bm25_query_filtered_terms": ",".join(filtered_terms),
                        "bm25_core_terms": ",".join(coverage_terms),
                        "bm25_coverage_terms": ",".join(coverage_terms),
                        "bm25_coverage_matched_terms": ",".join(coverage_info["matched_terms"]),
                        "bm25_coverage_missing_terms": ",".join(coverage_info["missing_terms"]),
                        "bm25_penalty_applied": penalty_applied,
                        "bm25_penalty_reason": self._penalty_reason(
                            penalty_applied,
                            coverage_info["coverage_ratio"],
                        ),
                        "bm25_score_before_penalty": raw_score,
                        "bm25_score_after_penalty": adjusted_score,
                    }
                }
            )
            results.append(
                RetrievedChunk(
                    chunk=chunk,
                    score=score,
                    distance=None,
                )
            )

        results, filter_summary = filter_retrieval_chunks(results, stage="bm25_search_post")
        results = results[:top_k]
        self.last_debug_info = {
            "bm25_query_tokens_raw": raw_query_tokens,
            "bm25_query_tokens_filtered": query_tokens,
            "bm25_query_filtered_terms": filtered_terms,
            "bm25_core_terms": coverage_terms,
            "bm25_coverage_terms": coverage_terms,
            "bm25_filter_summary": filter_summary,
        }

        logger.info(
            "BM25 search completed: raw_query_tokens=%s kept_query_tokens=%s dropped_query_terms=%s coverage_terms=%s returned=%s filter_summary=%s elapsed=%.2fs",
            len(raw_query_tokens),
            len(query_tokens),
            filtered_terms,
            coverage_terms,
            len(results),
            filter_summary,
            perf_counter() - start_time,
        )
        return results

    def _apply_coverage_penalty(
        self,
        score: float,
        coverage_ratio: float,
    ) -> float:
        if score <= 0:
            return score
        if coverage_ratio == 0:
            return score * self.settings.BM25_CORE_TERM_PENALTY_FACTOR
        if coverage_ratio < 0.4:
            return score * 0.7
        return score

    def _coverage_info(self, chunk: Chunk, coverage_terms: list[str]) -> dict[str, Any]:
        if not coverage_terms:
            return {"matched_terms": [], "missing_terms": [], "coverage_ratio": 1.0}
        text = chunk.text
        matched_terms = [term for term in coverage_terms if term in text]
        missing_terms = [term for term in coverage_terms if term not in text]
        return {
            "matched_terms": matched_terms,
            "missing_terms": missing_terms,
            "coverage_ratio": len(matched_terms) / len(coverage_terms),
        }

    def _penalty_reason(self, penalty_applied: bool, coverage_ratio: float) -> str:
        if not penalty_applied:
            return ""
        if coverage_ratio == 0:
            return "missing_query_coverage"
        return "low_query_coverage"

    def _with_inspection_metadata(self, chunk: Chunk) -> Chunk:
        from app.rag.retrievers.chunk_filters import inspect_chunk_filter

        filter_info = inspect_chunk_filter(chunk, stage="bm25_build")
        return chunk.model_copy(
            update={
                "metadata": {
                    **chunk.metadata,
                    "is_toc": filter_info["is_toc"],
                    "is_noise": filter_info["is_noise"],
                    "filter_reason": filter_info["filter_reason"],
                    "index_status": "filtered",
                }
            }
        )
