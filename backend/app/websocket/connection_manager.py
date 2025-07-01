"""
WebSocket 연결 관리자

클라이언트 연결, 룸 관리, 메시지 브로드캐스트
"""

from typing import Dict, List, Set, Optional, Any
from uuid import UUID
import json
import logging
import asyncio
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class Connection:
    """WebSocket 연결 정보"""
    
    def __init__(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: Optional[UUID] = None,
        client_info: Optional[Dict] = None
    ):
        self.websocket = websocket
        self.connection_id = connection_id
        self.user_id = user_id
        self.client_info = client_info or {}
        self.connected_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.rooms: Set[str] = set()
    
    async def send_message(self, message: Dict[str, Any]):
        """개별 메시지 전송"""
        try:
            await self.websocket.send_text(json.dumps(message))
            self.last_activity = datetime.utcnow()
            logger.debug(f"Message sent to {self.connection_id}: {message['type']}")
        except Exception as e:
            logger.error(f"Failed to send message to {self.connection_id}: {str(e)}")
            raise
    
    def join_room(self, room_id: str):
        """룸 참가"""
        self.rooms.add(room_id)
        logger.debug(f"Connection {self.connection_id} joined room {room_id}")
    
    def leave_room(self, room_id: str):
        """룸 나가기"""
        self.rooms.discard(room_id)
        logger.debug(f"Connection {self.connection_id} left room {room_id}")
    
    def leave_all_rooms(self):
        """모든 룸 나가기"""
        rooms_to_leave = self.rooms.copy()
        self.rooms.clear()
        return rooms_to_leave


