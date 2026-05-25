from fastapi import APIRouter

from app.data.schemas.models import QueryRequest, QueryResponse
from app.rag.chains.qa_chain import QAChain

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
def query_manual(request: QueryRequest) -> QueryResponse:
    chain = QAChain()
    return chain.answer(question=request.question, top_k=request.top_k)
