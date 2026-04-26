import asyncio
import json
import time

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

log = structlog.get_logger()
router = APIRouter()


@router.websocket("/ws/echo/{client_id}")
async def ws_echo(
    websocket: WebSocket,
    client_id: str,
    heartbeat_interval: int = 30,
    heartbeat_timeout: int = 5,
) -> None:
    await websocket.accept()
    print(f"Client {client_id} connected")
    log.info("client_connected", client_id=client_id)

    pong_event = asyncio.Event()

    async def _heartbeat() -> None:
        while True:
            await asyncio.sleep(heartbeat_interval)
            pong_event.clear()
            try:
                await websocket.send_text(
                    json.dumps({"type": "ping", "ts": int(time.time())})
                )
            except Exception:
                return
            try:
                await asyncio.wait_for(
                    pong_event.wait(), timeout=float(heartbeat_timeout)
                )
            except asyncio.TimeoutError:
                log.warning("heartbeat_timeout_closing", client_id=client_id)
                try:
                    await websocket.close(code=1001)
                except Exception:
                    pass
                return

    heartbeat_task = asyncio.create_task(_heartbeat())

    try:
        while True:
            message = await websocket.receive()

            if message["type"] == "websocket.disconnect":
                print(f"Client {client_id} disconnected")
                log.info("client_disconnected", client_id=client_id)
                break

            text = message.get("text")
            data = message.get("bytes")

            if text is not None:
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict) and parsed.get("type") == "pong":
                        pong_event.set()
                        continue
                except (json.JSONDecodeError, ValueError):
                    pass
                await websocket.send_text(f"Echo: {text}")

            elif data is not None:
                await websocket.send_bytes(data)

    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
        log.info("client_disconnected", client_id=client_id)
    finally:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
