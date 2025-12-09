import asyncio
import logging
import signal
import sys
from typing import Optional

from app.db.base import SessionLocal
from app.messaging.consumer import TaskConsumer
from app.messaging.task_schema import MLTaskMessage
from app.workers.ml_worker import MLWorkerFactory


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


class WorkerRunner:
    def __init__(self):
        self._consumer: Optional[TaskConsumer] = None
        self._worker = MLWorkerFactory.create(
            db_session_factory=SessionLocal
        )
        self._shutdown_event = asyncio.Event()

    async def _handle_message(self, task: MLTaskMessage) -> bool:
        result = await self._worker.execute(task)
        return result.success

    def _setup_signal_handlers(self) -> None:
        loop = asyncio.get_event_loop()

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(self._shutdown())
            )

    async def _shutdown(self) -> None:
        logger.info("Shutdown signal received")
        self._shutdown_event.set()

        if self._consumer:
            await self._consumer.stop()

        await self._worker.shutdown()

    async def run(self) -> None:
        logger.info(f"Starting ML Worker: {self._worker.worker_id}")

        try:
            self._setup_signal_handlers()
        except NotImplementedError:
            logger.warning("Signal handlers not supported on this platform")

        self._consumer = TaskConsumer(handler=self._handle_message)

        try:
            await self._consumer.start()

            logger.info("Worker is ready and consuming messages")

            await self._shutdown_event.wait()

        except Exception as e:
            logger.error(f"Worker error: {e}")
            raise

        finally:
            logger.info("Worker stopped")


def main() -> None:
    runner = WorkerRunner()
    asyncio.run(runner.run())


if __name__ == "__main__":
    main()
