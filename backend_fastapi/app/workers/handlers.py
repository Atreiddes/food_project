import logging
from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy.orm import Session

from app.models.prediction import Prediction, PredictionStatus
from app.workers.base import WorkerResult


logger = logging.getLogger(__name__)


class BaseResultHandler(ABC):
    @abstractmethod
    def handle(self, result: WorkerResult, db: Session) -> bool:
        pass


class PredictionResultHandler(BaseResultHandler):
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


class PredictionStatusUpdater:
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
