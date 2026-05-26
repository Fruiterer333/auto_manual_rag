from collections import Counter
from statistics import mean
from uuid import NAMESPACE_URL, uuid5

from app.core.logger import get_logger
from app.data.parsers.manual_structure_parser import (
    detect_content_type,
    detect_risk_level,
    is_procedure_text,
)
from app.data.schemas.models import Chunk, ManualBlock


logger = get_logger(__name__)


class ManualStructureSplitter:
    """Split parsed manual blocks while preserving safety/procedure structure."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 120) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_blocks(self, blocks: list[ManualBlock]) -> list[Chunk]:
        logger.info(
            "Manual splitter started: blocks=%s chunk_size=%s chunk_overlap=%s",
            len(blocks),
            self.chunk_size,
            self.chunk_overlap,
        )
        chunks: list[Chunk] = []
        for block in blocks:
            pieces = self._split_block_text(block)
            for piece_index, text in enumerate(pieces):
                content_type = block.content_type or detect_content_type(text)
                risk_level = block.risk_level or detect_risk_level(text, content_type)
                chunk_id = str(uuid5(NAMESPACE_URL, f"{block.block_id}:{piece_index}"))
                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        doc_id=block.block_id,
                        source_file=block.source_file,
                        page=block.start_page,
                        text=text,
                        chapter=block.chapter,
                        section=block.section,
                        content_type=content_type,
                        risk_level=risk_level,
                        metadata={
                            "start_page": block.start_page,
                            "end_page": block.end_page,
                            "heading_path": block.heading_path,
                            "chunk_index": len(chunks),
                            "split_strategy": "manual_structure",
                            "has_warning": "警告" in text,
                            "has_caution": "注意" in text,
                            "has_note": "说明" in text,
                            "is_procedure": is_procedure_text(text),
                            "source_pages": self._source_pages(block),
                        },
                    )
                )

        if not chunks:
            logger.warning("Manual splitter produced no chunks")
            return chunks

        lengths = [len(chunk.text) for chunk in chunks]
        content_counter = Counter(chunk.content_type or "normal" for chunk in chunks)
        risk_counter = Counter(chunk.risk_level or "low" for chunk in chunks)
        logger.info(
            "Manual splitter finished: chunks=%s length_min=%s length_max=%s length_avg=%.1f content_type=%s risk_level=%s",
            len(chunks),
            min(lengths),
            max(lengths),
            mean(lengths),
            dict(content_counter),
            dict(risk_counter),
        )
        return chunks

    def _split_block_text(self, block: ManualBlock) -> list[str]:
        text = block.text.strip()
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        if block.content_type in {"warning", "caution", "note", "procedure"} and len(text) <= int(
            self.chunk_size * 1.25
        ):
            return [text]

        return self._split_long_text(text)

    def _split_long_text(self, text: str) -> list[str]:
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
        boundary_chars = ("警告", "注意", "说明", "\n■", "\n-", "\n•", "。", "；", "\n")
        search_start = max(start + int(self.chunk_size * 0.55), start)
        best_index = -1
        for boundary in boundary_chars:
            index = text.rfind(boundary, search_start, target_end)
            if index > best_index:
                best_index = index + len(boundary)
        return best_index if best_index > search_start else target_end

    def _source_pages(self, block: ManualBlock) -> list[int]:
        pages = block.metadata.get("source_pages")
        if isinstance(pages, list):
            return [int(page) for page in pages if isinstance(page, int)]
        return [page for page in (block.start_page, block.end_page) if page is not None]
