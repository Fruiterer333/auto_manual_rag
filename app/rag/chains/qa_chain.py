from app.core.config import Settings, get_settings
from app.core.logger import get_logger
from app.data.schemas.models import Citation, QueryRequest, QueryResponse
from app.rag.embeddings.local_embedding import LocalEmbeddingClient
from app.rag.llms.ollama_client import OllamaClient
from app.rag.prompts.answer_prompt import build_answer_prompt
from app.rag.retrievers.chroma_retriever import ChromaRetriever


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
        logger.info("Query received: %s", question)
        query_embedding = self.embedding_client.embed_query(question)
        chunks = self.retriever.search(query_embedding=query_embedding, top_k=top_k)
        logger.info("Retrieved chunks: %s", len(chunks))

        if not chunks:
            return QueryResponse(
                question=question,
                answer="我没有在手册中找到可靠依据",
                citations=[],
            )

        prompt = build_answer_prompt(question=question, chunks=chunks)
        answer = self.llm_client.generate(prompt)
        citations = [
            Citation(
                source_file=chunk.source_file,
                page=chunk.page,
                chunk_id=chunk.chunk_id,
                quote=chunk.text[:120],
            )
            for chunk in chunks
        ]
        return QueryResponse(question=question, answer=answer, citations=citations)

    def run(self, request: QueryRequest) -> QueryResponse:
        return self.answer(question=request.question, top_k=request.top_k)
