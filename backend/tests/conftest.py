"""
pytest 설정 파일

테스트 환경 설정 및 공통 fixture 정의
"""

import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.config import settings
from app.core.database import get_database


# 테스트 데이터베이스 URL (환경 변수에서 읽거나 기본값 사용)
TEST_DATABASE_URL = settings.DATABASE_URL + "_test"


@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 fixture"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """비동기 HTTP 클라이언트 fixture"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
async def authenticated_client(async_client: AsyncClient) -> AsyncClient:
    """인증된 클라이언트 fixture"""
    # 테스트 사용자 생성 및 로그인
    test_user = {
        "email": "test@example.com",
        "password": "testpass123",
        "username": "testuser"
    }
    
    # 사용자 등록
    await async_client.post("/api/v1/auth/register", json=test_user)
    
    # 로그인
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"]
        }
    )
    
    token = response.json().get("access_token")
    async_client.headers["Authorization"] = f"Bearer {token}"
    
    return async_client


@pytest.fixture(scope="function")
async def test_db():
    """테스트 데이터베이스 fixture"""
    # 테스트 DB 생성 및 마이그레이션
    # 실제 구현에서는 테스트 전용 DB 설정 필요
    pass


@pytest.fixture(scope="function")
async def sample_script_data():
    """샘플 스크립트 데이터"""
    return {
        "title": "테스트 라디오 방송",
        "description": "통합 테스트용 샘플 스크립트",
        "audio_url": "https://example.com/test.mp3",
        "duration": 3600,
        "language": "ja",
        "level": "intermediate",
        "is_public": True
    }


@pytest.fixture(scope="function")
async def sample_audio_file():
    """샘플 오디오 파일"""
    # 테스트용 임시 오디오 파일 생성
    import tempfile
    import wave
    import struct
    
    # 1초짜리 사인파 오디오 생성
    sample_rate = 44100
    duration = 1
    frequency = 440
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        with wave.open(temp_file.name, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            
            # 사인파 생성
            for i in range(sample_rate * duration):
                value = int(32767 * 0.5 * 
                          (1.0 + struct.unpack('f', 
                          struct.pack('f', i * frequency / sample_rate))[0]))
                data = struct.pack('<h', value)
                wav_file.writeframesraw(data)
        
        yield temp_file.name
        
        # 정리
        import os
        os.unlink(temp_file.name)


# 테스트 마커 정의
def pytest_configure(config):
    """pytest 설정"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


# 테스트 실행 전 설정
@pytest.fixture(scope="session", autouse=True)
async def setup_test_environment():
    """테스트 환경 설정"""
    # 테스트 모드 설정
    settings.TESTING = True
    
    # 테스트 데이터베이스 초기화
    # await init_test_database()
    
    yield
    
    # 정리
    # await cleanup_test_database()


# 성능 측정 헬퍼
class PerformanceCounter:
    """성능 측정 헬퍼 클래스"""
    
    def __init__(self):
        self.measurements = []
    
    def measure(self, name: str):
        """컨텍스트 매니저로 시간 측정"""
        import time
        
        class Timer:
            def __enter__(timer_self):
                timer_self.start = time.time()
                return timer_self
            
            def __exit__(timer_self, *args):
                elapsed = time.time() - timer_self.start
                self.measurements.append({
                    "name": name,
                    "time": elapsed
                })
        
        return Timer()
    
    def get_stats(self):
        """측정 통계 반환"""
        if not self.measurements:
            return {}
        
        times = [m["time"] for m in self.measurements]
        times.sort()
        
        return {
            "count": len(times),
            "min": times[0],
            "max": times[-1],
            "avg": sum(times) / len(times),
            "p50": times[len(times) // 2],
            "p95": times[int(len(times) * 0.95)],
            "p99": times[int(len(times) * 0.99)]
        }


@pytest.fixture
def performance_counter():
    """성능 측정 fixture"""
    return PerformanceCounter() 