"""
스크립트-오디오 싱크 매핑 서비스

문장별 타임코드 매핑 관리, 실시간 동기화, 편집 내역 추적
"""

from uuid import UUID, uuid4
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import asyncio

from app.core.cache.cache_manager import CacheManager
from app.core.database import get_database
from app.models.sync import (
    SentenceMappingCreate, SentenceMappingUpdate, SentenceMappingResponse,
    MappingEditResponse, SyncSessionCreate, SyncSessionResponse,
    MappingType, EditType
)

logger = logging.getLogger(__name__)


class SyncMappingService:
    """스크립트-오디오 싱크 매핑 서비스"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
    
    # =============================================================================
    # 문장 매핑 CRUD 기능
    # =============================================================================
    
    async def create_sentence_mapping(
        self,
        sentence_id: UUID,
        start_time: float,
        end_time: float,
        user_id: UUID,
        mapping_type: str = "manual",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """새 문장 매핑 생성"""
        try:
            db = await get_database()
            
            # 기존 활성 매핑 비활성화
            await self._deactivate_existing_mapping(sentence_id)
            
            # 신뢰도 계산
            confidence_score = self._calculate_confidence(mapping_type, end_time - start_time)
            
            # 새 매핑 생성
            mapping_id = uuid4()
            mapping_dict = {
                'id': mapping_id,
                'sentence_id': sentence_id,
                'start_time': start_time,
                'end_time': end_time,
                'confidence_score': confidence_score,
                'mapping_type': mapping_type,
                'created_by': user_id,
                'is_active': True,
                'metadata': metadata or {},
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            result = await db.create('sentence_mappings', mapping_dict)
            
            # 편집 내역 기록
            await self._record_mapping_edit(
                sentence_id=sentence_id,
                user_id=user_id,
                new_mapping_id=mapping_id,
                new_start_time=start_time,
                new_end_time=end_time,
                edit_type="manual",
                edit_reason="새 매핑 생성"
            )
            
            # 캐시 업데이트
            await self._update_mapping_cache(sentence_id, mapping_dict)
            
            # WebSocket으로 실시간 브로드캐스트
            asyncio.create_task(
                self._broadcast_mapping_update(sentence_id, mapping_dict)
            )
            
            return mapping_dict
            
        except Exception as e:
            logger.error(f"Error creating sentence mapping: {str(e)}")
            raise
    
    async def get_sentence_mapping(
        self,
        sentence_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """문장 매핑 조회"""
        try:
            # 캐시 먼저 확인
            cached_mapping = await self.cache.get(f"mapping:sentence:{sentence_id}")
            if cached_mapping:
                return cached_mapping
            
            # DB에서 조회
            db = await get_database()
            result = await db.client.from_('sentence_mappings')\
                .select('*')\
                .eq('sentence_id', str(sentence_id))\
                .eq('is_active', True)\
                .single()\
                .execute()
            
            if not result.data:
                return None
            
            mapping_data = result.data
            
            # 캐시에 저장
            await self.cache.set(
                f"mapping:sentence:{sentence_id}",
                mapping_data,
                ttl=300  # 5분
            )
            
            return mapping_data
            
        except Exception as e:
            logger.error(f"Error getting sentence mapping: {str(e)}")
            return None
    
    async def update_sentence_mapping(
        self,
        sentence_id: UUID,
        start_time: float,
        end_time: float,
        user_id: UUID,
        mapping_type: str = "manual",
        edit_reason: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """문장 매핑 업데이트"""
        try:
            db = await get_database()
            
            # 기존 매핑 조회
            existing_mapping = await self.get_sentence_mapping(sentence_id)
            if not existing_mapping:
                raise ValueError(f"Mapping not found for sentence {sentence_id}")
            
            # 기존 매핑 비활성화
            await self._deactivate_existing_mapping(sentence_id)
            
            # 새 매핑 생성 (버전 관리를 위해)
            new_mapping_id = uuid4()
            confidence_score = self._calculate_confidence(mapping_type, end_time - start_time)
            
            new_mapping_dict = {
                'id': new_mapping_id,
                'sentence_id': sentence_id,
                'start_time': start_time,
                'end_time': end_time,
                'confidence_score': confidence_score,
                'mapping_type': mapping_type,
                'created_by': user_id,
                'is_active': True,
                'metadata': metadata or existing_mapping.get('metadata', {}),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            await db.create('sentence_mappings', new_mapping_dict)
            
            # 편집 내역 기록
            await self._record_mapping_edit(
                sentence_id=sentence_id,
                user_id=user_id,
                old_mapping_id=UUID(existing_mapping['id']),
                new_mapping_id=new_mapping_id,
                old_start_time=existing_mapping['start_time'],
                old_end_time=existing_mapping['end_time'],
                new_start_time=start_time,
                new_end_time=end_time,
                edit_type="manual",
                edit_reason=edit_reason or "매핑 수정"
            )
            
            # 캐시 업데이트
            await self._update_mapping_cache(sentence_id, new_mapping_dict)
            
            # 실시간 브로드캐스트
            asyncio.create_task(
                self._broadcast_mapping_update(sentence_id, new_mapping_dict)
            )
            
            return new_mapping_dict
            
        except Exception as e:
            logger.error(f"Error updating sentence mapping: {str(e)}")
            raise
    
    async def delete_sentence_mapping(
        self,
        sentence_id: UUID,
        user_id: UUID
    ) -> bool:
        """문장 매핑 삭제 (비활성화)"""
        try:
            # 기존 매핑 조회
            existing_mapping = await self.get_sentence_mapping(sentence_id)
            if not existing_mapping:
                return False
            
            # 매핑 비활성화
            await self._deactivate_existing_mapping(sentence_id)
            
            # 편집 내역 기록
            await self._record_mapping_edit(
                sentence_id=sentence_id,
                user_id=user_id,
                old_mapping_id=UUID(existing_mapping['id']),
                old_start_time=existing_mapping['start_time'],
                old_end_time=existing_mapping['end_time'],
                edit_type="manual",
                edit_reason="매핑 삭제"
            )
            
            # 캐시 삭제
            await self.cache.delete(f"mapping:sentence:{sentence_id}")
            
            # 실시간 브로드캐스트
            asyncio.create_task(
                self._broadcast_mapping_deletion(sentence_id)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting sentence mapping: {str(e)}")
            raise
    
    async def get_script_mappings(
        self,
        script_id: UUID,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """스크립트의 모든 문장 매핑 조회"""
        try:
            db = await get_database()
            
            query = db.client.from_('sentence_mappings')\
                .select('*, sentences!inner(*)')\
                .eq('sentences.script_id', str(script_id))\
                .order('sentences.order_index')
            
            if not include_inactive:
                query = query.eq('is_active', True)
            
            result = await query.execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting script mappings: {str(e)}")
            return []
    
    # =============================================================================
    # 편집 내역 관리
    # =============================================================================
    
    async def get_mapping_edit_history(
        self,
        sentence_id: UUID,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """매핑 편집 내역 조회"""
        try:
            db = await get_database()
            
            result = await db.client.from_('mapping_edits')\
                .select('*, users(id, email, full_name)')\
                .eq('sentence_id', str(sentence_id))\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting mapping edit history: {str(e)}")
            return []
    
    # =============================================================================
    # 실시간 동기화 세션 관리
    # =============================================================================
    
    async def create_sync_session(
        self,
        script_id: UUID,
        connection_id: str,
        user_id: Optional[UUID] = None,
        current_position: float = 0.0,
        is_playing: bool = False,
        session_token: Optional[str] = None,
        client_info: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """동기화 세션 생성"""
        try:
            db = await get_database()
            
            # 룸 ID 생성 (스크립트별)
            room_id = f"sync_{str(script_id).replace('-', '')}"
            
            # 기존 세션 비활성화 (같은 연결 ID)
            await self._deactivate_user_sessions(connection_id, script_id)
            
            # 새 세션 생성
            session_id = uuid4()
            session_dict = {
                'id': session_id,
                'script_id': script_id,
                'user_id': user_id,
                'connection_id': connection_id,
                'room_id': room_id,
                'current_position': current_position,
                'is_playing': is_playing,
                'session_token': session_token,
                'client_info': client_info or {},
                'is_active': True,
                'joined_at': datetime.utcnow(),
                'last_activity': datetime.utcnow()
            }
            
            await db.create('sync_sessions', session_dict)
            
            # 세션 캐시 저장
            await self.cache.set(
                f"sync:session:{session_id}",
                session_dict,
                ttl=3600  # 1시간
            )
            
            # 실시간 브로드캐스트 (룸 참가 알림)
            asyncio.create_task(
                self._broadcast_session_joined(room_id, session_dict)
            )
            
            return session_dict
            
        except Exception as e:
            logger.error(f"Error creating sync session: {str(e)}")
            raise
    
    async def update_sync_position(
        self,
        session_id: UUID,
        position: float,
        is_playing: Optional[bool] = None,
        sentence_id: Optional[UUID] = None
    ) -> bool:
        """동기화 세션 위치 업데이트"""
        try:
            db = await get_database()
            
            # 세션 조회
            session_data = await self.cache.get(f"sync:session:{session_id}")
            if not session_data:
                result = await db.get_by_id('sync_sessions', session_id)
                if not result:
                    return False
                session_data = result
            
            # 위치 업데이트
            update_data = {
                'current_position': position,
                'last_activity': datetime.utcnow()
            }
            
            if is_playing is not None:
                update_data['is_playing'] = is_playing
            if sentence_id is not None:
                update_data['current_sentence_id'] = sentence_id
            
            await db.update('sync_sessions', session_id, update_data)
            
            # 캐시 업데이트
            session_data.update(update_data)
            await self.cache.set(
                f"sync:session:{session_id}",
                session_data,
                ttl=3600
            )
            
            # 실시간 브로드캐스트
            asyncio.create_task(
                self._broadcast_position_update(
                    session_data['room_id'], 
                    session_id, 
                    position, 
                    is_playing, 
                    sentence_id
                )
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating sync position: {str(e)}")
            return False
    
    async def get_room_participants(
        self,
        script_id: UUID
    ) -> List[Dict[str, Any]]:
        """룸 참가자 목록 조회"""
        try:
            db = await get_database()
            
            result = await db.client.from_('sync_sessions')\
                .select('user_id, connection_id, current_position, is_playing, joined_at, users(id, email, full_name)')\
                .eq('script_id', str(script_id))\
                .eq('is_active', True)\
                .order('joined_at')\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting room participants: {str(e)}")
            return []
    
    # =============================================================================
    # AI 자동 정렬 (향후 구현)
    # =============================================================================
    
    async def auto_align_script(
        self,
        script_id: UUID,
        audio_duration: float,
        user_id: UUID
    ) -> List[Dict[str, Any]]:
        """AI 기반 자동 스크립트 정렬"""
        # TODO: AI 모델 연동 구현
        # 현재는 기본적인 균등 분할로 시뮬레이션
        try:
            db = await get_database()
            
            # 스크립트의 문장들 조회
            result = await db.client.from_('sentences')\
                .select('*')\
                .eq('script_id', str(script_id))\
                .order('order_index')\
                .execute()
            
            sentences = result.data if result.data else []
            if not sentences:
                return []
            
            # 균등 분할 (임시 구현)
            sentence_count = len(sentences)
            time_per_sentence = audio_duration / sentence_count
            
            mappings = []
            for i, sentence in enumerate(sentences):
                start_time = i * time_per_sentence
                end_time = (i + 1) * time_per_sentence
                
                mapping = await self.create_sentence_mapping(
                    sentence_id=UUID(sentence['id']),
                    start_time=start_time,
                    end_time=end_time,
                    user_id=user_id,
                    mapping_type="ai_generated",
                    metadata={'auto_aligned': True, 'confidence': 0.7}
                )
                
                mappings.append(mapping)
            
            return mappings
            
        except Exception as e:
            logger.error(f"Error auto-aligning script: {str(e)}")
            raise
    
    # =============================================================================
    # Private 헬퍼 메서드
    # =============================================================================
    
    async def _deactivate_existing_mapping(self, sentence_id: UUID):
        """기존 활성 매핑 비활성화"""
        db = await get_database()
        await db.client.from_('sentence_mappings')\
            .update({'is_active': False})\
            .eq('sentence_id', str(sentence_id))\
            .eq('is_active', True)\
            .execute()
    
    async def _record_mapping_edit(
        self,
        sentence_id: UUID,
        user_id: UUID,
        edit_type: str,
        new_start_time: float,
        new_end_time: float,
        old_mapping_id: Optional[UUID] = None,
        new_mapping_id: Optional[UUID] = None,
        old_start_time: Optional[float] = None,
        old_end_time: Optional[float] = None,
        edit_reason: Optional[str] = None
    ):
        """편집 내역 기록"""
        try:
            db = await get_database()
            
            edit_dict = {
                'id': uuid4(),
                'sentence_id': sentence_id,
                'user_id': user_id,
                'old_mapping_id': old_mapping_id,
                'new_mapping_id': new_mapping_id,
                'old_start_time': old_start_time,
                'old_end_time': old_end_time,
                'new_start_time': new_start_time,
                'new_end_time': new_end_time,
                'edit_reason': edit_reason,
                'edit_type': edit_type,
                'client_info': {},
                'created_at': datetime.utcnow()
            }
            
            await db.create('mapping_edits', edit_dict)
            
        except Exception as e:
            logger.error(f"Error recording mapping edit: {str(e)}")
    
    def _calculate_confidence(
        self,
        mapping_type: str,
        duration_seconds: float
    ) -> float:
        """매핑 신뢰도 계산"""
        if mapping_type == "manual":
            return 1.0
        elif mapping_type == "ai_generated":
            # 지속시간 기반 신뢰도 (짧은 문장은 낮은 신뢰도)
            base_confidence = 0.8
            if duration_seconds < 1.0:
                return 0.3
            elif duration_seconds < 3.0:
                return 0.6
            else:
                return base_confidence
        else:
            return 0.5
    
    async def _update_mapping_cache(self, sentence_id: UUID, mapping_data: Dict):
        """매핑 캐시 업데이트"""
        await self.cache.set(
            f"mapping:sentence:{sentence_id}",
            mapping_data,
            ttl=300
        )
    
    async def _deactivate_user_sessions(
        self, 
        connection_id: str, 
        script_id: UUID
    ):
        """사용자의 기존 세션들 비활성화"""
        db = await get_database()
        await db.client.from_('sync_sessions')\
            .update({'is_active': False, 'left_at': datetime.utcnow()})\
            .eq('connection_id', connection_id)\
            .eq('script_id', str(script_id))\
            .eq('is_active', True)\
            .execute()
    
    # =============================================================================
    # WebSocket 브로드캐스트 메서드
    # =============================================================================
    
    async def _broadcast_mapping_update(
        self, 
        sentence_id: UUID, 
        mapping_data: Dict
    ):
        """매핑 업데이트 브로드캐스트"""
        try:
            # WebSocket 매니저 import (지연 import로 순환 의존성 방지)
            from app.websocket.sync_websocket import get_sync_websocket_manager
            
            # 문장이 속한 스크립트 ID 조회
            db = await get_database()
            result = await db.client.from_('sentences')\
                .select('script_id')\
                .eq('id', str(sentence_id))\
                .single()\
                .execute()
            
            if result.data:
                script_id = result.data['script_id']
                sync_manager = get_sync_websocket_manager()
                await sync_manager.broadcast_mapping_update(
                    script_id=script_id,
                    sentence_id=sentence_id,
                    mapping_data=mapping_data
                )
                logger.debug(f"Broadcasted mapping update for sentence {sentence_id}")
            else:
                logger.warning(f"Script not found for sentence {sentence_id}")
                
        except Exception as e:
            logger.error(f"Error broadcasting mapping update: {str(e)}")
    
    async def _broadcast_mapping_deletion(self, sentence_id: UUID):
        """매핑 삭제 브로드캐스트"""
        try:
            from app.websocket.sync_websocket import get_sync_websocket_manager
            
            # 문장이 속한 스크립트 ID 조회
            db = await get_database()
            result = await db.client.from_('sentences')\
                .select('script_id')\
                .eq('id', str(sentence_id))\
                .single()\
                .execute()
            
            if result.data:
                script_id = result.data['script_id']
                sync_manager = get_sync_websocket_manager()
                await sync_manager.broadcast_mapping_deletion(
                    script_id=script_id,
                    sentence_id=sentence_id
                )
                logger.debug(f"Broadcasted mapping deletion for sentence {sentence_id}")
            else:
                logger.warning(f"Script not found for sentence {sentence_id}")
                
        except Exception as e:
            logger.error(f"Error broadcasting mapping deletion: {str(e)}")
    
    async def _broadcast_session_joined(self, room_id: str, session_data: Dict):
        """세션 참가 브로드캐스트"""
        try:
            from app.websocket.sync_websocket import get_sync_websocket_manager
            
            sync_manager = get_sync_websocket_manager()
            # 세션 참가는 connection_manager에서 자동으로 처리됨
            logger.debug(f"Session joined to room {room_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting session joined: {str(e)}")
    
    async def _broadcast_position_update(
        self,
        room_id: str,
        session_id: UUID,
        position: float,
        is_playing: Optional[bool],
        sentence_id: Optional[UUID]
    ):
        """위치 업데이트 브로드캐스트"""
        try:
            from app.websocket.sync_websocket import get_sync_websocket_manager
            
            # 위치 업데이트는 클라이언트에서 직접 WebSocket으로 전송됨
            # 서비스 레이어에서는 별도 브로드캐스트가 필요하지 않음
            logger.debug(f"Position update handled for room {room_id}: {position}")
            
        except Exception as e:
            logger.error(f"Error handling position update: {str(e)}")


# 의존성 주입을 위한 싱글톤
_sync_mapping_service: Optional[SyncMappingService] = None


def get_sync_mapping_service() -> SyncMappingService:
    """동기화 매핑 서비스 인스턴스 반환"""
    if not _sync_mapping_service:
        raise RuntimeError("Sync mapping service not initialized")
    return _sync_mapping_service


def set_sync_mapping_service(sync_mapping_service: SyncMappingService):
    """동기화 매핑 서비스 인스턴스 설정"""
    global _sync_mapping_service
    _sync_mapping_service = sync_mapping_service 