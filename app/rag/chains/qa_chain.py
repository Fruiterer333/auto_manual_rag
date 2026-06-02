from time import perf_counter

from app.core.config import Settings, get_settings
from app.core.logger import get_logger
from app.data.schemas.models import Citation, QueryRequest, QueryResponse
from app.rag.embeddings.local_embedding import LocalEmbeddingClient
from app.rag.llms.ollama_client import OllamaClient
from app.rag.prompts.answer_prompt import build_answer_prompt
from app.rag.rerankers import get_reranker
from app.rag.rerankers.base import BaseReranker
from app.rag.retrievers.context_selector import (
    enforce_max_context_chars,
    expand_neighbor_contexts,
    select_contexts,
)
from app.rag.retrievers.chunk_filters import (
    deduplicate_chunks_by_content,
    filter_retrieval_chunks,
)
from app.rag.retrievers.hybrid_retriever import HybridRetriever
from app.rag.utils.citation_utils import build_relevant_quote


logger = get_logger(__name__)


class QAChain:
    """Minimal V1 RAG QA chain."""

    def __init__(
        self,
        settings: Settings | None = None,
        embedding_client: LocalEmbeddingClient | None = None,
        retriever: HybridRetriever | None = None,
        llm_client: OllamaClient | None = None,
        reranker: BaseReranker | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.embedding_client = embedding_client or LocalEmbeddingClient(self.settings)
        self.retriever = retriever or HybridRetriever(self.settings)
        self.llm_client = llm_client or OllamaClient(self.settings)
        self.reranker = reranker or get_reranker(self.settings)

    def answer(
        self,
        question: str,
        top_k: int = 5,
        retrieval_mode: str | None = None,
    ) -> QueryResponse:
        start_time = perf_counter()
        mode = self._resolve_retrieval_mode(retrieval_mode)
        logger.info("QA started: question=%s top_k=%s retrieval_mode=%s", question, top_k, mode)
        query_embedding = self.embedding_client.embed_query(question)
        selection_enabled = self.settings.ENABLE_METADATA_CONTEXT_SELECTION
        candidate_k = top_k
        if selection_enabled:
            candidate_k = max(top_k, self.settings.CONTEXT_SELECTION_CANDIDATE_K)
        if self.settings.ENABLE_RERANK:
            candidate_k = max(candidate_k, self.settings.RERANK_TOP_N)
        retrieved_candidates = self.retriever.search(
            question=question,
            query_embedding=query_embedding,
            top_k=candidate_k,
            candidate_k=candidate_k,
            retrieval_mode=mode,
        )
        filtered_candidates, candidate_filter_summary = filter_retrieval_chunks(
            retrieved_candidates,
            stage="context_selection_pre",
        )
        filtered_candidates, candidate_dedup_summary = deduplicate_chunks_by_content(
            filtered_candidates,
            stage="context_selection_pre",
        )
        if self.settings.ENABLE_RERANK:
            rerank_pool_size = max(top_k, self.settings.RERANK_TOP_N)
            rerank_output_size = max(top_k, self.settings.RERANK_OUTPUT_TOP_K)
            reranked_candidates = self.reranker.rerank(
                query=question,
                chunks=filtered_candidates[:rerank_pool_size],
                top_k=rerank_output_size,
            )
        else:
            reranked_candidates = self.reranker.rerank(
                query=question,
                chunks=filtered_candidates,
                top_k=None,
            )
        retrieved_chunks = select_contexts(
            question=question,
            retrieved=reranked_candidates,
            top_k=top_k,
            enabled=selection_enabled,
        )
        selected_count = len(retrieved_chunks)
        retrieved_chunks, selection_dedup_summary = deduplicate_chunks_by_content(
            retrieved_chunks,
            stage="context_selection_post",
        )
        expansion_enabled = self.settings.ENABLE_NEIGHBOR_CONTEXT_EXPANSION
        expanded_count = 0
        expansion_dedup_summary = {}
        if expansion_enabled:
            expanded_contexts = expand_neighbor_contexts(
                retrieved_chunks,
                neighbor_lookup=self.retriever.find_neighbor_chunks,
                enabled=True,
                max_per_chunk=self.settings.NEIGHBOR_EXPANSION_MAX_PER_CHUNK,
            )
            expanded_count = len(expanded_contexts) - len(retrieved_chunks)
            retrieved_chunks, expansion_dedup_summary = deduplicate_chunks_by_content(
                expanded_contexts,
                stage="neighbor_expansion_post",
            )
        retrieved_chunks, final_filter_summary = filter_retrieval_chunks(
            retrieved_chunks,
            stage="final_context_pre_prompt",
        )
        retrieved_chunks, final_dedup_summary = deduplicate_chunks_by_content(
            retrieved_chunks,
            stage="final_context_pre_prompt",
        )
        retrieved_chunks = enforce_max_context_chars(
            retrieved_chunks,
            max_chars=self.settings.MAX_CONTEXT_CHARS,
        )
        logger.info(
            "Retrieved chunks: candidate_count=%s candidate_after_filter=%s candidate_filter=%s candidate_dedup=%s rerank_enabled=%s rerank_strategy=%s reranked=%s selected=%s selection_dedup=%s expansion_enabled=%s expanded=%s expansion_dedup=%s final_filter=%s final_dedup=%s final_context_count=%s selection_enabled=%s candidate_k=%s",
            len(retrieved_candidates),
            len(filtered_candidates),
            candidate_filter_summary,
            candidate_dedup_summary,
            self.settings.ENABLE_RERANK,
            self.reranker.__class__.__name__,
            len(reranked_candidates),
            selected_count,
            selection_dedup_summary,
            expansion_enabled,
            expanded_count,
            expansion_dedup_summary,
            final_filter_summary,
            final_dedup_summary,
            len(retrieved_chunks),
            selection_enabled,
            candidate_k,
        )

        if not retrieved_chunks:
            answer = "我没有在手册中找到可靠依据"
            logger.warning("No retrieved chunks for question=%s", question)
            logger.info(
                "QA completed: citations=0 answer_chars=%s elapsed=%.2fs",
                len(answer),
                perf_counter() - start_time,
            )
            return QueryResponse(
                question=question,
                answer=answer,
                citations=[],
                retrieval_mode=mode,
            )

        chunks = [retrieved.chunk for retrieved in retrieved_chunks]
        prompt = build_answer_prompt(question=question, chunks=chunks)
        raw_answer = self.llm_client.generate(prompt)
        answer = self._post_process_answer(raw_answer)
        citations = [
            Citation(
                source_file=retrieved.chunk.source_file,
                page=retrieved.chunk.page,
                chunk_id=retrieved.chunk.chunk_id,
                quote=build_relevant_quote(question, retrieved.chunk.text),
                score=retrieved.score,
                distance=retrieved.distance,
                chapter=retrieved.chunk.chapter,
                section=retrieved.chunk.section,
                content_type=retrieved.chunk.content_type,
                risk_level=retrieved.chunk.risk_level,
                selection_score=retrieved.selection_score,
                is_expanded_neighbor=retrieved.is_expanded_neighbor,
                retrieval_source=self._metadata_str(retrieved, "retrieval_source"),
                dense_rank=self._metadata_int(retrieved, "dense_rank"),
                bm25_rank=self._metadata_int(retrieved, "bm25_rank"),
                dense_score=self._metadata_float(retrieved, "dense_score"),
                bm25_score=self._metadata_float(retrieved, "bm25_score"),
                rrf_score=self._metadata_float(retrieved, "rrf_score"),
            )
            for retrieved in retrieved_chunks
        ]
        logger.info(
            "QA completed: citations=%s answer_chars=%s elapsed=%.2fs",
            len(citations),
            len(answer),
            perf_counter() - start_time,
        )
        return QueryResponse(
            question=question,
            answer=answer,
            citations=citations,
            retrieval_mode=mode,
        )

    def run(self, request: QueryRequest) -> QueryResponse:
        return self.answer(
            question=request.question,
            top_k=request.top_k,
            retrieval_mode=request.retrieval_mode,
        )

    def _resolve_retrieval_mode(self, retrieval_mode: str | None) -> str:
        mode = retrieval_mode or self.settings.RETRIEVAL_MODE
        if mode not in HybridRetriever.VALID_MODES:
            raise ValueError(f"Invalid retrieval_mode: {mode}")
        return mode

    def _post_process_answer(self, answer: str) -> str:
        import re

        cleaned = re.sub(
            r"(参见|参考|根据)?\s*(手册片段|资料|片段|上下文|context|source id)\s*\d+\s*(中|里|内)?",
            "",
            answer,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"(参见|参考|根据)\s*[,，:：]?", "", cleaned)
        cleaned = cleaned.lstrip("，,:：。；; ")
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
        removed = cleaned != answer
        logger.info("Answer postprocess completed: removed_internal_refs=%s", removed)
        return cleaned

    def _metadata_str(self, retrieved, key: str) -> str | None:
        value = retrieved.chunk.metadata.get(key)
        return str(value) if value is not None and value != "" else None

    def _metadata_int(self, retrieved, key: str) -> int | None:
        value = retrieved.chunk.metadata.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return None

    def _metadata_float(self, retrieved, key: str) -> float | None:
        value = retrieved.chunk.metadata.get(key)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None
        return None
