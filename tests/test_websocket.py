import pytest

# import asyncio
from fastapi.testclient import TestClient
from app.main import app


@pytest.mark.asyncio
async def test_websocket_connection():
    client = TestClient(app)

    with client.websocket_connect("/api/v1/ws?token=test_token") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "status"
        assert data["status"] == "connected"


@pytest.mark.asyncio
async def test_heartbeat():
    client = TestClient(app)

    with client.websocket_connect("/api/v1/ws?token=test_token") as websocket:
        websocket.send_json({"type": "heartbeat"})

        data = websocket.receive_json()
        assert data["type"] == "heartbeat_ack"


@pytest.mark.asyncio
async def test_chat_message():
    client = TestClient(app)

    with client.websocket_connect("/api/v1/ws?token=test_token") as websocket:
        websocket.send_json(
            {"type": "chat.message", "content": "Hello", "request_id": "test_123"}
        )

        status_msg = websocket.receive_json()
        assert status_msg["type"] == "status"

        response = websocket.receive_json()
        assert response["type"] == "chat.response"
        assert response["request_id"] == "test_123"
