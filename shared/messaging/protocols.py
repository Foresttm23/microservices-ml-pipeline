from typing import Protocol


class Processor[MessageT, PayloadT](Protocol):
    async def process(self, task: MessageT) -> PayloadT: ...


class Publisher[PublishT](Protocol):
    async def publish(self, payload: PublishT) -> None: ...
