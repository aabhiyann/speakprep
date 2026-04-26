import json

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_echo_text(client: TestClient) -> None:
    with client.websocket_connect("/ws/echo/test1") as ws:
        ws.send_text("hello")
        assert ws.receive_text() == "Echo: hello"


def test_echo_binary(client: TestClient) -> None:
    with client.websocket_connect("/ws/echo/test2") as ws:
        ws.send_bytes(b"\x01\x02\x03")
        assert ws.receive_bytes() == b"\x01\x02\x03"


def test_heartbeat_closes_unresponsive_connection(client: TestClient) -> None:
    # interval=1s + timeout=1s: server sends ping at t=1, closes at t=2 if no pong
    with client.websocket_connect(
        "/ws/echo/test3?heartbeat_interval=1&heartbeat_timeout=1"
    ) as ws:
        ping = ws.receive_text()  # blocks until server sends ping (~1s)
        assert json.loads(ping)["type"] == "ping"
        with pytest.raises(WebSocketDisconnect):
            ws.receive_text()  # blocks until server closes (~1s) — raises
