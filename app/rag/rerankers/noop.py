from app.data.schemas.models import RetrievedChunk
from app.rag.rerankers.base import BaseReranker


class NoopReranker(BaseReranker):
    """Compatibility reranker that preserves the retrieval order."""

    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        del query
        copied_chunks = list(chunks)
        return copied_chunks if top_k is None else copied_chunks[:top_k]

