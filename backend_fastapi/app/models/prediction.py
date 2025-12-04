from sqlalchemy import Column, String, Text, JSON, DECIMAL, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
import enum
from app.db.base import Base


class PredictionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    model_id = Column(String, nullable=False)
    input_data = Column(JSON, nullable=False)
    result = Column(JSON)
    status = Column(SQLEnum(PredictionStatus, values_callable=lambda x: [e.value for e in x]), default=PredictionStatus.PENDING, nullable=False)
    cost_charged = Column(DECIMAL(10, 2), default=0, nullable=False)
    validation_errors = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
