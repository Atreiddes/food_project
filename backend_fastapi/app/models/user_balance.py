from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.user import Base


class UserBalance(Base):
    """
    Модель баланса пользователя.

    Отдельная сущность для управления финансами пользователя.
    Следует принципу Single Responsibility Principle (SRP).

    User отвечает за: аутентификацию, профиль
    UserBalance отвечает за: финансы, баланс
    """

    __tablename__ = "user_balances"

    # Primary key
    user_id = Column(
        String(255),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    # Связь с пользователем 1:1
    # ondelete="CASCADE" - при удалении пользователя удаляется и баланс

    # Текущий баланс
    balance = Column(
        Numeric(10, 2),
        nullable=False,
        default=0
    )

    # Временные метки
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationship с User (обратная связь)
    user = relationship("User", back_populates="balance_info")

    def __repr__(self):
        return f"<UserBalance(user_id={self.user_id}, balance={self.balance})>"
