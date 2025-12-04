from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.models.user import User
from app.models.prediction import Prediction
from app.schemas.prediction import PredictionResponse
from app.api.auth import get_current_user

router = APIRouter()


@router.get("/")
async def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    predictions = db.query(Prediction).filter(
        Prediction.user_id == current_user.id
    ).order_by(Prediction.created_at.desc()).limit(50).all()

    return {
        "predictions": [
            {
                "id": p.id,
                "status": p.status.value,
                "cost_charged": float(p.cost_charged),
                "created_at": p.created_at,
                "input_data": p.input_data,
                "result": p.result
            }
            for p in predictions
        ]
    }


@router.get("/{prediction_id}", response_model=PredictionResponse)
async def get_prediction_by_id(
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
