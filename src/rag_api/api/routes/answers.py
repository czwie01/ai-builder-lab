from typing import Annotated

from fastapi import APIRouter, Depends

from rag_api.api.dependencies import get_answer_question
from rag_api.api.schemas import AnswerRequest, AnswerResponse
from rag_api.application.answer_question import AnswerQuestion

router = APIRouter(prefix="/api/v1", tags=["answers"])


@router.post("/answers", response_model=AnswerResponse)
async def create_answer(
    request: AnswerRequest,
    answer_question: Annotated[AnswerQuestion, Depends(get_answer_question)],
) -> AnswerResponse:
    answer = await answer_question.execute(request.question, request.top_k)
    return AnswerResponse.from_domain(answer)
