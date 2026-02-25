from fastapi import WebSocket
import structlog
from datetime import datetime, timezone
from app.websocket.router import router
from app.core.cache import cache
from app.schemas.websocket import ChatMessageResponse, StatusMessage

logger = structlog.get_logger()


@router.register("heartbeat")
async def handle_heartbeat(
    message: dict, websocket: WebSocket, session_id: str, user_id: int
):
    await cache.set(
        f"ws:session:{session_id}",
        {
            "user_id": user_id,
            "last_heartbeat": datetime.now(timezone.utc).isoformat(),
        },
        expire=3600,
    )
    await websocket.send_json({"type": "heartbeat_ack"})


@router.register("chat.message")
async def handle_chat_message(
    message: dict, websocket: WebSocket, session_id: str, user_id: int
):
    request_id = message.get("request_id")
    payload = message.get("payload", {})
    content = payload.get("content")
    model = payload.get("model", message.get("model", "meta-llama/Llama-2-7b-chat-hf"))
    context = payload.get("context", {})

    logger.info(
        "chat_message_received", user_id=user_id, request_id=request_id, model=model
    )

    await websocket.send_json(
        StatusMessage(
            status="processing", message="Processing your request..."
        ).model_dump(mode="json")
    )

    response_content = (
        f"Context: {context}, \nContext items: {len(context)}\nMessage: {content} "
    )

    response = ChatMessageResponse(
        content=response_content, request_id=request_id, model=model
    )

    await websocket.send_json(response.model_dump(mode="json"))

    await websocket.send_json(StatusMessage(status="idle").model_dump(mode="json"))


@router.register("context.update")
async def handle_context_update(
    message: dict, websocket: WebSocket, session_id: str, user_id: int
):
    context = message.get("context", {})

    logger.info("context_updated", user_id=user_id, context_keys=list(context.keys()))

    await websocket.send_json({"type": "context.ack", "received": len(context)})


@router.register("ping")
async def handle_ping(
    message: dict, websocket: WebSocket, session_id: str, user_id: int
):
    await websocket.send_json(
        {"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()}
    )
