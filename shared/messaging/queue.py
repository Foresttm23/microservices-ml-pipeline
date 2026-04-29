from __future__ import annotations

from typing import Awaitable, cast

import redis.asyncio as redis

from . import RedisResource


class RedisQueue(RedisResource):
    def __init__(self, client: redis.Redis, name: str) -> None:
        super().__init__(client)
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def enqueue(self, payload: str | bytes) -> int:
        call = cast(Awaitable[int], self._client.rpush(self._name, payload))
        return await call

    async def dequeue(self, timeout: int | None = None) -> str | bytes | None:
        timeout_value = 0 if timeout is None else timeout

        call = cast(
            Awaitable[list], self._client.blpop(self._name, timeout=timeout_value)
        )
        item = await call
        if item is None:
            return None
        _, value = item
        return value

    async def size(self) -> int:
        call = cast(Awaitable[int], self._client.llen(self._name))
        return await call
