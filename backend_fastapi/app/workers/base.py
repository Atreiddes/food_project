import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from app.messaging.task_schema import MLTaskMessage


logger = logging.getLogger(__name__)


@dataclass
class WorkerResult:
    success: bool
    prediction_id: str
    response: Optional[str] = None
    error: Optional[str] = None
    processing_started_at: Optional[datetime] = None
    processing_finished_at: Optional[datetime] = None

    @property
    def processing_time_ms(self) -> int:
        if self.processing_started_at and self.processing_finished_at:
            delta = self.processing_finished_at - self.processing_started_at
            return int(delta.total_seconds() * 1000)
        return 0


class BaseWorker(ABC):
    def __init__(self, worker_id: Optional[str] = None):
        self._worker_id = worker_id or self._generate_worker_id()
        self._processed_count = 0
        self._failed_count = 0

    @property
    def worker_id(self) -> str:
        return self._worker_id

    @property
    def processed_count(self) -> int:
        return self._processed_count

    @property
    def failed_count(self) -> int:
        return self._failed_count

    @property
    def success_rate(self) -> float:
        total = self._processed_count + self._failed_count
        if total == 0:
            return 0.0
        return self._processed_count / total

    def _generate_worker_id(self) -> str:
        import uuid
        return f"worker-{uuid.uuid4().hex[:8]}"

    @abstractmethod
    async def process(self, task: MLTaskMessage) -> WorkerResult:
        pass

    @abstractmethod
    async def validate(self, task: MLTaskMessage) -> bool:
        pass

    async def execute(self, task: MLTaskMessage) -> WorkerResult:
        logger.info(
            f"[{self._worker_id}] Processing task: prediction_id={task.prediction_id}"
        )

        is_valid = await self.validate(task)
        if not is_valid:
            self._failed_count += 1
            return WorkerResult(
                success=False,
                prediction_id=task.prediction_id,
                error="Validation failed"
            )

        result = await self.process(task)

        if result.success:
            self._processed_count += 1
        else:
            self._failed_count += 1

        logger.info(
            f"[{self._worker_id}] Task completed: prediction_id={task.prediction_id}, "
            f"success={result.success}, time={result.processing_time_ms}ms"
        )

        return result

    async def shutdown(self) -> None:
        logger.info(
            f"[{self._worker_id}] Shutting down. "
            f"Processed: {self._processed_count}, Failed: {self._failed_count}"
        )
