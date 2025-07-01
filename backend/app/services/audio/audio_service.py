"""
오디오 서비스

오디오 재생 관련 비즈니스 로직
"""

from uuid import UUID, uuid4
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import asyncio
import tempfile
import os

from app.core.cache.cache_manager import CacheManager
from app.core.storage.storage_manager import StorageManager
from app.core.database import get_database
from app.models.audio import (
    StreamResponse, PrepareResponse, PlayResponse,
    ProgressResponse, SeekResponse, BookmarkResponse,
    QualityType, StatusType
)

logger = logging.getLogger(__name__)


class AudioService:
    """오디오 서비스 - 핵심 비즈니스 로직"""
    
    def __init__(
        self,
        storage_manager: StorageManager,
        cache_manager: CacheManager
    ):
        self.storage = storage_manager
        self.cache = cache_manager
    
    async def get_stream_info(
        self,
        script_id: UUID,
        quality: QualityType = "medium",
        user_id: Optional[UUID] = None
    ) -> StreamResponse:
        """스트림 정보 조회"""
        try:
            # 캐시 확인
            cached = await self.cache.get_stream_info(str(script_id), quality)
            if cached:
                logger.info(f"Cache hit for stream {script_id}:{quality}")
                return StreamResponse(**cached)
            
            # DB에서 스크립트 정보 조회
            db = await get_database()
            script_result = await db.get_by_id("scripts", script_id)
            
            if not script_result:
                raise ValueError(f"Script {script_id} not found")
            
            script = script_result
            
            # 권한 확인
            if not script['is_public'] and str(script['user_id']) != str(user_id):
                raise PermissionError(f"Access denied to script {script_id}")
            
            # HLS manifest URL 생성
            stream_url = await self.storage.get_manifest_url(str(script_id))
            
            # 스트림 정보 구성
            stream_info = {
                'stream_url': stream_url,
                'duration': float(script.get('duration', 0)),
                'bitrate': self._get_bitrate_for_quality(quality),
                'format': 'hls',
                'cached': False,
                'expires_at': datetime.utcnow().isoformat()
            }
            
            # 캐시 저장
            await self.cache.set_stream_info(str(script_id), quality, stream_info)
            
            return StreamResponse(**stream_info)
            
        except Exception as e:
            logger.error(f"Error getting stream info: {str(e)}")
            raise
    
    async def prepare_audio(
        self,
        script_id: UUID,
        priority: str = "normal"
    ) -> PrepareResponse:
        """오디오 사전 처리"""
        try:
            # 이미 처리중인지 확인
            existing = await self.cache.get_prepare_status(str(script_id))
            if existing:
                return PrepareResponse(**existing)
            
            # 처리 시작
            status = {
                'status': 'preparing',
                'progress': 0,
                'estimated_time': 30
            }
            await self.cache.set_prepare_status(str(script_id), status)
            
            # 비동기 처리 시작 (실제 구현에서는 Celery 등 사용)
            asyncio.create_task(
                self._process_audio_background(script_id, priority)
            )
            
            return PrepareResponse(**status)
            
        except Exception as e:
            logger.error(f"Error preparing audio: {str(e)}")
            raise
    
    async def create_play_session(
        self,
        script_id: UUID,
        user_id: UUID,
        position: float = 0,
        sentence_id: Optional[UUID] = None
    ) -> PlayResponse:
        """재생 세션 생성"""
        try:
            # 스트림 정보 가져오기
            stream_info = await self.get_stream_info(script_id, user_id=user_id)
            
            # 세션 생성
            session_id = uuid4()
            session_data = {
                'id': str(session_id),
                'user_id': str(user_id),
                'script_id': str(script_id),
                'started_at': datetime.utcnow().isoformat(),
                'last_position': position,
                'total_duration': stream_info.duration,
                'playback_rate': 1.0,
                'is_active': True
            }
            
            # 세션 캐시 저장
            await self.cache.set_session(str(session_id), session_data)
            
            # DB에 세션 기록
            db = await get_database()
            await db.create(
                "audio_sessions",
                {
                    'id': session_id,
                    'user_id': user_id,
                    'script_id': script_id,
                    'started_at': datetime.utcnow(),
                    'last_position': position
                }
            )
            
            return PlayResponse(
                session_id=session_id,
                stream_url=stream_info.stream_url,
                start_position=position
            )
            
        except Exception as e:
            logger.error(f"Error creating play session: {str(e)}")
            raise
    
    async def update_progress(
        self,
        session_id: UUID,
        position: float,
        sentence_id: Optional[UUID] = None,
        playback_rate: float = 1.0
    ) -> ProgressResponse:
        """재생 진행률 업데이트"""
        try:
            # 세션 조회
            session_data = await self.cache.get_session(str(session_id))
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
            
            # 진행률 계산
            total_duration = session_data.get('total_duration', 1)
            progress_percent = (position / total_duration * 100) if total_duration > 0 else 0
            
            # 세션 업데이트
            session_data['last_position'] = position
            session_data['playback_rate'] = playback_rate
            session_data['updated_at'] = datetime.utcnow().isoformat()
            
            await self.cache.set_session(str(session_id), session_data)
            
            # DB 업데이트 (비동기)
            asyncio.create_task(
                self._update_progress_db(session_id, position, sentence_id)
            )
            
            # 학습 진행률 업데이트
            if sentence_id:
                asyncio.create_task(
                    self._update_learning_progress(
                        session_data['user_id'],
                        session_data['script_id'],
                        sentence_id,
                        position
                    )
                )
            
            return ProgressResponse(
                saved=True,
                total_listened=position,
                progress_percent=progress_percent
            )
            
        except Exception as e:
            logger.error(f"Error updating progress: {str(e)}")
            raise
    
    async def seek_position(
        self,
        session_id: UUID,
        position: float,
        sentence_id: Optional[UUID] = None
    ) -> SeekResponse:
        """재생 위치 이동"""
        try:
            # 세션 확인
            session_data = await self.cache.get_session(str(session_id))
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
            
            # 위치 업데이트
            await self.update_progress(session_id, position, sentence_id)
            
            # 해당 위치의 세그먼트 URL 생성
            segment_num = int(position // 10)  # 10초 단위 세그먼트 가정
            segment_url = await self.storage.get_segment_url(
                session_data['script_id'],
                segment_num
            )
            
            return SeekResponse(
                success=True,
                new_position=position,
                segment_url=segment_url
            )
            
        except Exception as e:
            logger.error(f"Error seeking position: {str(e)}")
            raise
    
    async def create_bookmark(
        self,
        user_id: UUID,
        script_id: UUID,
        position: float,
        note: Optional[str] = None
    ) -> BookmarkResponse:
        """북마크 생성"""
        try:
            bookmark_id = uuid4()
            
            # DB에 북마크 저장
            db = await get_database()
            await db.create(
                "audio_bookmarks",
                {
                    'id': bookmark_id,
                    'user_id': user_id,
                    'script_id': script_id,
                    'position': position,
                    'note': note,
                    'created_at': datetime.utcnow()
                }
            )
            
            return BookmarkResponse(
                id=bookmark_id,
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error creating bookmark: {str(e)}")
            raise
    
    async def end_session(self, session_id: UUID):
        """세션 종료"""
        try:
            # 세션 캐시 삭제
            await self.cache.delete_session(str(session_id))
            
            # DB 업데이트
            db = await get_database()
            await db.update(
                "audio_sessions",
                session_id,
                {
                    'is_active': False,
                    'ended_at': datetime.utcnow()
                }
            )
            
        except Exception as e:
            logger.error(f"Error ending session: {str(e)}")
            raise
    
    # Private methods
    
    def _get_bitrate_for_quality(self, quality: str) -> int:
        """품질별 비트레이트 반환"""
        bitrates = {
            'low': 64000,
            'medium': 128000,
            'high': 256000
        }
        return bitrates.get(quality, 128000)
    
    async def _process_audio_background(self, script_id: UUID, priority: str):
        """백그라운드 오디오 처리 (HLS 변환)"""
        # 실제 구현에서는 FFmpeg를 사용한 HLS 변환 로직
        # 여기서는 시뮬레이션만
        try:
            for progress in [25, 50, 75, 100]:
                await asyncio.sleep(2)  # 시뮬레이션
                
                status = {
                    'status': 'preparing' if progress < 100 else 'ready',
                    'progress': progress,
                    'estimated_time': max(0, 30 - (progress // 3))
                }
                await self.cache.set_prepare_status(str(script_id), status)
            
        except Exception as e:
            status = {
                'status': 'failed',
                'progress': 0,
                'error': str(e)
            }
            await self.cache.set_prepare_status(str(script_id), status)
    
    async def _update_progress_db(
        self,
        session_id: UUID,
        position: float,
        sentence_id: Optional[UUID] = None
    ):
        """DB에 진행률 업데이트"""
        try:
            db = await get_database()
            await db.update(
                "audio_sessions",
                session_id,
                {
                    'last_position': position,
                    'last_sentence_id': sentence_id
                }
            )
        except Exception as e:
            logger.error(f"Error updating progress in DB: {str(e)}")
    
    async def _update_learning_progress(
        self,
        user_id: str,
        script_id: str,
        sentence_id: UUID,
        position: float
    ):
        """학습 진행률 업데이트"""
        try:
            db = await get_database()
            
            # user_scripts_progress 테이블 업데이트
            progress_data = {
                'user_id': UUID(user_id),
                'script_id': UUID(script_id),
                'last_position': position,
                'last_sentence_id': sentence_id,
                'updated_at': datetime.utcnow()
            }
            
            # Upsert 로직
            existing = await db.client.from_("user_scripts_progress")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("script_id", script_id)\
                .execute()
            
            if existing.data:
                await db.update(
                    "user_scripts_progress",
                    existing.data[0]['id'],
                    progress_data
                )
            else:
                progress_data['id'] = uuid4()
                await db.create("user_scripts_progress", progress_data)
                
        except Exception as e:
            logger.error(f"Error updating learning progress: {str(e)}")


# 의존성 주입을 위한 싱글톤
_audio_service: Optional[AudioService] = None


def get_audio_service() -> AudioService:
    """오디오 서비스 인스턴스 반환"""
    if not _audio_service:
        raise RuntimeError("Audio service not initialized")
    return _audio_service


def set_audio_service(audio_service: AudioService):
    """오디오 서비스 인스턴스 설정"""
    global _audio_service
    _audio_service = audio_service 