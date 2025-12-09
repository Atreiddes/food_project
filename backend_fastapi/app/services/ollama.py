import logging
from dataclasses import dataclass
from typing import Optional
from abc import ABC, abstractmethod

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


@dataclass
class OllamaResponse:
    success: bool
    content: Optional[str] = None
    model: Optional[str] = None
    error: Optional[str] = None


class BaseMLService(ABC):
    @abstractmethod
    async def chat(
        self,
        message: str,
        conversation_history: Optional[list] = None
    ) -> OllamaResponse:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass


class OllamaService(BaseMLService):
    DEFAULT_TIMEOUT = 120.0

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT
    ):
        self._base_url = base_url or settings.OLLAMA_URL
        self._model = model or settings.OLLAMA_MODEL
        self._timeout = timeout

    @property
    def model(self) -> str:
        return self._model

    @property
    def base_url(self) -> str:
        return self._base_url

    def _build_messages(
        self,
        message: str,
        conversation_history: Optional[list]
    ) -> list:
        messages = []

        if conversation_history:
            for msg in conversation_history:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

        messages.append({
            "role": "user",
            "content": message
        })

        return messages

    async def chat(
        self,
        message: str,
        conversation_history: Optional[list] = None
    ) -> OllamaResponse:
        messages = self._build_messages(message, conversation_history)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/api/chat",
                    json={
                        "model": self._model,
                        "messages": messages,
                        "stream": False
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data.get("message", {}).get("content", "")
                    return OllamaResponse(
                        success=True,
                        content=content,
                        model=self._model
                    )

                logger.error(
                    f"Ollama returned status {response.status_code}: {response.text}"
                )
                return OllamaResponse(
                    success=False,
                    error=f"Service returned status {response.status_code}"
                )

        except httpx.TimeoutException:
            logger.error("Ollama request timed out")
            return OllamaResponse(
                success=False,
                error="Request timed out"
            )

        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama service")
            return OllamaResponse(
                success=False,
                error="Service unavailable"
            )

        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            return OllamaResponse(
                success=False,
                error=str(e)
            )

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False


class OllamaServiceFactory:
    _instance: Optional[OllamaService] = None

    @classmethod
    def get_service(cls) -> OllamaService:
        if cls._instance is None:
            cls._instance = OllamaService()
        return cls._instance

    @classmethod
    def create_service(
        cls,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ) -> OllamaService:
        return OllamaService(base_url=base_url, model=model)
