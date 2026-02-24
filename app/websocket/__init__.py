from app.websocket.manager import manager
from app.websocket.router import router
from app.websocket import handlers as _handlers  # noqa: F401 — registers @router.register handlers

__all__ = ["manager", "router"]
