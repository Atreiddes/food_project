from decimal import Decimal
import uuid

from sqlalchemy.orm import Session

from app.models.prediction import Prediction, PredictionStatus


class PredictionService:
    """Service for managing prediction records."""

    def __init__(self, db: Session):
        self._db = db

    def create_pending(
        self,
        user_id: str,
        model_id: str,
        message: str,
        conversation_history: list,
        cost: Decimal
    ) -> Prediction:
        """Create a new pending prediction record."""
        prediction = Prediction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            model_id=model_id,
            input_data={
                "message": message,
                "conversation_history": conversation_history
            },
            status=PredictionStatus.PENDING,
            cost_charged=cost
        )
        self._db.add(prediction)
        return prediction

    def get_by_id(self, prediction_id: str) -> Prediction:
        """Get prediction by ID."""
        return self._db.query(Prediction).filter(
            Prediction.id == prediction_id
        ).first()

    def get_by_id_and_user(self, prediction_id: str, user_id: str) -> Prediction:
        """Get prediction by ID for specific user."""
        return self._db.query(Prediction).filter(
            Prediction.id == prediction_id,
            Prediction.user_id == user_id
        ).first()
