from pydantic import BaseModel, field_validator
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any


class PredictionCreate(BaseModel):
    message: str
    conversation_history: Optional[list] = []

    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Message cannot be empty')
        if len(v) > 2000:
            raise ValueError('Message is too long (max 2000 characters)')
        return v.strip()

    @field_validator('conversation_history')
    @classmethod
    def validate_history(cls, v: Optional[list]) -> list:
        if v is None:
            return []
        if len(v) > 50:
            raise ValueError('Conversation history is too long (max 50 messages)')
        return v


class PredictionResponse(BaseModel):
    id: str
    user_id: str
    model_id: str
    status: str
    cost_charged: Decimal
    result: Optional[dict] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
        protected_namespaces = ()
