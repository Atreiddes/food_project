from sqlalchemy import Column, String, DECIMAL, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
import enum
from app.db.base import Base


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    ML_REQUEST = "ml_request"
    REFUND = "refund"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    type = Column(SQLEnum(TransactionType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    status = Column(SQLEnum(TransactionStatus, values_callable=lambda x: [e.value for e in x]), default=TransactionStatus.PENDING, nullable=False)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
