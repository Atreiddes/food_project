"""
Базовая конфигурация БД
"""
from app.db.session import Base

# Import всех моделей для Alembic
from app.models.all_models import User, MLModel, Prediction
