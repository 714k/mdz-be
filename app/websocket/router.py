from typing import Callable, Dict
from fastapi import WebSocket
import structlog
from app.schemas.websocket import (
    ErrorMessage,
)

logger = structlog.get_logger()


class MessageRouter:
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}

    def register(self, message_type: str):
        def decorator(func: Callable):
            self.handlers[message_type] = func
            return func

        return decorator

    async def route(
        self, message: dict, websocket: WebSocket, session_id: str, user_id: int
    ):
        message_type = message.get("type")

        if not message_type:
            await self.send_error(websocket, "missing_type", "Message type is required")
            return

        handler = self.handlers.get(message_type)

        if not handler:
            await self.send_error(
                websocket, "unknown_type", f"Unknown message type: {message_type}"
            )
            return

        try:
            await handler(message, websocket, session_id, user_id)
        except Exception as e:
            logger.error("message_handler_error", type=message_type, error=str(e))
            await self.send_error(
                websocket, "handler_error", str(e), message.get("request_id")
            )

    async def send_error(
        self, websocket: WebSocket, code: str, error: str, request_id: str = None
    ):
        error_msg = ErrorMessage(error=error, code=code, request_id=request_id)
        await websocket.send_json(error_msg.model_dump(mode="json"))


router = MessageRouter()
