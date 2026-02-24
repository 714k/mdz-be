from typing import Dict, Set, Optional
from fastapi import WebSocket
from datetime import datetime, timezone

import asyncio
import structlog
from app.core.cache import cache

logger = structlog.get_logger()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[int, Set[str]] = {}
        self.heartbeat_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket, session_id: str, user_id: int):
        await websocket.accept()

        self.active_connections[session_id] = websocket

        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(session_id)

        await cache.set(
            f"ws:session:{session_id}",
            {
                "user_id": user_id,
                "connected_at": datetime.now(timezone.utc).isoformat(),
                "last_heartbeat": datetime.now(timezone.utc).isoformat(),
            },
            expire=3600,
        )

        logger.info("websocket_connected", session_id=session_id, user_id=user_id)

        if not self.heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self.heartbeat_monitor())

    async def disconnect(self, session_id: str, user_id: int):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

        if user_id in self.user_sessions:
            self.user_sessions[user_id].discard(session_id)
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]

        await cache.delete(f"ws:session:{session_id}")

        logger.info("websocket_disconnected", session_id=session_id, user_id=user_id)

    async def send_personal_message(self, message: dict, session_id: str):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
            except Exception as e:
                logger.error("send_message_failed", session_id=session_id, error=str(e))

    async def send_to_user(self, message: dict, user_id: int):
        if user_id in self.user_sessions:
            for session_id in self.user_sessions[user_id]:
                await self.send_personal_message(message, session_id)

    async def broadcast(self, message: dict, exclude: Optional[Set[str]] = None):
        exclude = exclude or set()
        for session_id in self.active_connections:
            if session_id not in exclude:
                await self.send_personal_message(message, session_id)

    async def heartbeat_monitor(self):
        while True:
            await asyncio.sleep(30)

            now = datetime.now(timezone.utc)
            stale_sessions = []
            stale_session_data: dict = {}

            for session_id in list(self.active_connections.keys()):
                session_data = await cache.get(f"ws:session:{session_id}")

                if session_data:
                    last_heartbeat = datetime.fromisoformat(
                        session_data["last_heartbeat"]
                    )
                    if (now - last_heartbeat).total_seconds() > 90:
                        stale_sessions.append(session_id)
                        stale_session_data[session_id] = session_data
                else:
                    stale_sessions.append(session_id)
                    stale_session_data[session_id] = None

            for session_id in stale_sessions:
                logger.warning("stale_session_detected", session_id=session_id)
                if session_id in self.active_connections:
                    try:
                        await self.active_connections[session_id].close()
                    except Exception:
                        pass

                session_data = stale_session_data.get(session_id)
                if session_data:
                    await self.disconnect(session_id, int(session_data["user_id"]))
                else:
                    self.active_connections.pop(session_id, None)


manager = ConnectionManager()
