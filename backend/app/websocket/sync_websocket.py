"""
스크립트-오디오 싱크 WebSocket 관리자

실시간 동기화, 위치 브로드캐스트, 매핑 업데이트 알림
"""

from uuid import UUID, uuid4
from typing import Optional, Dict, Any, List
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.routing import APIRouter
import json
import logging
import asyncio
from datetime import datetime

from app.core.auth import get_current_user_websocket, get_optional_user_websocket
from app.models.user import User
from app.models.sync import WebSocketMessage, WebSocketMessageType
from .connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


class SyncWebSocketManager:
    """스크립트-오디오 싱크 WebSocket 관리자"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
    
    async def connect_to_sync_room(
        self,
        websocket: WebSocket,
        script_id: str,
        user: Optional[User] = None,
        session_token: Optional[str] = None
    ):
        """싱크 룸에 연결"""
        try:
            # 연결 ID 생성
            connection_id = str(uuid4())
            
            # WebSocket 연결
            connection = await self.connection_manager.connect(
                websocket=websocket,
                connection_id=connection_id,
                user_id=user.id if user else None,
                client_info={
                    "script_id": script_id,
                    "session_token": session_token,
                    "connected_at": datetime.utcnow().isoformat()
                }
            )
            
            # 스크립트 룸 참가
            room_id = f"script:{script_id}"
            await self.connection_manager.join_room(connection_id, room_id)
            
            # 연결 확인 메시지 전송
            await connection.send_message({
                "type": WebSocketMessageType.CONNECTION_ACK.value,
                "data": {
                    "connection_id": connection_id,
                    "room_id": room_id,
                    "user_id": str(user.id) if user else None,
                    "message": "스크립트 싱크 룸에 연결되었습니다."
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return connection_id, room_id
            
        except Exception as e:
            logger.error(f"Error connecting to sync room: {str(e)}")
            await websocket.close(code=1011, reason="Connection failed")
            raise
    
    async def handle_sync_message(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ):
        """수신된 싱크 메시지 처리"""
        try:
            connection = self.connection_manager.connections.get(connection_id)
            if not connection:
                logger.warning(f"Connection {connection_id} not found")
                return
            
            message_type = message.get("type")
            data = message.get("data", {})
            
            script_id = connection.client_info.get("script_id")
            room_id = f"script:{script_id}"
            
            if message_type == WebSocketMessageType.POSITION_UPDATE.value:
                # 재생 위치 업데이트
                await self._handle_position_update(connection_id, room_id, data)
            
            elif message_type == WebSocketMessageType.MAPPING_EDIT.value:
                # 매핑 편집 알림
                await self._handle_mapping_edit(connection_id, room_id, data)
            
            elif message_type == WebSocketMessageType.PING.value:
                # Ping 응답
                await connection.send_message({
                    "type": WebSocketMessageType.PONG.value,
                    "data": {"timestamp": datetime.utcnow().isoformat()},
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
            
        except Exception as e:
            logger.error(f"Error handling sync message: {str(e)}")
    
    async def _handle_position_update(
        self,
        connection_id: str,
        room_id: str,
        data: Dict[str, Any]
    ):
        """재생 위치 업데이트 처리"""
        try:
            position = data.get("position", 0.0)
            is_playing = data.get("is_playing", False)
            sentence_id = data.get("sentence_id")
            
            # 룸의 다른 참가자들에게 브로드캐스트 (본인 제외)
            await self.connection_manager.broadcast_to_room(
                room_id,
                {
                    "type": WebSocketMessageType.POSITION_SYNC.value,
                    "data": {
                        "connection_id": connection_id,
                        "position": position,
                        "is_playing": is_playing,
                        "sentence_id": str(sentence_id) if sentence_id else None
                    },
                    "timestamp": datetime.utcnow().isoformat()
                },
                exclude_connections={connection_id}
            )
            
            logger.debug(f"Position update broadcasted to room {room_id}: {position}s")
            
        except Exception as e:
            logger.error(f"Error handling position update: {str(e)}")
    
    async def _handle_mapping_edit(
        self,
        connection_id: str,
        room_id: str,
        data: Dict[str, Any]
    ):
        """매핑 편집 알림 처리"""
        try:
            sentence_id = data.get("sentence_id")
            start_time = data.get("start_time")
            end_time = data.get("end_time")
            edit_type = data.get("edit_type", "manual")
            
            # 룸의 다른 참가자들에게 브로드캐스트
            await self.connection_manager.broadcast_to_room(
                room_id,
                {
                    "type": WebSocketMessageType.MAPPING_UPDATE.value,
                    "data": {
                        "connection_id": connection_id,
                        "sentence_id": str(sentence_id) if sentence_id else None,
                        "start_time": start_time,
                        "end_time": end_time,
                        "edit_type": edit_type
                    },
                    "timestamp": datetime.utcnow().isoformat()
                },
                exclude_connections={connection_id}
            )
            
            logger.debug(f"Mapping edit broadcasted to room {room_id}: sentence {sentence_id}")
            
        except Exception as e:
            logger.error(f"Error handling mapping edit: {str(e)}")
    
    async def broadcast_mapping_update(
        self,
        script_id: str,
        sentence_id: UUID,
        mapping_data: Dict[str, Any]
    ):
        """매핑 업데이트 브로드캐스트 (서비스 레이어에서 호출)"""
        try:
            room_id = f"script:{script_id}"
            
            await self.connection_manager.broadcast_to_room(
                room_id,
                {
                    "type": WebSocketMessageType.MAPPING_UPDATE.value,
                    "data": {
                        "sentence_id": str(sentence_id),
                        "mapping": mapping_data,
                        "action": "updated"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.debug(f"Mapping update broadcasted to script {script_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting mapping update: {str(e)}")
    
    async def broadcast_mapping_deletion(
        self,
        script_id: str,
        sentence_id: UUID
    ):
        """매핑 삭제 브로드캐스트"""
        try:
            room_id = f"script:{script_id}"
            
            await self.connection_manager.broadcast_to_room(
                room_id,
                {
                    "type": WebSocketMessageType.MAPPING_UPDATE.value,
                    "data": {
                        "sentence_id": str(sentence_id),
                        "action": "deleted"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.debug(f"Mapping deletion broadcasted to script {script_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting mapping deletion: {str(e)}")
    
    async def disconnect(self, connection_id: str):
        """연결 해제"""
        try:
            await self.connection_manager.disconnect(connection_id)
            logger.debug(f"WebSocket disconnected: {connection_id}")
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {str(e)}")
    
    def get_room_participants(self, script_id: str) -> List[Dict[str, Any]]:
        """룸 참가자 목록 조회"""
        room_id = f"script:{script_id}"
        return self.connection_manager.get_room_participants(room_id)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """연결 통계 조회"""
        return self.connection_manager.get_stats()


# 글로벌 인스턴스
_sync_websocket_manager: Optional[SyncWebSocketManager] = None


def get_sync_websocket_manager() -> SyncWebSocketManager:
    """싱크 WebSocket 매니저 조회"""
    global _sync_websocket_manager
    if _sync_websocket_manager is None:
        _sync_websocket_manager = SyncWebSocketManager()
    return _sync_websocket_manager


def set_sync_websocket_manager(manager: SyncWebSocketManager):
    """싱크 WebSocket 매니저 설정"""
    global _sync_websocket_manager
    _sync_websocket_manager = manager


# WebSocket 엔드포인트 라우터
websocket_router = APIRouter()


@websocket_router.websocket("/ws/sync/{script_id}")
async def websocket_sync_endpoint(
    websocket: WebSocket,
    script_id: str,
    token: Optional[str] = None
):
    """
    스크립트 실시간 싱크 WebSocket 엔드포인트
    
    - **script_id**: 스크립트 ID
    - **token**: JWT 토큰 (선택, 인증된 사용자용)
    """
    connection_id = None
    
    try:
        # 사용자 인증 (선택적)
        user = None
        if token:
            try:
                user = await get_current_user_websocket(token)
            except Exception as e:
                logger.warning(f"WebSocket auth failed: {str(e)}")
                # 인증 실패해도 익명으로 계속 진행
        
        # WebSocket 연결
        sync_manager = get_sync_websocket_manager()
        connection_id, room_id = await sync_manager.connect_to_sync_room(
            websocket=websocket,
            script_id=script_id,
            user=user
        )
        
        logger.info(f"WebSocket sync connected: {connection_id} to room {room_id}")
        
        # 메시지 수신 루프
        while True:
            try:
                # 메시지 수신 (타임아웃 60초)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                message = json.loads(data)
                
                # 메시지 처리
                await sync_manager.handle_sync_message(connection_id, message)
                
            except asyncio.TimeoutError:
                # Ping 전송으로 연결 유지 확인
                await websocket.send_text(json.dumps({
                    "type": WebSocketMessageType.PING.value,
                    "data": {},
                    "timestamp": datetime.utcnow().isoformat()
                }))
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {connection_id}")
                break
                
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from {connection_id}: {str(e)}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"error": "Invalid JSON format"},
                    "timestamp": datetime.utcnow().isoformat()
                }))
                
            except Exception as e:
                logger.error(f"Error in WebSocket loop: {str(e)}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"error": "Internal server error"},
                    "timestamp": datetime.utcnow().isoformat()
                }))
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
    
    finally:
        # 연결 정리
        if connection_id:
            sync_manager = get_sync_websocket_manager()
            await sync_manager.disconnect(connection_id) 