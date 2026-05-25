from fastapi import APIRouter

from app.data.schemas.models import QueryRequest

router = APIRouter(tags=["query"])


@router.post("/query")
def query_manual(request: QueryRequest) -> dict[str, str]:
    return {
        "question": request.question,
        "answer": "Query endpoint is not implemented yet",
    }
