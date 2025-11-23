"""
Сервис для работы с LLM через Ollama
"""
import httpx
import time
from app.core.config import settings
from app.schemas.all_schemas import ChatCompletionRequest, ChatCompletionResponse, ChatMessage, ChatCompletionResponseChoice

class LLMService:
    """Сервис для работы с языковой моделью"""
    
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.model = "mistral"
    
    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """
        vLLM / OpenAI совместимый chat completion
        Конвертирует OpenAI формат в Ollama формат
        """
        async with httpx.AsyncClient() as client:
            try:
                # Ollama использует /api/generate, не /api/chat
                ollama_url = f"{self.ollama_url}/api/generate"
                
                # Конвертируем messages в один prompt
                prompt_parts = []
                for msg in request.messages:
                    role = msg.role
                    content = msg.content
                    if role == "system":
                        prompt_parts.append(f"System: {content}")
                    elif role == "user":
                        prompt_parts.append(f"User: {content}")
                    elif role == "assistant":
                        prompt_parts.append(f"Assistant: {content}")
                
                prompt_parts.append("Assistant:")
                full_prompt = "\n".join(prompt_parts)
                
                payload = {
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                }
                
                if request.temperature is not None:
                    payload["options"] = {"temperature": request.temperature}

                response = await client.post(ollama_url, json=payload, timeout=120.0)
                response.raise_for_status()
                result = response.json()
                
                # Маппинг Ollama ответа в OpenAI формат
                content = result.get("response", "")
                
                return ChatCompletionResponse(
                    id=f"chatcmpl-{int(time.time())}",
                    created=int(time.time()),
                    model=request.model,
                    choices=[
                        ChatCompletionResponseChoice(
                            index=0,
                            message=ChatMessage(role="assistant", content=content),
                            finish_reason="stop"
                        )
                    ],
                    usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                )

            except httpx.HTTPError as e:
                error_msg = f"HTTP ошибка при вызове Ollama: {type(e).__name__} - {str(e)}"
                print(error_msg)
                raise Exception(error_msg)
            except Exception as e:
                error_msg = f"Неожиданная ошибка при вызове Ollama: {type(e).__name__} - {str(e)}"
                print(error_msg)
                import traceback
                traceback.print_exc()
                raise Exception(error_msg)

# Singleton instance
llm_service = LLMService()
