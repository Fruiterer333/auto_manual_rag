from app.data.schemas.models import Chunk, Document


class ManualSplitter:
    """Placeholder splitter for automotive manual chunks."""

    def split(self, document: Document) -> list[Chunk]:
        raise NotImplementedError("Manual splitting will be implemented in V1/V2.")
