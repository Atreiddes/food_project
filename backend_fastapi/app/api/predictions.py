from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
from app.db.base import get_db
from app.models.user import User
from app.models.user_balance import UserBalance
from app.models.prediction import Prediction, PredictionStatus
from app.schemas.prediction import PredictionCreate, PredictionResponse
from app.api.auth import get_current_user
from app.core.config import settings
from app.core.exceptions import InsufficientBalanceError, DatabaseError
from app.core.rate_limit import limiter
import uuid

router = APIRouter()


@router.post("/message")
@limiter.limit("100/hour")
async def create_prediction(
    request: Request,
    prediction_data: PredictionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create prediction request.
    Checks and deducts balance from separate UserBalance entity (SRP).
    """
    cost = settings.ML_SERVICE_COST_PER_REQUEST

    # Get UserBalance entity
    user_balance = db.query(UserBalance).filter(
        UserBalance.user_id == current_user.id
    ).first()

    if not user_balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Balance not found"
        )

    # Check balance
    if user_balance.balance < cost:
        raise InsufficientBalanceError(
            f"Insufficient balance. Required: {cost}, Available: {user_balance.balance}"
        )

    prediction = Prediction(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        model_id="mistral",
        input_data={"message": prediction_data.message, "history": prediction_data.conversation_history},
        status=PredictionStatus.PENDING,
        cost_charged=cost
    )

    # Deduct from UserBalance, not User
    user_balance.balance -= cost

    db.add(prediction)
    try:
        db.commit()
        db.refresh(prediction)
        db.refresh(user_balance)
    except IntegrityError as e:
        db.rollback()
        raise DatabaseError(f"Failed to create prediction: {str(e)}")
    except OperationalError as e:
        db.rollback()
        raise DatabaseError(f"Database connection error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Unexpected error: {str(e)}")

    return {
        "predictionId": prediction.id,
        "remainingBalance": float(user_balance.balance),
        "message": "Prediction request submitted"
    }


@router.get("/prediction/{prediction_id}", response_model=PredictionResponse)
async def get_prediction(
    prediction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.user_id == current_user.id
    ).first()

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
