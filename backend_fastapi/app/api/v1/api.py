"""API v1 router"""
from fastapi import APIRouter
from app.api.v1.endpoints import vllm

api_router = APIRouter()

# vLLM эндпоинт - /api/v1/v1/chat/completions (двойной v1 для совместимости с OpenAI)
api_router.include_router(vllm.router, prefix="/v1", tags=["vllm"])
