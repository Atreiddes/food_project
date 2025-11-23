"""
vLLM / OpenAI совместимый эндпоинт
"""
from fastapi import APIRouter
from app.schemas.all_schemas import ChatCompletionRequest, ChatCompletionResponse
from app.services.llm_service import llm_service

router = APIRouter()

@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-совместимый эндпоинт для chat completion.
    Позволяет использовать сервис как drop-in замену для vLLM или OpenAI.
    """
    return await llm_service.chat_completion(request)
