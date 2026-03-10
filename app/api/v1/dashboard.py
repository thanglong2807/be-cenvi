"""
WebSocket API cho Dashboard
Clients kết nối để nhận real-time updates từ Google Sheets
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Set
import json
import asyncio

from app.services.dashboard_sheet_service import dashboard_service
from app.core.config import settings

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# Quản lý WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        """Thêm client mới vào danh sách"""
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"✅ Client kết nối. Tổng clients: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Xóa client khi disconnect"""
        self.active_connections.discard(websocket)
        print(f"❌ Client ngắt kết nối. Tổng clients: {len(self.active_connections)}")
    
    async def broadcast(self, data: dict):
        """Gửi dữ liệu tới tất cả clients đang kết nối"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                print(f"⚠️ Lỗi gửi dữ liệu: {e}")
                disconnected.append(connection)
        
        # Xóa các connection bị lỗi
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint để clients kết nối và nhận real-time updates
    
    Message từ server:
    {
        "type": "data_update" | "initial",
        "data": {...},
        "timestamp": "2026-02-03T..."
    }
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Chờ message từ client (keep-alive)
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": __import__('datetime').datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.get("/data")
async def get_dashboard_data():
    """
    REST API để lấy dữ liệu dashboard hiện tại (không WebSocket)
    """
    range_name = f"'{settings.GOOGLE_SHEET_NAME}'!{settings.GOOGLE_SHEET_RANGE}"
    data = dashboard_service.fetch_data(range_name)
    
    if not data:
        return {"error": "Không thể lấy dữ liệu từ Sheet"}
    
    return {
        "type": "data",
        "timestamp": data['timestamp'],
        "rows_count": data['rows_count'],
        "cols_count": data['cols_count'],
        "data": data['data'][:10],  # Trả 10 dòng đầu cho demo
        "message": "Sử dụng /dashboard/ws để kết nối WebSocket và nhận updates real-time"
    }


@router.get("/parsed")
async def get_parsed_dashboard():
    """Return parsed JSON per employee for dashboard KPIs"""
    parsed = dashboard_service.parse_sheet_for_kpis()
    if parsed is None:
        return {"error": "Không thể lấy hoặc parse dữ liệu từ Sheet"}
    return {"type": "parsed", "count": len(parsed), "items": parsed}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "connected_clients": len(manager.active_connections),
        "sheet_id": settings.GOOGLE_SHEET_ID
    }


# ============================================================================
# BROADCAST FUNCTION (dùng trong background task)
# ============================================================================

async def broadcast_sheet_update(data: dict):
    """
    Gọi từ background task khi có dữ liệu mới từ Sheet
    
    Args:
        data: Dict chứa dữ liệu từ Google Sheet
    """
    # Also include parsed employee JSON so FE can consume structured data directly
    try:
        parsed_items = dashboard_service.parse_sheet_for_kpis()
    except Exception as e:
        parsed_items = None

    message = {
        "type": "data_update",
        "timestamp": data['timestamp'],
        "data": data['data'],  # Toàn bộ data
        "rows_count": data['rows_count'],
        "cols_count": data['cols_count'],
        "parsed": parsed_items
    }

    await manager.broadcast(message)
