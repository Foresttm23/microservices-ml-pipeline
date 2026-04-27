from loguru import logger

from ..schemas.result import ResultMessage


# TODO if queue broker and implementation exists, implements the connecting and publishing to the class
class ResultPublisher:
    async def publish(self, result: ResultMessage) -> None:
        # Queue publishing is not wired yet, so we log the payload for now.
        logger.info(
            "Publishing result interaction_id={} status={} payload={}",
            result.interaction_id,
            result.status,
            result.model_dump_json(),
        )
