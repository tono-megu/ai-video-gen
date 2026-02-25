"""WebSocket進捗通知"""

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    """WebSocket接続管理"""

    def __init__(self):
        # project_id -> list of websockets
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: str):
        """接続を追加"""
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)

    def disconnect(self, websocket: WebSocket, project_id: str):
        """接続を削除"""
        if project_id in self.active_connections:
            if websocket in self.active_connections[project_id]:
                self.active_connections[project_id].remove(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]

    async def send_progress(self, project_id: str, stage: str, progress: int, message: str):
        """進捗を送信"""
        if project_id not in self.active_connections:
            return

        data = json.dumps({
            "type": "progress",
            "stage": stage,
            "progress": progress,
            "message": message,
        })

        for websocket in self.active_connections[project_id]:
            try:
                await websocket.send_text(data)
            except Exception:
                pass

    async def send_complete(self, project_id: str, stage: str, result: dict | None = None):
        """完了を送信"""
        if project_id not in self.active_connections:
            return

        data = json.dumps({
            "type": "complete",
            "stage": stage,
            "result": result,
        })

        for websocket in self.active_connections[project_id]:
            try:
                await websocket.send_text(data)
            except Exception:
                pass

    async def send_error(self, project_id: str, stage: str, error: str):
        """エラーを送信"""
        if project_id not in self.active_connections:
            return

        data = json.dumps({
            "type": "error",
            "stage": stage,
            "error": error,
        })

        for websocket in self.active_connections[project_id]:
            try:
                await websocket.send_text(data)
            except Exception:
                pass


# グローバルマネージャー
manager = ConnectionManager()


@router.websocket("/projects/{project_id}/progress")
async def websocket_progress(websocket: WebSocket, project_id: UUID):
    """プロジェクト進捗のWebSocket"""
    project_id_str = str(project_id)
    await manager.connect(websocket, project_id_str)

    try:
        while True:
            # クライアントからのメッセージを待機（キープアライブ）
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0,
                )
                # pingに対してpongを返す
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # タイムアウト時はpingを送信
                await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id_str)
    except Exception:
        manager.disconnect(websocket, project_id_str)
