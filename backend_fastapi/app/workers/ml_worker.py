import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.messaging.task_schema import MLTaskMessage
from app.services.ollama import OllamaService, OllamaServiceFactory
from app.workers.base import BaseWorker, WorkerResult
from app.workers.validators import TaskValidatorFactory, ValidationResult
from app.workers.handlers import PredictionResultHandler, PredictionStatusUpdater


logger = logging.getLogger(__name__)


class MLWorker(BaseWorker):
    def __init__(
        self,
        db_session_factory,
        ollama_service: Optional[OllamaService] = None,
        worker_id: Optional[str] = None
    ):
        super().__init__(worker_id)
        self._db_session_factory = db_session_factory
        self._ollama_service = ollama_service or OllamaServiceFactory.get_service()
        self._validator = TaskValidatorFactory.create_ml_task_validator()
        self._result_handler = PredictionResultHandler()

    async def validate(self, task: MLTaskMessage) -> bool:
        data = {
            "message": task.message,
            "conversation_history": task.conversation_history
        }
        validation_result = self._validator.validate(data)

        if not validation_result.is_valid:
            logger.warning(
                f"[{self._worker_id}] Validation failed for task {task.prediction_id}: "
                f"{validation_result.error_message}"
            )
            await self._save_validation_error(task.prediction_id, validation_result)

        return validation_result.is_valid

    async def _save_validation_error(
        self,
        prediction_id: str,
        validation_result: ValidationResult
    ) -> None:
        db = self._db_session_factory()
        try:
            status_updater = PredictionStatusUpdater(db)
            status_updater.mark_failed(
                prediction_id,
                f"Validation error: {validation_result.error_message}"
            )
        finally:
            db.close()

    async def process(self, task: MLTaskMessage) -> WorkerResult:
        started_at = datetime.utcnow()
        db = self._db_session_factory()

        try:
            status_updater = PredictionStatusUpdater(db)
            status_updater.mark_processing(task.prediction_id)

            ollama_response = await self._ollama_service.chat(
                message=task.message,
                conversation_history=task.conversation_history
            )

            finished_at = datetime.utcnow()

            if ollama_response.success:
                result = WorkerResult(
                    success=True,
                    prediction_id=task.prediction_id,
                    response=ollama_response.content,
                    processing_started_at=started_at,
                    processing_finished_at=finished_at
                )
            else:
                result = WorkerResult(
                    success=False,
                    prediction_id=task.prediction_id,
                    error=ollama_response.error,
                    processing_started_at=started_at,
                    processing_finished_at=finished_at
                )

            self._result_handler.handle(result, db)
            return result

        except Exception as e:
            logger.error(f"[{self._worker_id}] Error processing task: {e}")
            finished_at = datetime.utcnow()

            result = WorkerResult(
                success=False,
                prediction_id=task.prediction_id,
                error=str(e),
                processing_started_at=started_at,
                processing_finished_at=finished_at
            )
            self._result_handler.handle(result, db)
            return result

        finally:
            db.close()


class MLWorkerFactory:
    @staticmethod
    def create(db_session_factory, worker_id: Optional[str] = None) -> MLWorker:
        return MLWorker(
            db_session_factory=db_session_factory,
            worker_id=worker_id
        )
