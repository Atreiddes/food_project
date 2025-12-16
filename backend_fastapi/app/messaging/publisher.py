import logging
from abc import ABC, abstractmethod
from typing import Optional

import aio_pika
from aio_pika import Message, DeliveryMode

from app.core.config import settings
from .connection import RabbitMQConnection
from .task_schema import MLTaskMessage


logger = logging.getLogger(__name__)


class BasePublisher(ABC):
    def __init__(self, queue_name: str):
        self._queue_name = queue_name
        self._connection_manager: Optional[RabbitMQConnection] = None

    @property
    def queue_name(self) -> str:
        return self._queue_name

    async def _ensure_connection(self) -> None:
        if self._connection_manager is None:
            self._connection_manager = await RabbitMQConnection.get_instance()

    @abstractmethod
    async def publish(self, message: MLTaskMessage) -> bool:
        pass


class TaskPublisher(BasePublisher):
    def __init__(self):
        super().__init__(settings.QUEUE_NAME)

    async def _declare_queue(self) -> aio_pika.Queue:
        await self._ensure_connection()
        channel = await self._connection_manager.get_channel()
        queue = await channel.declare_queue(
            self._queue_name,
            durable=True,
            arguments={
                "x-message-ttl": settings.QUEUE_MESSAGE_TTL,
                "x-max-length": settings.QUEUE_MAX_LENGTH,
            }
        )
        return queue

    async def publish(self, task: MLTaskMessage) -> bool:
        try:
            await self._declare_queue()
            channel = await self._connection_manager.get_channel()

            message = Message(
                body=task.to_json().encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                priority=task.priority.value,
                content_type="application/json",
            )

            await channel.default_exchange.publish(
                message,
                routing_key=self._queue_name,
            )

            logger.info(
                f"Task published: prediction_id={task.prediction_id}, "
                f"priority={task.priority.name}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to publish task: {e}")
            return False


class TaskPublisherFactory:
    _publisher: Optional[TaskPublisher] = None

    @classmethod
    async def get_publisher(cls) -> TaskPublisher:
        if cls._publisher is None:
            cls._publisher = TaskPublisher()
        return cls._publisher
