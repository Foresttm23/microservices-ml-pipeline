from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from shared.messaging import RedisPubSub, get_redis_client, result_channel

router = APIRouter()


@router.websocket("/ws/results/{user_id}")
async def results_socket(websocket: WebSocket, user_id: str = "anonymous") -> None:
    await websocket.accept()

    pubsub = RedisPubSub(get_redis_client())
    channel = result_channel(user_id)
    logger.info("WebSocket subscribed to {}", channel)

    try:
        async for message in pubsub.listen(channel):
            if isinstance(message, bytes):
                message = message.decode("utf-8")
            await websocket.send_text(message)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for user {}", user_id)
    except Exception:
        logger.exception("WebSocket error for user {}", user_id)
