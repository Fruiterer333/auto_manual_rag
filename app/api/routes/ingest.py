from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.ingest_service import ingest_manual

router = APIRouter(tags=["ingest"])


class IngestRequest(BaseModel):
    file_path: str = "data/raw/demo_manual.pdf"
    rebuild: bool = True
    chunk_size: int = Field(default=800, gt=0)
    chunk_overlap: int = Field(default=120, ge=0)


@router.post("/ingest")
def ingest(request: IngestRequest) -> dict[str, bool | int | str]:
    result = ingest_manual(
        file_path=request.file_path,
        rebuild=request.rebuild,
        chunk_size=request.chunk_size,
        chunk_overlap=request.chunk_overlap,
    )
    return {
        "success": result.success,
        "pages": result.pages,
        "chunks": result.chunks,
        "message": result.message,
    }
