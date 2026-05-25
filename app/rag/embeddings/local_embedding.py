from app.core.config import Settings, get_settings
from app.rag.embeddings.base import BaseEmbeddingClient


class LocalEmbeddingClient(BaseEmbeddingClient):
    """SentenceTransformers embedding client loaded on instance creation."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(self.settings.EMBEDDING_MODEL_NAME)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]
