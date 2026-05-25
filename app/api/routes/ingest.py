from fastapi import APIRouter

router = APIRouter(tags=["ingest"])


@router.post("/ingest")
def ingest_manual() -> dict[str, str]:
    return {"message": "Ingest endpoint is not implemented yet"}
