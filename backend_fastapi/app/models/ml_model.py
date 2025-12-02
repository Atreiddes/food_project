from sqlalchemy import Column, String, Text, DECIMAL, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class MLModel(Base):
    """
    Модель ML сервиса.

    Ответственность: Хранение информации о доступных ML моделях.
    """
    __tablename__ = "ml_models"

    id = Column(String(255), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False, default="1.0")
    status = Column(String(50), nullable=False, default="active")
    cost_per_request = Column(DECIMAL(10, 2), nullable=False)
    endpoint = Column(String(500), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    @property
    def is_active(self) -> bool:
        """Check if model is active."""
        return self.status == "active"
