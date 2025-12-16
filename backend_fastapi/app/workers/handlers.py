import logging
from abc import ABC, abstractmethod
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.prediction import Prediction, PredictionStatus
from app.services.balance import BalanceService, TransactionService
from app.workers.base import WorkerResult


logger = logging.getLogger(__name__)


class BaseResultHandler(ABC):
    @abstractmethod
    def handle(self, result: WorkerResult, db: Session) -> bool:
        pass


class PredictionResultHandler(BaseResultHandler):
    """Handler for processing prediction results with refund on failure."""

    def handle(self, result: WorkerResult, db: Session) -> bool:
        try:
            prediction = db.query(Prediction).filter(
                Prediction.id == result.prediction_id
            ).first()

            if not prediction:
                logger.error(f"Prediction not found: {result.prediction_id}")
                return False

            if result.success:
                prediction.status = PredictionStatus.COMPLETED
                prediction.result = {
                    "response": result.response,
                    "processing_time_ms": result.processing_time_ms
                }
                prediction.error_message = None
            else:
                prediction.status = PredictionStatus.FAILED
                prediction.error_message = result.error
                prediction.result = {"error": result.error}

                self._refund_user(db, prediction)

            db.commit()

            logger.info(
                f"Prediction updated: id={result.prediction_id}, "
                f"status={prediction.status.value}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to update prediction: {e}")
            db.rollback()
            return False

    def _refund_user(self, db: Session, prediction: Prediction) -> None:
        """Refund the user when prediction fails."""
        try:
            refund_amount = Decimal(str(prediction.cost_charged))

            if refund_amount <= 0:
                return

            balance_service = BalanceService(db)
            transaction_service = TransactionService(db)

            balance_service.refund(prediction.user_id, refund_amount)

            description = f"Refund for failed ML request: {prediction.id[:8]}..."
            transaction_service.create_refund_transaction(
                user_id=prediction.user_id,
                amount=refund_amount,
                description=description
            )

            logger.info(
                f"Refunded {refund_amount} to user {prediction.user_id} "
                f"for failed prediction {prediction.id}"
            )

        except Exception as e:
            logger.error(f"Failed to refund user: {e}")


class PredictionStatusUpdater:
    """Utility class for updating prediction status."""

    def __init__(self, db: Session):
        self._db = db

    def mark_processing(self, prediction_id: str) -> bool:
        try:
            prediction = self._db.query(Prediction).filter(
                Prediction.id == prediction_id
            ).first()

            if prediction:
                prediction.status = PredictionStatus.PROCESSING
                self._db.commit()
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to mark prediction as processing: {e}")
            self._db.rollback()
            return False

    def mark_failed(self, prediction_id: str, error: str) -> bool:
        try:
            prediction = self._db.query(Prediction).filter(
                Prediction.id == prediction_id
            ).first()

            if prediction:
                prediction.status = PredictionStatus.FAILED
                prediction.error_message = error
                self._db.commit()
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to mark prediction as failed: {e}")
            self._db.rollback()
            return False
