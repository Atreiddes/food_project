from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal
import uuid
import httpx

from app.db.base import get_db
from app.models.user import User
from app.models.user_balance import UserBalance
from app.models.prediction import Prediction, PredictionStatus
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.schemas.prediction import PredictionCreate, PredictionResponse
from app.api.auth import get_current_user
from app.core.config import settings
from app.core.logging_config import app_logger

router = APIRouter()

# Cost per ML request
ML_REQUEST_COST = Decimal(str(settings.ML_SERVICE_COST_PER_REQUEST))


async def call_ollama(message: str, conversation_history: list = None) -> dict:
    """
    Call Ollama API to get ML model response.
    Works only in Docker environment where Ollama service is available.
    """
    if conversation_history is None:
        conversation_history = []

    # Build messages for Ollama chat format
    messages = []

    # Add conversation history
    for msg in conversation_history:
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

    # Add current user message
    messages.append({
        "role": "user",
        "content": message
    })

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.OLLAMA_URL}/api/chat",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False
                }
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response": data.get("message", {}).get("content", ""),
                    "model": settings.OLLAMA_MODEL
                }
            else:
                app_logger.error(f"Ollama returned status {response.status_code}: {response.text}")
                return {
                    "success": False,
                    "error": f"Ollama service returned status {response.status_code}"
                }

    except httpx.TimeoutException:
        app_logger.error("Ollama request timed out")
        return {
            "success": False,
            "error": "ML service request timed out. Please try again."
        }
    except httpx.ConnectError:
        app_logger.error("Cannot connect to Ollama service")
        return {
            "success": False,
            "error": "ML service is not available. Make sure you're running in Docker environment."
        }
    except Exception as e:
        app_logger.error(f"Ollama request failed: {str(e)}")
        return {
            "success": False,
            "error": f"ML service error: {str(e)}"
        }


@router.post("/message", response_model=PredictionResponse)
async def send_message(
    request: PredictionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message to the ML model (Ollama).
    Deducts balance and creates prediction record.
    """
    # Check user balance
    balance_record = db.query(UserBalance).filter(
        UserBalance.user_id == current_user.id
    ).first()

    if not balance_record or balance_record.balance < ML_REQUEST_COST:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient balance. Required: {ML_REQUEST_COST}, Current: {balance_record.balance if balance_record else 0}"
        )

    # Create prediction record
    prediction_id = str(uuid.uuid4())
    prediction = Prediction(
        id=prediction_id,
        user_id=current_user.id,
        model_id=settings.OLLAMA_MODEL,
        input_data={
            "message": request.message,
            "conversation_history": request.conversation_history
        },
        status=PredictionStatus.PROCESSING,
        cost_charged=ML_REQUEST_COST
    )
    db.add(prediction)

    # Deduct balance
    balance_record.balance -= ML_REQUEST_COST

    # Create transaction record
    transaction = Transaction(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        type=TransactionType.ML_REQUEST,
        amount=-ML_REQUEST_COST,
        status=TransactionStatus.COMPLETED,
        description=f"ML request: {request.message[:50]}..."
    )
    db.add(transaction)

    db.commit()

    # Call Ollama ML model
    ollama_result = await call_ollama(
        message=request.message,
        conversation_history=request.conversation_history
    )

    # Update prediction based on result
    if ollama_result["success"]:
        prediction.status = PredictionStatus.COMPLETED
        prediction.result = {
            "response": ollama_result["response"],
            "model": ollama_result["model"]
        }
    else:
        prediction.status = PredictionStatus.FAILED
        prediction.error_message = ollama_result["error"]
        prediction.result = {"error": ollama_result["error"]}

    db.commit()
    db.refresh(prediction)

    return PredictionResponse(
        id=prediction.id,
        user_id=prediction.user_id,
        model_id=prediction.model_id,
        status=prediction.status.value,
        cost_charged=prediction.cost_charged,
        result=prediction.result,
        error_message=prediction.error_message,
        created_at=prediction.created_at
    )
