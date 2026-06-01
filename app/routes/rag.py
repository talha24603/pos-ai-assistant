from fastapi import APIRouter

from pydantic import BaseModel

from app.services.rag_service import answer_question

router = APIRouter()


class RagRequest(BaseModel):
    question: str
    tenant_id: str


@router.post("/rag")
def rag_query(payload: RagRequest):

    result = answer_question(
        payload.question,
        payload.tenant_id
    )

    return result