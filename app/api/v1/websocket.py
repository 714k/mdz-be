from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from datetime import datetime, timezone
import structlog
from app.core.security import decode_access_token
from app.websocket import manager, router

logger = structlog.get_logger()

ws_router = APIRouter()


@ws_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, token: str = Query(...)
):
    payload = decode_access_token(token)

    if not payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = int(payload.get("sub"))
    session_id = f"ws_{user_id}_{datetime.now(timezone.utc).timestamp()}"

    await manager.connect(websocket, session_id, user_id)

    await websocket.send_json(
        {
            "type": "status",
            "status": "connected",
            "session_id": session_id,
            "message": "Connection established",
        }
    )

    try:
        while True:
            data = await websocket.receive_json()
            await router.route(data, websocket, session_id, user_id)

    except WebSocketDisconnect:
        await manager.disconnect(session_id, user_id)
        logger.info("client_disconnected", session_id=session_id)

    except Exception as e:
        logger.error("websocket_error", session_id=session_id, error=str(e))
        await manager.disconnect(session_id, user_id)
        try:
            await websocket.close()
        except Exception:
            pass
