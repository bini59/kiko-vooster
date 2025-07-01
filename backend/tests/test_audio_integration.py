"""
오디오 API 통합 테스트

실제 API 엔드포인트를 호출하여 통합 동작을 검증
"""

import pytest
import asyncio
from uuid import uuid4
from httpx import AsyncClient
from datetime import datetime
import time

# 테스트 설정
BASE_URL = "http://localhost:8000/api/v1"
TEST_TIMEOUT = 10.0


class TestAudioAPIIntegration:
    """오디오 API 통합 테스트"""
    
    @pytest.fixture
    async def auth_headers(self, async_client: AsyncClient):
        """인증 헤더 생성"""
        # 테스트 사용자 로그인
        response = await async_client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpass123"
            }
        )
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}
        else:
            # 테스트 사용자 생성
            await async_client.post(
                f"{BASE_URL}/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "testpass123",
                    "username": "testuser"
                }
            )
            # 재로그인
            response = await async_client.post(
                f"{BASE_URL}/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "testpass123"
                }
            )
            token = response.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    async def test_script_id(self):
        """테스트용 스크립트 ID"""
        # 실제 테스트에서는 미리 생성된 스크립트 ID 사용
        return uuid4()
    
    @pytest.mark.asyncio
    async def test_full_audio_flow(self, async_client: AsyncClient, auth_headers, test_script_id):
        """전체 오디오 재생 플로우 테스트"""
        
        # 1. 스트림 정보 조회
        start_time = time.time()
        response = await async_client.get(
            f"{BASE_URL}/audio/stream/{test_script_id}",
            headers=auth_headers,
            params={"quality": "medium"}
        )
        stream_time = time.time() - start_time
        
        assert response.status_code == 200
        stream_info = response.json()
        assert "stream_url" in stream_info
        assert stream_info["format"] == "hls"
        assert stream_time < 0.3  # 300ms 이하
        
        # 2. 재생 세션 생성
        start_time = time.time()
        response = await async_client.post(
            f"{BASE_URL}/audio/play",
            headers=auth_headers,
            json={
                "script_id": str(test_script_id),
                "position": 0
            }
        )
        play_time = time.time() - start_time
        
        assert response.status_code == 200
        play_response = response.json()
        session_id = play_response["session_id"]
        assert play_time < 0.3
        
        # 3. 진행률 업데이트
        start_time = time.time()
        response = await async_client.put(
            f"{BASE_URL}/audio/progress",
            headers=auth_headers,
            json={
                "session_id": session_id,
                "position": 60.5,
                "playback_rate": 1.0
            }
        )
        progress_time = time.time() - start_time
        
        assert response.status_code == 200
        progress_response = response.json()
        assert progress_response["saved"] is True
        assert progress_time < 0.3
        
        # 4. 북마크 생성
        response = await async_client.post(
            f"{BASE_URL}/audio/bookmark",
            headers=auth_headers,
            json={
                "script_id": str(test_script_id),
                "position": 60.5,
                "note": "테스트 북마크"
            }
        )
        
        assert response.status_code == 200
        bookmark_response = response.json()
        bookmark_id = bookmark_response["id"]
        
        # 5. 북마크 목록 조회
        response = await async_client.get(
            f"{BASE_URL}/audio/bookmarks/{test_script_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        bookmarks = response.json()
        assert len(bookmarks) > 0
        
        # 6. 세션 종료
        response = await async_client.delete(
            f"{BASE_URL}/audio/session/{session_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_error_handling(self, async_client: AsyncClient, auth_headers):
        """에러 처리 테스트"""
        
        # 1. 존재하지 않는 스크립트
        response = await async_client.get(
            f"{BASE_URL}/audio/stream/{uuid4()}",
            headers=auth_headers
        )
        assert response.status_code == 404
        
        # 2. 잘못된 세션 ID로 진행률 업데이트
        response = await async_client.put(
            f"{BASE_URL}/audio/progress",
            headers=auth_headers,
            json={
                "session_id": str(uuid4()),
                "position": 60.5
            }
        )
        assert response.status_code == 404
        
        # 3. 권한 없는 북마크 삭제
        response = await async_client.delete(
            f"{BASE_URL}/audio/bookmark/{uuid4()}",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_performance_requirements(self, async_client: AsyncClient, auth_headers, test_script_id):
        """성능 요구사항 테스트"""
        
        response_times = []
        
        # 100개 요청 수행
        for _ in range(100):
            start_time = time.time()
            response = await async_client.get(
                f"{BASE_URL}/audio/stream/{test_script_id}",
                headers=auth_headers,
                params={"quality": "medium"}
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                response_times.append(response_time)
        
        # p95 계산
        response_times.sort()
        p95_index = int(len(response_times) * 0.95)
        p95_time = response_times[p95_index] if response_times else 0
        
        print(f"p95 응답시간: {p95_time * 1000:.2f}ms")
        assert p95_time < 0.3  # 300ms 이하
    
    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, async_client: AsyncClient, auth_headers, test_script_id):
        """동시 세션 처리 테스트"""
        
        async def create_and_update_session():
            # 세션 생성
            response = await async_client.post(
                f"{BASE_URL}/audio/play",
                headers=auth_headers,
                json={
                    "script_id": str(test_script_id),
                    "position": 0
                }
            )
            
            if response.status_code == 200:
                session_id = response.json()["session_id"]
                
                # 진행률 업데이트
                await async_client.put(
                    f"{BASE_URL}/audio/progress",
                    headers=auth_headers,
                    json={
                        "session_id": session_id,
                        "position": 120.0
                    }
                )
                
                # 세션 종료
                await async_client.delete(
                    f"{BASE_URL}/audio/session/{session_id}",
                    headers=auth_headers
                )
        
        # 10개 동시 세션 생성
        tasks = [create_and_update_session() for _ in range(10)]
        await asyncio.gather(*tasks)


class TestCacheEffectiveness:
    """캐시 효과 테스트"""
    
    @pytest.mark.asyncio
    async def test_cache_hit_rate(self, async_client: AsyncClient, auth_headers, test_script_id):
        """캐시 히트율 테스트"""
        
        # 첫 번째 요청 (캐시 미스)
        response1 = await async_client.get(
            f"{BASE_URL}/audio/stream/{test_script_id}",
            headers=auth_headers,
            params={"quality": "medium"}
        )
        assert response1.status_code == 200
        assert response1.json()["cached"] is False
        
        # 두 번째 요청 (캐시 히트)
        response2 = await async_client.get(
            f"{BASE_URL}/audio/stream/{test_script_id}",
            headers=auth_headers,
            params={"quality": "medium"}
        )
        assert response2.status_code == 200
        assert response2.json()["cached"] is True
        
        # 응답 시간 비교
        start_time = time.time()
        await async_client.get(
            f"{BASE_URL}/audio/stream/{test_script_id}",
            headers=auth_headers,
            params={"quality": "medium"}
        )
        cached_time = time.time() - start_time
        
        print(f"캐시된 응답 시간: {cached_time * 1000:.2f}ms")
        assert cached_time < 0.05  # 50ms 이하


class TestWebSocketSync:
    """WebSocket 실시간 동기화 테스트 (추후 구현)"""
    
    @pytest.mark.skip(reason="WebSocket 구현 후 활성화")
    async def test_realtime_progress_sync(self):
        """실시간 진행률 동기화 테스트"""
        pass
    
    @pytest.mark.skip(reason="WebSocket 구현 후 활성화")
    async def test_multi_device_sync(self):
        """다중 기기 동기화 테스트"""
        pass


# 헬퍼 함수
async def measure_api_performance(client: AsyncClient, endpoint: str, method: str = "GET", **kwargs):
    """API 성능 측정 헬퍼"""
    start_time = time.time()
    
    if method == "GET":
        response = await client.get(endpoint, **kwargs)
    elif method == "POST":
        response = await client.post(endpoint, **kwargs)
    elif method == "PUT":
        response = await client.put(endpoint, **kwargs)
    elif method == "DELETE":
        response = await client.delete(endpoint, **kwargs)
    
    response_time = time.time() - start_time
    
    return {
        "status_code": response.status_code,
        "response_time": response_time,
        "response": response.json() if response.status_code == 200 else None
    } 