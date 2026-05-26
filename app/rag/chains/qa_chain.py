from time import perf_counter

from app.core.config import Settings, get_settings
from app.core.logger import get_logger
from app.data.schemas.models import Citation, QueryRequest, QueryResponse
from app.rag.embeddings.local_embedding import LocalEmbeddingClient
from app.rag.llms.ollama_client import OllamaClient
from app.rag.prompts.answer_prompt import build_answer_prompt
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
        retrieved_chunks = self.retriever.search(query_embedding=query_embedding, top_k=top_k)
        logger.info("Retrieved chunks: %s", len(retrieved_chunks))

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
        answer = self.llm_client.generate(prompt)
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
