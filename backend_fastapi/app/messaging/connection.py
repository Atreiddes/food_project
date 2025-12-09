import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager

import aio_pika
from aio_pika import RobustConnection, RobustChannel
from aio_pika.abc import AbstractRobustConnection

from app.core.config import settings


logger = logging.getLogger(__name__)


class RabbitMQConnection:
    _instance: Optional["RabbitMQConnection"] = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(self):
        self._connection: Optional[AbstractRobustConnection] = None
        self._channel: Optional[RobustChannel] = None

    @classmethod
    async def get_instance(cls) -> "RabbitMQConnection":
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    async def connect(self) -> AbstractRobustConnection:
        if self._connection is None or self._connection.is_closed:
            self._connection = await aio_pika.connect_robust(
                settings.RABBITMQ_URL,
                timeout=30,
            )
            logger.info("Connected to RabbitMQ")
        return self._connection

    async def get_channel(self) -> RobustChannel:
        connection = await self.connect()
        if self._channel is None or self._channel.is_closed:
            self._channel = await connection.channel()
            await self._channel.set_qos(prefetch_count=1)
            logger.info("RabbitMQ channel created")
        return self._channel

    async def close(self) -> None:
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
            self._channel = None

        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            self._connection = None
            logger.info("RabbitMQ connection closed")

    @classmethod
    async def close_instance(cls) -> None:
        if cls._instance:
            await cls._instance.close()
            cls._instance = None


@asynccontextmanager
async def get_rabbitmq_channel():
    connection_manager = await RabbitMQConnection.get_instance()
    channel = await connection_manager.get_channel()
    try:
        yield channel
    finally:
        pass


async def check_rabbitmq_health() -> bool:
    try:
        connection_manager = await RabbitMQConnection.get_instance()
        connection = await connection_manager.connect()
        return not connection.is_closed
    except Exception as e:
        logger.error(f"RabbitMQ health check failed: {e}")
        return False
