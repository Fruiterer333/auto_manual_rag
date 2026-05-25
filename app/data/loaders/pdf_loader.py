from pathlib import Path
from time import perf_counter
from uuid import NAMESPACE_URL, uuid5

import fitz

from app.core.logger import get_logger
from app.data.schemas.models import Document


logger = get_logger(__name__)


class PDFLoader:
    """Load a PDF manual into page-level documents."""

    def load(self, file_path: str | Path) -> list[Document]:
        start_time = perf_counter()
        path = Path(file_path)
        logger.info("Start loading PDF: file_path=%s", path)
        if not path.exists():
            logger.error("PDF file not found: %s", path)
            raise FileNotFoundError(f"PDF file not found: {path}")

        documents: list[Document] = []
        empty_pages = 0
        with fitz.open(path) as pdf:
            logger.info("PDF page count: %s", pdf.page_count)
            for page_index, page in enumerate(pdf, start=1):
                text = page.get_text("text")
                if not text.strip():
                    empty_pages += 1
                doc_id = str(uuid5(NAMESPACE_URL, f"{path.name}:{page_index}"))
                documents.append(
                    Document(
                        doc_id=doc_id,
                        source_file=path.name,
                        page=page_index,
                        text=text,
                        metadata={
                            "file_path": str(path),
                            "file_name": path.name,
                            "page": page_index,
                        },
                    )
                )

        elapsed = perf_counter() - start_time
        logger.info(
            "PDF loaded: documents=%s empty_pages=%s elapsed=%.2fs",
            len(documents),
            empty_pages,
            elapsed,
        )
        return documents
