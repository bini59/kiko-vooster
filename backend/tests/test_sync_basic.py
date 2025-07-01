"""
스크립트-오디오 싱크 매핑 기본 테스트
"""

import pytest
import time
from uuid import uuid4
from httpx import AsyncClient


class TestSyncHealth:
    """싱크 헬스 체크 테스트"""
    
    @pytest.mark.asyncio
    async def test_sync_health_check(self, async_client: AsyncClient):
        """싱크 헬스 체크 테스트"""
        response = await async_client.get("/api/v1/sync/health")
        
        assert response.status_code == 200
        result = response.json()
        
        assert "status" in result
        assert "timestamp" in result
        assert "version" in result
        assert result["status"] == "healthy"


class TestSyncMappingBasic:
    """기본 매핑 테스트"""
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, async_client: AsyncClient):
        """비인증 접근 테스트"""
        mapping_data = {
            "sentence_id": str(uuid4()),
            "start_time": 0.0,
            "end_time": 3.0,
            "mapping_type": "manual"
        }
        
        response = await async_client.post(
            "/api/v1/sync/mappings",
            json=mapping_data
        )
        
        assert response.status_code == 401  # Unauthorized
    
    @pytest.mark.asyncio
    async def test_invalid_token_access(self, async_client: AsyncClient):
        """잘못된 토큰으로 접근 테스트"""
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}
        
        response = await async_client.get(
            f"/api/v1/sync/mappings/script/{uuid4()}",
            headers=invalid_headers
        )
        
        assert response.status_code == 401  # Unauthorized
    
    @pytest.mark.asyncio
    async def test_input_validation(self, async_client: AsyncClient, auth_headers):
        """입력 검증 테스트"""
        # 잘못된 시간 범위
        invalid_mapping = {
            "sentence_id": str(uuid4()),
            "start_time": 5.0,
            "end_time": 3.0,  # 시작 시간보다 작음
            "mapping_type": "manual"
        }
        
        response = await async_client.post(
            "/api/v1/sync/mappings",
            json=invalid_mapping,
            headers=auth_headers
        )
        
        assert response.status_code == 400  # Bad Request


class TestSyncMappingCRUD:
    """매핑 CRUD 테스트"""
    
    @pytest.mark.asyncio
    async def test_create_sentence_mapping(self, async_client: AsyncClient, auth_headers, test_script_id):
        """문장 매핑 생성 테스트"""
        # 테스트용 문장 생성
        sentence_data = {
            "script_id": test_script_id,
            "content": "これは日本語のテストです。",
            "order_index": 1,
            "metadata": {}
        }
        
        sentence_response = await async_client.post(
            "/api/v1/scripts/sentences",
            json=sentence_data,
            headers=auth_headers
        )
        assert sentence_response.status_code == 201
        sentence_id = sentence_response.json()["id"]
        
        # 매핑 생성
        mapping_data = {
            "sentence_id": sentence_id,
            "start_time": 0.0,
            "end_time": 3.5,
            "mapping_type": "manual",
            "metadata": {"test": True}
        }
        
        response = await async_client.post(
            "/api/v1/sync/mappings",
            json=mapping_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        result = response.json()
        
        # 응답 검증
        assert result["sentence_id"] == sentence_id
        assert result["start_time"] == 0.0
        assert result["end_time"] == 3.5
        assert result["mapping_type"] == "manual"
        assert result["is_active"] is True
        assert "id" in result
        assert "created_at" in result
        
        return result
    
    @pytest.mark.asyncio
    async def test_get_sentence_mapping(self, async_client: AsyncClient, auth_headers, test_script_id):
        """문장 매핑 조회 테스트"""
        # 먼저 매핑 생성
        mapping = await self.test_create_sentence_mapping(async_client, auth_headers, test_script_id)
        sentence_id = mapping["sentence_id"]
        
        # 매핑 조회
        response = await async_client.get(
            f"/api/v1/sync/mappings/sentence/{sentence_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 결과 검증
        assert result["id"] == mapping["id"]
        assert result["sentence_id"] == sentence_id
        assert result["start_time"] == mapping["start_time"]
        assert result["end_time"] == mapping["end_time"]


class TestPerformanceRequirements:
    """성능 요구사항 테스트"""
    
    @pytest.mark.asyncio
    async def test_mapping_creation_performance(self, async_client: AsyncClient, auth_headers, test_script_id):
        """매핑 생성 성능 테스트 (≤1s 요구사항)"""
        # 테스트용 문장 생성
        sentence_data = {
            "script_id": test_script_id,
            "content": "パフォーマンステストです。",
            "order_index": 1,
            "metadata": {}
        }
        
        sentence_response = await async_client.post(
            "/api/v1/scripts/sentences",
            json=sentence_data,
            headers=auth_headers
        )
        sentence_id = sentence_response.json()["id"]
        
        # 매핑 생성 시간 측정
        mapping_data = {
            "sentence_id": sentence_id,
            "start_time": 0.0,
            "end_time": 2.0,
            "mapping_type": "manual"
        }
        
        start_time = time.time()
        
        response = await async_client.post(
            "/api/v1/sync/mappings",
            json=mapping_data,
            headers=auth_headers
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert response.status_code == 201
        assert duration <= 1.0, f"매핑 생성이 {duration:.2f}초 소요 (1초 초과)"


class TestWebSocketIntegration:
    """WebSocket 통합 테스트"""
    
    def test_websocket_endpoint_exists(self):
        """WebSocket 엔드포인트 존재 확인"""
        from app.websocket.sync_websocket import websocket_router
        
        # 라우터에 WebSocket 엔드포인트가 있는지 확인
        websocket_routes = [route for route in websocket_router.routes if hasattr(route, 'path')]
        websocket_paths = [route.path for route in websocket_routes]
        
        assert "/ws/sync/{script_id}" in websocket_paths
    
    def test_websocket_manager_initialization(self):
        """WebSocket 매니저 초기화 테스트"""
        from app.websocket.sync_websocket import get_sync_websocket_manager
        
        manager = get_sync_websocket_manager()
        assert manager is not None
        assert hasattr(manager, 'connection_manager')
        assert hasattr(manager, 'connect_to_sync_room')
        assert hasattr(manager, 'broadcast_mapping_update') 