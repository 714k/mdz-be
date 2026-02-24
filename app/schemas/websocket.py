from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime, timezone


class WSMessage(BaseModel):
    type: str
    payload: dict = {}
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: Optional[str] = None


class HeartbeatMessage(BaseModel):
    type: Literal["heartbeat"] = "heartbeat"


class ChatMessageRequest(BaseModel):
    type: Literal["chat.message"] = "chat.message"
    content: str
    context: dict = {}
    model: str = "meta-llama/Llama-2-7b-chat-hf"
    request_id: str


class ChatMessageResponse(BaseModel):
    type: Literal["chat.response"] = "chat.response"
    content: str
    request_id: str
    model: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatStreamChunk(BaseModel):
    type: Literal["chat.stream"] = "chat.stream"
    chunk: str
    request_id: str
    done: bool = False


class ContextUpdateMessage(BaseModel):
    type: Literal["context.update"] = "context.update"
    context: dict


class ErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    error: str
    code: str
    request_id: Optional[str] = None


class StatusMessage(BaseModel):
    type: Literal["status"] = "status"
    status: Literal["connected", "processing", "idle", "error"]
    message: Optional[str] = None
