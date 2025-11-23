"""
Pydantic схемы для API
"""
from pydantic import BaseModel
from typing import List, Optional

# --- vLLM / OpenAI Compatible Schemas ---

class ChatMessage(BaseModel):
    """Сообщение чата"""
    role: str  # "system", "user", "assistant"
    content: str

class ChatCompletionRequest(BaseModel):
    """Запрос на chat completion"""
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None

class ChatCompletionResponseChoice(BaseModel):
    """Вариант ответа"""
    index: int
    message: ChatMessage
    finish_reason: str

class ChatCompletionResponse(BaseModel):
    """Ответ chat completion"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: dict

# --- User Schemas ---

class UserCreate(BaseModel):
    """Создание пользователя"""
    email: str
    password: str

class UserResponse(BaseModel):
    """Ответ с данными пользователя"""
    id: int
    email: str
    balance: float
    
    class Config:
        from_attributes = True

# --- Prediction Schemas ---

class PredictionCreate(BaseModel):
    """Создание предсказания"""
    user_id: int
    model_id: int
    input_data: str

class PredictionResponse(BaseModel):
    """Ответ с предсказанием"""
    id: int
    user_id: int
    model_id: int
    input_data: str
    output_result: Optional[str]
    status: str
    
    class Config:
        from_attributes = True
