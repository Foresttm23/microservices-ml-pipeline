from __future__ import annotations

from abc import ABC

import redis.asyncio as redis


class RedisResource(ABC):
    def __init__(self, client: redis.Redis, key_prefix: str | None = None) -> None:
        self._client: redis.Redis = client
        self._key_prefix = key_prefix or ""

    @property
    def client(self) -> redis.Redis:
        return self._client

    @property
    def key_prefix(self) -> str:
        return self._key_prefix
