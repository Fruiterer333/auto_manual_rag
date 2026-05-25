from statistics import mean
from uuid import NAMESPACE_URL, uuid5

from app.core.logger import get_logger
from app.data.schemas.models import Chunk, Document


logger = get_logger(__name__)


class ManualTextSplitter:
    """Fixed-size splitter for V1 manual chunks."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 120) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_documents(self, documents: list[Document]) -> list[Chunk]:
        logger.info(
            "Start splitting documents: documents=%s chunk_size=%s chunk_overlap=%s",
            len(documents),
            self.chunk_size,
            self.chunk_overlap,
        )
        chunks: list[Chunk] = []

        for document in documents:
            pieces = self._split_text(document.text)
            for chunk_index, text in enumerate(pieces):
                chunk_id = str(uuid5(NAMESPACE_URL, f"{document.doc_id}:{chunk_index}"))
                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        doc_id=document.doc_id,
                        source_file=document.source_file,
                        page=document.page,
                        text=text,
                        metadata={
                            "chunk_index": chunk_index,
                            "page": document.page,
                            "source_file": document.source_file,
                        },
                    )
                )

        if not chunks:
            logger.warning("No chunks generated from documents=%s", len(documents))
            return chunks

        lengths = [len(chunk.text) for chunk in chunks]
        logger.info(
            "Documents split: chunks=%s length_min=%s length_max=%s length_avg=%.1f",
            len(chunks),
            min(lengths),
            max(lengths),
            mean(lengths),
        )
        return chunks

    def _split_text(self, text: str) -> list[str]:
        if not text:
            return []

        chunks: list[str] = []
        start = 0
        text_length = len(text)

        while start < text_length:
            target_end = min(start + self.chunk_size, text_length)
            end = self._find_boundary(text, start, target_end)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            if end >= text_length:
                break

            start = max(end - self.chunk_overlap, 0)
            if start >= end:
                start = end

        return chunks

    def _find_boundary(self, text: str, start: int, target_end: int) -> int:
        if target_end >= len(text):
            return len(text)

        boundary_chars = ("。", "；", "\n")
        search_start = max(start + int(self.chunk_size * 0.6), start)
        for index in range(target_end, search_start, -1):
            if text[index - 1] in boundary_chars:
                return index

        return target_end


class ManualSplitter(ManualTextSplitter):
    """Backward-compatible alias for the V0 placeholder name."""

    def split(self, document: Document) -> list[Chunk]:
        return self.split_documents([document])
