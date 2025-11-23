"""
SQLAlchemy модели
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.db.session import Base

class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique= True, nullable=False)
    hashed_password = Column(String(255))
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MLModel(Base):
    """Модель ML модели"""
    __tablename__ = "ml_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    version = Column(String(50))
    cost_per_request = Column(Float, default=0.01)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Prediction(Base):
    """Модель предсказания"""
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    model_id = Column(Integer, ForeignKey("ml_models.id"))
    input_data = Column(Text)
    output_result = Column(Text)
    status = Column(String(50), default="completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
