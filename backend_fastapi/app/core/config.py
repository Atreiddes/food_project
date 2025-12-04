from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "ML Nutrition Service"
    VERSION: str = "1.0.0"

    # Database
    DB_HOST: str = "database"
    DB_PORT: int = 5432
    DB_NAME: str = "nutrimarket_db"
    DB_USER: str = "nutrimarket_user"
    DB_PASSWORD: str = "nutrimarket_pass"

    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24

    def validate_jwt_secret(self) -> None:
        if not self.JWT_SECRET:
            raise ValueError("JWT_SECRET environment variable is required")
        if len(self.JWT_SECRET) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long for security")
        if self.JWT_SECRET in ["your-secret-key", "change-me", "secret", "test"]:
            raise ValueError("JWT_SECRET cannot be a common/default value. Generate a secure random key!")

    # ML Service
    ML_SERVICE_COST_PER_REQUEST: int = 10
    DEFAULT_USER_BALANCE: int = 1000

    # Ollama
    OLLAMA_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "mistral"

    # RabbitMQ
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "admin"
    RABBITMQ_PASS: str = "admin"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"

    @property
    def CORS_ORIGINS_LIST(self) -> list:
        """Convert comma-separated CORS origins to a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def RABBITMQ_URL(self) -> str:
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASS}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
settings.validate_jwt_secret()
