"""
캐시 매니저

캐시 백엔드 추상화 및 도메인별 캐시 관리
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """캐시 백엔드 추상 클래스"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """키로 값 조회"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """키-값 저장"""
        pass
    
    @abstractmethod
    async def delete(self, key: str):
        """키 삭제"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        pass
    
    @abstractmethod
    async def expire(self, key: str, ttl: int):
        """TTL 설정"""
        pass


class RedisCacheBackend(CacheBackend):
    """Redis 캐시 백엔드 구현"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """Redis에서 값 조회"""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Redis에 값 저장"""
        try:
            serialized = json.dumps(value, default=str)
            if ttl:
                await self.redis.setex(key, ttl, serialized)
            else:
                await self.redis.set(key, serialized)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
    
    async def delete(self, key: str):
        """Redis에서 키 삭제"""
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
    
    async def exists(self, key: str) -> bool:
        """Redis에서 키 존재 여부 확인"""
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int):
        """Redis 키 TTL 설정"""
        try:
            await self.redis.expire(key, ttl)
        except Exception as e:
            logger.error(f"Redis expire error for key {key}: {e}")


class MemoryCacheBackend(CacheBackend):
    """메모리 캐시 백엔드 (Redis 사용 불가 시 폴백)"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._ttl: Dict[str, float] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """메모리에서 값 조회"""
        # TTL 확인
        if key in self._ttl:
            import time
            if time.time() > self._ttl[key]:
                del self._cache[key]
                del self._ttl[key]
                return None
        
        return self._cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """메모리에 값 저장"""
        self._cache[key] = value
        if ttl:
            import time
            self._ttl[key] = time.time() + ttl
    
    async def delete(self, key: str):
        """메모리에서 키 삭제"""
        self._cache.pop(key, None)
        self._ttl.pop(key, None)
    
    async def exists(self, key: str) -> bool:
        """메모리에서 키 존재 여부 확인"""
        return key in self._cache
    
    async def expire(self, key: str, ttl: int):
        """메모리 키 TTL 설정"""
        if key in self._cache:
            import time
            self._ttl[key] = time.time() + ttl


class CacheManager:
    """캐시 관리자 - 도메인별 캐시 관리"""
    
    # 기본 TTL 설정 (초)
    DEFAULT_TTL = 3600  # 1시간
    STREAM_INFO_TTL = 86400  # 24시간
    SESSION_TTL = 7200  # 2시간
    PREPARE_STATUS_TTL = 300  # 5분
    
    def __init__(self, backend: CacheBackend):
        self.backend = backend
    
    # 스트림 정보 관련
    async def get_stream_info(self, script_id: str, quality: str) -> Optional[dict]:
        """스트림 정보 캐시 조회"""
        key = f"audio:stream:{script_id}:{quality}"
        return await self.backend.get(key)
    
    async def set_stream_info(self, script_id: str, quality: str, info: dict):
        """스트림 정보 캐시 저장"""
        key = f"audio:stream:{script_id}:{quality}"
        await self.backend.set(key, info, ttl=self.STREAM_INFO_TTL)
    
    # 세션 관련
    async def get_session(self, session_id: str) -> Optional[dict]:
        """세션 정보 조회"""
        key = f"audio:session:{session_id}"
        return await self.backend.get(key)
    
    async def set_session(self, session_id: str, data: dict):
        """세션 정보 저장"""
        key = f"audio:session:{session_id}"
        await self.backend.set(key, data, ttl=self.SESSION_TTL)
    
    async def update_session_position(self, session_id: str, position: float):
        """세션 재생 위치 업데이트"""
        session = await self.get_session(session_id)
        if session:
            session['last_position'] = position
            session['updated_at'] = str(datetime.utcnow())
            await self.set_session(session_id, session)
    
    async def delete_session(self, session_id: str):
        """세션 삭제"""
        key = f"audio:session:{session_id}"
        await self.backend.delete(key)
    
    # 준비 상태 관련
    async def get_prepare_status(self, script_id: str) -> Optional[dict]:
        """오디오 준비 상태 조회"""
        key = f"audio:prepare:{script_id}"
        return await self.backend.get(key)
    
    async def set_prepare_status(self, script_id: str, status: dict):
        """오디오 준비 상태 저장"""
        key = f"audio:prepare:{script_id}"
        await self.backend.set(key, status, ttl=self.PREPARE_STATUS_TTL)
    
    # HLS 매니페스트 관련
    async def get_manifest(self, script_id: str) -> Optional[str]:
        """HLS 매니페스트 캐시 조회"""
        key = f"audio:manifest:{script_id}"
        data = await self.backend.get(key)
        return data.get('content') if data else None
    
    async def set_manifest(self, script_id: str, content: str):
        """HLS 매니페스트 캐시 저장"""
        key = f"audio:manifest:{script_id}"
        await self.backend.set(key, {'content': content}, ttl=self.STREAM_INFO_TTL)
    
    # 세그먼트 URL 관련
    async def get_segment_url(self, script_id: str, segment_num: int) -> Optional[str]:
        """세그먼트 URL 캐시 조회"""
        key = f"audio:segment:{script_id}:{segment_num}"
        data = await self.backend.get(key)
        return data.get('url') if data else None
    
    async def set_segment_url(self, script_id: str, segment_num: int, url: str):
        """세그먼트 URL 캐시 저장"""
        key = f"audio:segment:{script_id}:{segment_num}"
        await self.backend.set(key, {'url': url}, ttl=self.STREAM_INFO_TTL)
    
    # 유틸리티 메서드
    async def clear_script_cache(self, script_id: str):
        """스크립트 관련 모든 캐시 삭제"""
        patterns = [
            f"audio:stream:{script_id}:*",
            f"audio:manifest:{script_id}",
            f"audio:segment:{script_id}:*",
            f"audio:prepare:{script_id}"
        ]
        # Redis SCAN을 사용한 패턴 매칭 삭제 (구현 필요)
        # 여기서는 간단히 개별 삭제만 구현
        pass


# 의존성 주입을 위한 전역 인스턴스
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> Optional[CacheManager]:
    """캐시 매니저 인스턴스 반환"""
    return _cache_manager


def set_cache_manager(cache_manager: CacheManager):
    """캐시 매니저 인스턴스 설정"""
    global _cache_manager
    _cache_manager = cache_manager 