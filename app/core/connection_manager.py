"""
WebSocket connection manager — broadcast workflow events to all connected clients.
"""
from __future__ import annotations
import json
import logging
from typing import Dict, List, Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts events."""

    def __init__(self):
        # Map connection_id -> WebSocket
        self._connections: Dict[int, WebSocket] = {}
        self._counter: int = 0

    async def connect(self, websocket: WebSocket) -> int:
        await websocket.accept()
        conn_id = self._counter
        self._counter += 1
        self._connections[conn_id] = websocket
        logger.info(f"[WS] Client #{conn_id} connected. Total: {len(self._connections)}")
        return conn_id

    def disconnect(self, conn_id: int):
        self._connections.pop(conn_id, None)
        logger.info(f"[WS] Client #{conn_id} disconnected. Total: {len(self._connections)}")

    async def broadcast(self, event: str, data: Any):
        """Send an event to all connected clients."""
        payload = json.dumps({"event": event, "data": data}, default=str)
        dead: List[int] = []
        for conn_id, ws in list(self._connections.items()):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(conn_id)
        for conn_id in dead:
            self.disconnect(conn_id)

    @property
    def connection_count(self) -> int:
        return len(self._connections)


# Singleton — import this instance everywhere
manager = ConnectionManager()
