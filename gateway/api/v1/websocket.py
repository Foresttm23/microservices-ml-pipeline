from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Query
from loguru import logger
from gateway.core.config import get_settings
from shared.messaging import RedisPubSub, get_redis_client, result_channel
from shared.middlewares import decode_jwt_token, JWTSettingsProtocol

router = APIRouter()


@router.websocket("/ws/results/")
async def results_socket(websocket: WebSocket, token: str = Query("anonymous")) -> None:
    settings = get_settings()

    user_id = await validate_jwt(token, settings, websocket)
    if user_id is None:
        return

    await websocket.accept()

    pubsub = RedisPubSub(get_redis_client())
    channel = result_channel(user_id)
    logger.info("WebSocket subscribed to {}", channel)

    try:
        async for message in pubsub.listen(channel):
            if isinstance(message, bytes):
                message = message.decode("utf-8")
            await websocket.send_text(message)
            logger.info("Sent message to user {}", user_id)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for user {}", user_id)
    except Exception:
        logger.exception("WebSocket error for user {}", user_id)


async def validate_jwt(token: str, settings: JWTSettingsProtocol, websocket: WebSocket) -> str | None:
    user_id = "anonymous"

    if settings.JWT_ENABLED or token != "anonymous":
        if token == "anonymous":
            logger.warning("WebSocket rejected: JWT is enabled but token was not provided")
            await websocket.accept()
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

        try:
            payload = decode_jwt_token(token, settings)
            user_id = str(payload[settings.JWT_USER_ID_CLAIM])
        except Exception as exc:
            logger.warning("WebSocket JWT validation failed: {}", exc)
            await websocket.accept()
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

    return user_id
