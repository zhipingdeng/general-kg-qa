from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from app.api.v1.auth import get_current_user
from app.models.user import User

router = APIRouter()


class QARequest(BaseModel):
    question: str


class QAResponse(BaseModel):
    question: str
    entities: list[str]
    answer: str


@router.post("/qa", response_model=QAResponse)
async def ask_question(req: QARequest, request: Request, current_user: User = Depends(get_current_user)):
    pipeline = request.app.state.qa_pipeline
    if pipeline is None:
        return QAResponse(question=req.question, entities=[], answer="QA pipeline 未初始化，请等待服务启动完成。")
    result = await pipeline.answer(req.question)
    return QAResponse(question=result.question, entities=result.entities, answer=result.answer)
