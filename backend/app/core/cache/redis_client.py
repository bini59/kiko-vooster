"""
Redis 클라이언트 연결 관리

캐싱을 위한 Redis 연결 설정 및 관리
"""

import redis.asyncio as redis
from typing import Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# 글로벌 Redis 클라이언트 인스턴스
_redis_client: Optional[redis.Redis] = None


async def init_redis() -> redis.Redis:
    """Redis 연결 초기화"""
    global _redis_client
    
    try:
        # Redis URL 파싱 및 연결
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50
        )
        
        # 연결 테스트
        await _redis_client.ping()
        logger.info("✅ Redis 연결 성공")
        
        return _redis_client
        
    except Exception as e:
        logger.error(f"❌ Redis 연결 실패: {str(e)}")
        # Redis 없이도 동작하도록 (캐싱 비활성화)
        _redis_client = None
        raise e


async def close_redis():
    """Redis 연결 종료"""
    global _redis_client
    
    if _redis_client:
        await _redis_client.close()
        logger.info("Redis 연결 종료")
        _redis_client = None


def get_redis_client() -> Optional[redis.Redis]:
    """Redis 클라이언트 인스턴스 반환"""
    return _redis_client


async def is_redis_available() -> bool:
    """Redis 사용 가능 여부 확인"""
    if not _redis_client:
        return False
    
    try:
        await _redis_client.ping()
        return True
    except:
        return False


class RedisConnectionManager:
    """Redis 연결 컨텍스트 매니저"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
    
    async def __aenter__(self):
        if not _redis_client:
            await init_redis()
        self.client = _redis_client
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 연결은 전역적으로 관리되므로 여기서는 닫지 않음
        pass 