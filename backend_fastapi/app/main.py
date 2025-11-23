"""
Главный файл FastAPI приложения
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings

# Создание FastAPI приложения
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="NutriMarket ML Service API"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {"message": "NutriMarket ML Service API"}
