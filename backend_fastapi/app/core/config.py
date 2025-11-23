"""
Конфигурация приложения
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Настройки приложения"""
    PROJECT_NAME: str = "NutriMarket ML Service"
    DATABASE_URL: str = "postgresql://postgres:postgres@database:5432/nutrimarket"
    OLLAMA_URL: str = "http://ollama:11434"
    
    class Config:
        case_sensitive = True

settings = Settings()
