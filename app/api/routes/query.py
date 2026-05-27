from fastapi import APIRouter, HTTPException

from app.data.schemas.models import QueryRequest, QueryResponse
from app.rag.chains.qa_chain import QAChain

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
def query_manual(request: QueryRequest) -> QueryResponse:
    chain = QAChain()
    try:
        return chain.answer(
            question=request.question,
            top_k=request.top_k,
            retrieval_mode=request.retrieval_mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
