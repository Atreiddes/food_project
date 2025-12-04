from sqlalchemy import Column, String, DECIMAL, DateTime
from sqlalchemy.sql import func
import uuid
from app.db.base import Base


def generate_uuid():
    return str(uuid.uuid4())


class UserBalance(Base):
    """
    Модель баланса пользователя.

    Ответственность: Хранение информации о балансе (SRP - отдельно от User).
    """
    __tablename__ = "user_balances"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    user_id = Column(String, unique=True, nullable=False, index=True)
    balance = Column(DECIMAL(10, 2), default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
