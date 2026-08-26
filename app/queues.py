"""The waiting line between the agent and the worker."""

from __future__ import annotations

from typing import Optional

import redis

from app.config import settings
from app.envelope import ExecutionEnvelope

QUEUE_KEY = "flyrank:queue"


def get_redis() -> "redis.Redis":
    return redis.from_url(settings.redis_url, decode_responses=True)


def publish(envelope: ExecutionEnvelope, client: Optional["redis.Redis"] = None) -> None:
    (client or get_redis()).lpush(QUEUE_KEY, envelope.to_json())


def depth(client: Optional["redis.Redis"] = None) -> int:
    return (client or get_redis()).llen(QUEUE_KEY)


def peek(limit: int = 10, client: Optional["redis.Redis"] = None) -> list:
    raw = (client or get_redis()).lrange(QUEUE_KEY, 0, limit - 1)
    return [ExecutionEnvelope.from_json(r) for r in raw]
