from time import perf_counter

from app.core.config import Settings, get_settings
from app.core.logger import get_logger
from app.data.schemas.models import Citation, QueryRequest, QueryResponse
from app.rag.embeddings.local_embedding import LocalEmbeddingClient
from app.rag.llms.ollama_client import OllamaClient
from app.rag.prompts.answer_prompt import build_answer_prompt
from app.rag.retrievers.context_selector import (
    deduplicate_contexts,
    enforce_max_context_chars,
    expand_neighbor_contexts,
    select_contexts,
)
from app.rag.retrievers.chroma_retriever import ChromaRetriever
from app.rag.utils.citation_utils import build_relevant_quote


logger = get_logger(__name__)


class QAChain:
    """Minimal V1 RAG QA chain."""

    def __init__(
        self,
        settings: Settings | None = None,
        embedding_client: LocalEmbeddingClient | None = None,
        retriever: ChromaRetriever | None = None,
        llm_client: OllamaClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.embedding_client = embedding_client or LocalEmbeddingClient(self.settings)
        self.retriever = retriever or ChromaRetriever(self.settings)
        self.llm_client = llm_client or OllamaClient(self.settings)

    def answer(self, question: str, top_k: int = 5) -> QueryResponse:
        start_time = perf_counter()
        logger.info("QA started: question=%s top_k=%s", question, top_k)
        query_embedding = self.embedding_client.embed_query(question)
        selection_enabled = self.settings.ENABLE_METADATA_CONTEXT_SELECTION
        candidate_k = top_k
        if selection_enabled:
            candidate_k = max(top_k, self.settings.CONTEXT_SELECTION_CANDIDATE_K)
        retrieved_candidates = self.retriever.search(
            query_embedding=query_embedding,
            top_k=candidate_k,
        )
        retrieved_chunks = select_contexts(
            question=question,
            retrieved=retrieved_candidates,
            top_k=top_k,
            enabled=selection_enabled,
        )
        selected_count = len(retrieved_chunks)
        retrieved_chunks, removed_duplicates = deduplicate_contexts(retrieved_chunks)
        expansion_enabled = self.settings.ENABLE_NEIGHBOR_CONTEXT_EXPANSION
        expanded_count = 0
        removed_after_expansion = 0
        if expansion_enabled:
            expanded_contexts = expand_neighbor_contexts(
                retrieved_chunks,
                neighbor_lookup=self.retriever.find_neighbor_chunks,
                enabled=True,
                max_per_chunk=self.settings.NEIGHBOR_EXPANSION_MAX_PER_CHUNK,
            )
            expanded_count = len(expanded_contexts) - len(retrieved_chunks)
            retrieved_chunks, removed_after_expansion = deduplicate_contexts(expanded_contexts)
        retrieved_chunks = enforce_max_context_chars(
            retrieved_chunks,
            max_chars=self.settings.MAX_CONTEXT_CHARS,
        )
        logger.info(
            "Retrieved chunks: candidate_count=%s selected=%s after_dedup=%s dedup_removed_count=%s expansion_enabled=%s expanded=%s duplicate_removed_after_expansion=%s final_context_count=%s selection_enabled=%s candidate_k=%s",
            len(retrieved_candidates),
            selected_count,
            selected_count - removed_duplicates,
            removed_duplicates,
            expansion_enabled,
            expanded_count,
            removed_after_expansion,
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
            )
            for retrieved in retrieved_chunks
        ]
        logger.info(
            "QA completed: citations=%s answer_chars=%s elapsed=%.2fs",
            len(citations),
            len(answer),
            perf_counter() - start_time,
        )
        return QueryResponse(question=question, answer=answer, citations=citations)

    def run(self, request: QueryRequest) -> QueryResponse:
        return self.answer(question=request.question, top_k=request.top_k)

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