class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        # 연결 관리
        self.connections: Dict[str, Connection] = {}
        
        # 룸 관리 (room_id -> set of connection_ids)
        self.rooms: Dict[str, Set[str]] = {}
        
        # 사용자별 연결 (user_id -> set of connection_ids)
        self.user_connections: Dict[UUID, Set[str]] = {}
        
        # 통계
        self.total_connections = 0
        self.total_messages_sent = 0
    
    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: Optional[UUID] = None,
        client_info: Optional[Dict] = None
    ) -> Connection:
        """새 연결 등록"""
        try:
            await websocket.accept()
            
            connection = Connection(
                websocket=websocket,
                connection_id=connection_id,
                user_id=user_id,
                client_info=client_info
            )
            
            self.connections[connection_id] = connection
            self.total_connections += 1
            
            # 사용자별 연결 추가
            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(connection_id)
            
            logger.info(
                f"WebSocket connected: {connection_id}, "
                f"user: {user_id}, total: {len(self.connections)}"
            )
            
            return connection
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket {connection_id}: {str(e)}")
            raise
    
    async def disconnect(self, connection_id: str):
        """연결 해제"""
        connection = self.connections.get(connection_id)
        if not connection:
            return
        
        try:
            # 모든 룸에서 나가기
            rooms_to_leave = connection.leave_all_rooms()
            for room_id in rooms_to_leave:
                await self._leave_room_internal(connection_id, room_id)
            
            # 사용자별 연결에서 제거
            if connection.user_id:
                user_conns = self.user_connections.get(connection.user_id)
                if user_conns:
                    user_conns.discard(connection_id)
                    if not user_conns:
                        del self.user_connections[connection.user_id]
            
            # 연결 제거
            del self.connections[connection_id]
            
            logger.info(
                f"WebSocket disconnected: {connection_id}, "
                f"remaining: {len(self.connections)}"
            )
            
        except Exception as e:
            logger.error(f"Error during disconnect {connection_id}: {str(e)}")
    
    async def join_room(self, connection_id: str, room_id: str):
        """룸 참가"""
        connection = self.connections.get(connection_id)
        if not connection:
            raise ValueError(f"Connection {connection_id} not found")
        
        # 연결을 룸에 추가
        connection.join_room(room_id)
        
        # 룸에 연결 추가
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(connection_id)
        
        # 룸 참가 알림
        await self.broadcast_to_room(
            room_id,
            {
                "type": "session_join",
                "room_id": room_id,
                "data": {
                    "connection_id": connection_id,
                    "user_id": str(connection.user_id) if connection.user_id else None,
                    "joined_at": connection.connected_at.isoformat(),
                    "participant_count": len(self.rooms[room_id])
                },
                "timestamp": datetime.utcnow().isoformat()
            },
            exclude_connections={connection_id}  # 본인 제외
        )
        
        logger.info(f"Connection {connection_id} joined room {room_id}")
    
    async def leave_room(self, connection_id: str, room_id: str):
        """룸 나가기"""
        connection = self.connections.get(connection_id)
        if not connection:
            return
        
        await self._leave_room_internal(connection_id, room_id)
        connection.leave_room(room_id)
    
    async def _leave_room_internal(self, connection_id: str, room_id: str):
        """내부 룸 나가기 처리"""
        if room_id in self.rooms:
            self.rooms[room_id].discard(connection_id)
            
            # 룸 나가기 알림
            await self.broadcast_to_room(
                room_id,
                {
                    "type": "session_leave",
                    "room_id": room_id,
                    "data": {
                        "connection_id": connection_id,
                        "left_at": datetime.utcnow().isoformat(),
                        "participant_count": len(self.rooms[room_id])
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # 빈 룸 제거
            if not self.rooms[room_id]:
                del self.rooms[room_id]
                logger.info(f"Room {room_id} removed (empty)")
        
        logger.info(f"Connection {connection_id} left room {room_id}")
    
    async def send_to_connection(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ):
        """특정 연결에 메시지 전송"""
        connection = self.connections.get(connection_id)
        if not connection:
            logger.warning(f"Connection {connection_id} not found for message")
            return False
        
        try:
            await connection.send_message(message)
            self.total_messages_sent += 1
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {str(e)}")
            # 연결 오류 시 자동 해제
            await self.disconnect(connection_id)
            return False
    
    async def send_to_user(
        self,
        user_id: UUID,
        message: Dict[str, Any]
    ):
        """특정 사용자의 모든 연결에 메시지 전송"""
        user_conns = self.user_connections.get(user_id)
        if not user_conns:
            return 0
        
        sent_count = 0
        for connection_id in user_conns.copy():  # copy to avoid modification during iteration
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_room(
        self,
        room_id: str,
        message: Dict[str, Any],
        exclude_connections: Optional[Set[str]] = None
    ):
        """룸의 모든 연결에 메시지 브로드캐스트"""
        room_connections = self.rooms.get(room_id)
        if not room_connections:
            logger.debug(f"No connections in room {room_id}")
            return 0
        
        exclude_connections = exclude_connections or set()
        sent_count = 0
        
        # 브로드캐스트 실행
        tasks = []
        for connection_id in room_connections.copy():
            if connection_id not in exclude_connections:
                tasks.append(self.send_to_connection(connection_id, message))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            sent_count = sum(1 for result in results if result is True)
        
        logger.debug(f"Broadcasted to room {room_id}: {sent_count}/{len(room_connections)} sent")
        return sent_count
    
    async def broadcast_to_all(
        self,
        message: Dict[str, Any],
        exclude_connections: Optional[Set[str]] = None
    ):
        """모든 연결에 메시지 브로드캐스트"""
        exclude_connections = exclude_connections or set()
        sent_count = 0
        
        tasks = []
        for connection_id in list(self.connections.keys()):
            if connection_id not in exclude_connections:
                tasks.append(self.send_to_connection(connection_id, message))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            sent_count = sum(1 for result in results if result is True)
        
        logger.info(f"Broadcasted to all: {sent_count}/{len(self.connections)} sent")
        return sent_count
    
    def get_room_participants(self, room_id: str) -> List[Dict[str, Any]]:
        """룸 참가자 목록 조회"""
        room_connections = self.rooms.get(room_id, set())
        participants = []
        
        for connection_id in room_connections:
            connection = self.connections.get(connection_id)
            if connection:
                participants.append({
                    "connection_id": connection_id,
                    "user_id": str(connection.user_id) if connection.user_id else None,
                    "connected_at": connection.connected_at.isoformat(),
                    "last_activity": connection.last_activity.isoformat(),
                    "client_info": connection.client_info
                })
        
        return participants
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """연결 정보 조회"""
        connection = self.connections.get(connection_id)
        if not connection:
            return None
        
        return {
            "connection_id": connection_id,
            "user_id": str(connection.user_id) if connection.user_id else None,
            "connected_at": connection.connected_at.isoformat(),
            "last_activity": connection.last_activity.isoformat(),
            "rooms": list(connection.rooms),
            "client_info": connection.client_info
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """연결 통계 조회"""
        return {
            "active_connections": len(self.connections),
            "total_connections": self.total_connections,
            "active_rooms": len(self.rooms),
            "total_messages_sent": self.total_messages_sent,
            "users_online": len(self.user_connections),
            "rooms_info": {
                room_id: len(connections)
                for room_id, connections in self.rooms.items()
            }
        }
    
    async def cleanup_inactive_connections(self, timeout_minutes: int = 30):
        """비활성 연결 정리"""
        cutoff_time = datetime.utcnow().timestamp() - (timeout_minutes * 60)
        inactive_connections = []
        
        for connection_id, connection in self.connections.items():
            if connection.last_activity.timestamp() < cutoff_time:
                inactive_connections.append(connection_id)
        
        cleanup_count = 0
        for connection_id in inactive_connections:
            try:
                await self.disconnect(connection_id)
                cleanup_count += 1
            except Exception as e:
                logger.error(f"Error cleaning up connection {connection_id}: {str(e)}")
        
        if cleanup_count > 0:
            logger.info(f"Cleaned up {cleanup_count} inactive connections")
        
        return cleanup_count 