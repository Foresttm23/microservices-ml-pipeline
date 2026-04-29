from __future__ import annotations

from collections.abc import AsyncIterator

from . import RedisResource


class RedisPubSub(RedisResource):
    def __init__(self, client, channel_prefix: str = "") -> None:
        super().__init__(client, channel_prefix)

    def channel_for(self, key: str) -> str:
        if self._key_prefix and not key.startswith(self._key_prefix):
            return f"{self._key_prefix}{key}"
        return key

    async def publish(self, channel: str, payload: str | bytes) -> int:
        return await self._client.publish(channel, payload)

    async def listen(self, channel: str) -> AsyncIterator[str | bytes]:
        pubsub = self._client.pubsub()
        await pubsub.subscribe(channel)
        try:
            async for message in pubsub.listen():
                if message.get("type") == "message":
                    yield message.get("data")
        finally:
            await pubsub.close()

