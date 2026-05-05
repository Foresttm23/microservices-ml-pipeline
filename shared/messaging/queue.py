from typing import Awaitable, cast

import redis.asyncio as redis

from shared.messaging.base import RedisResource


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

    async def dequeue(self) -> str | bytes | None:
        """
        Dequeue a message from the queue.
        Blocks until there is a message in the queue.
        :return:
        """
        # timeout = 0, meaning not proceeding until receives a message
        item = await cast(
            Awaitable[list],
            self._client.blpop(self._name, timeout=0),
        )
        if item is None:
            return None
        _, value = item
        return value

    async def size(self) -> int:
        return await cast(Awaitable[int], self._client.llen(self._name))
