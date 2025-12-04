from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.logging_config import setup_logging, app_logger
from app.api import auth, predictions, balance, history, health
import time

# Setup structured logging
setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="REST API для ML сервиса рекомендаций по питанию"
)

# Add rate limiter state and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS from environment variables
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=[m.strip() for m in settings.CORS_ALLOW_METHODS.split(",")],
    allow_headers=[h.strip() for h in settings.CORS_ALLOW_HEADERS.split(",")],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing information."""
    start_time = time.time()

    # Log request
    app_logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "endpoint": f"{request.method} {request.url.path}",
            "client_ip": request.client.host if request.client else "unknown"
        }
    )

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log response
    app_logger.info(
        f"Request completed: {request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration:.3f}s",
        extra={
            "endpoint": f"{request.method} {request.url.path}",
            "status_code": response.status_code,
            "duration_seconds": round(duration, 3),
            "client_ip": request.client.host if request.client else "unknown"
        }
    )

    return response


# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(predictions.router, prefix="/api/chat", tags=["predictions"])
app.include_router(balance.router, prefix="/api/balance", tags=["balance"])
app.include_router(history.router, prefix="/api/history", tags=["history"])


@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "endpoints": {
            "health": {
                "basic": "GET /health",
                "readiness": "GET /health/ready",
                "liveness": "GET /health/live"
            },
            "auth": {
                "guest": "POST /api/auth/guest",
                "register": "POST /api/auth/register",
                "login": "POST /api/auth/login",
                "me": "GET /api/auth/me"
            },
            "chat": {
                "sendMessage": "POST /api/chat/message"
            },
            "balance": {
                "getBalance": "GET /api/balance",
                "addBalance": "POST /api/balance/add",
                "getTransactions": "GET /api/balance/transactions"
            },
            "history": {
                "getHistory": "GET /api/history",
                "getPrediction": "GET /api/history/{id}"
            }
        }
    }
