from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal

from app.db.base import get_db
from app.models.user import User
from app.schemas.prediction import PredictionCreate, PredictionResponse
from app.api.auth import get_current_user
from app.core.config import settings
from app.core.logging_config import app_logger
from app.services.balance import BalanceService, TransactionService
from app.services.prediction import PredictionService
from app.messaging.publisher import TaskPublisherFactory
from app.messaging.task_schema import MLTaskMessage, TaskPriority


router = APIRouter()

ML_REQUEST_COST = Decimal(str(settings.ML_SERVICE_COST_PER_REQUEST))


@router.post("/message", response_model=PredictionResponse)
async def send_message(
    request: PredictionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message to ML model for processing."""
    balance_service = BalanceService(db)
    transaction_service = TransactionService(db)
    prediction_service = PredictionService(db)

    if not balance_service.has_sufficient_balance(current_user.id, ML_REQUEST_COST):
        current_balance = balance_service.get_balance(current_user.id)
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient balance. Required: {ML_REQUEST_COST}, Available: {current_balance}"
        )

    prediction = prediction_service.create_pending(
        user_id=current_user.id,
        model_id=settings.OLLAMA_MODEL,
        message=request.message,
        conversation_history=request.conversation_history or [],
        cost=ML_REQUEST_COST
    )

    balance_service.deduct(current_user.id, ML_REQUEST_COST)

    description = f"ML request: {request.message[:50]}..."
    transaction_service.create_ml_request_transaction(
        user_id=current_user.id,
        amount=ML_REQUEST_COST,
        description=description
    )

    db.commit()
    db.refresh(prediction)

    task = MLTaskMessage(
        prediction_id=prediction.id,
        user_id=current_user.id,
        message=request.message,
        conversation_history=request.conversation_history or [],
        model_id=settings.OLLAMA_MODEL,
        priority=TaskPriority.NORMAL
    )

    publisher = await TaskPublisherFactory.get_publisher()
    published = await publisher.publish(task)

    if not published:
        app_logger.error(f"Failed to publish task for prediction {prediction.id}")

    return PredictionResponse(
        id=prediction.id,
        user_id=prediction.user_id,
        model_id=prediction.model_id,
        status=prediction.status.value,
        cost_charged=prediction.cost_charged,
        result=None,
        error_message=None,
        created_at=prediction.created_at
    )


@router.get("/status/{prediction_id}", response_model=PredictionResponse)
async def get_prediction_status(
    prediction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the status of a prediction."""
    prediction_service = PredictionService(db)
    prediction = prediction_service.get_by_id_and_user(prediction_id, current_user.id)

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )

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
