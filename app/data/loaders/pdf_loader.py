from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import fitz

from app.data.schemas.models import Document


class PDFLoader:
    """Load a PDF manual into page-level documents."""

    def load(self, file_path: str | Path) -> list[Document]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")

        documents: list[Document] = []
        with fitz.open(path) as pdf:
            for page_index, page in enumerate(pdf, start=1):
                text = page.get_text("text")
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

        return documents
