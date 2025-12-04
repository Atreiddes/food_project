from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.base import get_db
from app.core.config import settings
from app.core.logging_config import app_logger
import httpx
import time
from typing import Dict, Any

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    Returns OK if the service is running.
    """
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.VERSION
    }


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check - verifies all dependencies are available.
    Checks database, Ollama, and RabbitMQ connectivity.
    """
    health_status: Dict[str, Any] = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {}
    }

    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "up",
            "message": "Database connection successful"
        }
    except Exception as e:
        app_logger.error(f"Database health check failed: {str(e)}")
        health_status["checks"]["database"] = {
            "status": "down",
            "message": f"Database connection failed: {str(e)}"
        }
        health_status["status"] = "unhealthy"

    # Check Ollama service
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                health_status["checks"]["ollama"] = {
                    "status": "up",
                    "message": "Ollama service is reachable"
                }
            else:
                health_status["checks"]["ollama"] = {
                    "status": "degraded",
                    "message": f"Ollama returned status {response.status_code}"
                }
    except Exception as e:
        app_logger.warning(f"Ollama health check failed: {str(e)}")
        health_status["checks"]["ollama"] = {
            "status": "down",
            "message": f"Ollama service unreachable: {str(e)}"
        }
        # Don't mark overall status as unhealthy for Ollama failures
        # since the API can function without it (predictions will just fail)

    # Check RabbitMQ (optional - only if we can ping it)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # RabbitMQ management API endpoint
            rabbitmq_management_url = f"http://{settings.RABBITMQ_HOST}:15672/api/overview"
            response = await client.get(
                rabbitmq_management_url,
                auth=(settings.RABBITMQ_USER, settings.RABBITMQ_PASS)
            )
            if response.status_code == 200:
                health_status["checks"]["rabbitmq"] = {
                    "status": "up",
                    "message": "RabbitMQ is reachable"
                }
            else:
                health_status["checks"]["rabbitmq"] = {
                    "status": "unknown",
                    "message": "RabbitMQ management API not accessible"
                }
    except Exception as e:
        app_logger.debug(f"RabbitMQ health check skipped: {str(e)}")
        health_status["checks"]["rabbitmq"] = {
            "status": "unknown",
            "message": "RabbitMQ health check not available"
        }

    # Return appropriate HTTP status code
    if health_status["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )

    return health_status


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check - verifies the service is alive.
    This is a simple check that always returns OK if the service is running.
    Used by orchestrators (Kubernetes, Docker Swarm) to detect if a restart is needed.
    """
    return {
        "status": "alive",
        "service": settings.APP_NAME
    }
