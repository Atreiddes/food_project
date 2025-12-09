import logging
from abc import ABC, abstractmethod
from typing import Callable, Awaitable, Optional

import aio_pika
from aio_pika import IncomingMessage

from .connection import RabbitMQConnection
from .task_schema import MLTaskMessage


logger = logging.getLogger(__name__)

MessageHandler = Callable[[MLTaskMessage], Awaitable[bool]]


class BaseConsumer(ABC):
    def __init__(self, queue_name: str):
        self._queue_name = queue_name
        self._connection_manager: Optional[RabbitMQConnection] = None
        self._consuming = False

    @property
    def queue_name(self) -> str:
        return self._queue_name

    @property
    def is_consuming(self) -> bool:
        return self._consuming

    async def _ensure_connection(self) -> None:
        if self._connection_manager is None:
            self._connection_manager = await RabbitMQConnection.get_instance()

    @abstractmethod
    async def process_message(self, message: IncomingMessage) -> None:
        pass

    async def start(self) -> None:
        await self._ensure_connection()
        channel = await self._connection_manager.get_channel()

        queue = await channel.declare_queue(
            self._queue_name,
            durable=True,
            arguments={
                "x-message-ttl": 3600000,
                "x-max-length": 10000,
            }
        )

        self._consuming = True
        logger.info(f"Started consuming from queue: {self._queue_name}")

        await queue.consume(self.process_message)

    async def stop(self) -> None:
        self._consuming = False
        logger.info(f"Stopped consuming from queue: {self._queue_name}")


class TaskConsumer(BaseConsumer):
    QUEUE_NAME = "ml_tasks"

    def __init__(self, handler: MessageHandler):
        super().__init__(self.QUEUE_NAME)
        self._handler = handler

    async def process_message(self, message: IncomingMessage) -> None:
        async with message.process(requeue=False):
            try:
                body = message.body.decode()
                task = MLTaskMessage.from_json(body)

                logger.info(
                    f"Received task: prediction_id={task.prediction_id}, "
                    f"retry={task.retry_count}"
                )

                success = await self._handler(task)

                if success:
                    logger.info(f"Task completed: prediction_id={task.prediction_id}")
                else:
                    await self._handle_failure(task)

            except Exception as e:
                logger.error(f"Error processing message: {e}")

    async def _handle_failure(self, task: MLTaskMessage) -> None:
        if task.can_retry():
            retry_task = task.increment_retry()
            logger.warning(
                f"Task failed, scheduling retry {retry_task.retry_count}/{task.max_retries}: "
                f"prediction_id={task.prediction_id}"
            )
            from .publisher import TaskPublisherFactory
            publisher = await TaskPublisherFactory.get_publisher()
            await publisher.publish(retry_task)
        else:
            logger.error(
                f"Task failed after {task.max_retries} retries: "
                f"prediction_id={task.prediction_id}"
            )
