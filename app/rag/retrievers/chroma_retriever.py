from app.core.config import Settings
from app.data.schemas.models import Chunk


class ChromaRetriever:
    """Chroma retriever placeholder. Real Chroma connection will be added later."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def retrieve(self, query: str, top_k: int = 5) -> list[Chunk]:
        raise NotImplementedError("Chroma retrieval will be implemented in V1.")
