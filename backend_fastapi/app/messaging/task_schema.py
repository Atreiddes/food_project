from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import IntEnum
import uuid


class TaskPriority(IntEnum):
    LOW = 1
    NORMAL = 5
    HIGH = 10


class MLTaskMessage(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prediction_id: str
    user_id: str
    message: str
    conversation_history: Optional[list] = Field(default_factory=list)
    model_id: str
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = Field(default_factory=datetime.utcnow)
    retry_count: int = 0
    max_retries: int = 3

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Message cannot be empty")
        return value.strip()

    @field_validator("conversation_history")
    @classmethod
    def validate_history(cls, value: Optional[list]) -> list:
        if value is None:
            return []
        return value

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, data: str) -> "MLTaskMessage":
        return cls.model_validate_json(data)

    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries

    def increment_retry(self) -> "MLTaskMessage":
        return self.model_copy(update={"retry_count": self.retry_count + 1})


class TaskResult(BaseModel):
    task_id: str
    prediction_id: str
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    processing_time_ms: int = 0
    completed_at: datetime = Field(default_factory=datetime.utcnow)
