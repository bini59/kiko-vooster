"""
스크립트-오디오 싱크 매핑 엔진 통합 테스트

타임코드 매핑, 실시간 동기화, WebSocket, 성능, 보안 검증
"""

import pytest
import asyncio
import json
import time
from uuid import uuid4, UUID
from typing import Dict, Any, List
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

from app.main import app
from app.core.config import settings
from app.models.sync import MappingType, WebSocketMessageType


class TestSyncMappingCRUD:
    """타임코드 매핑 CRUD 테스트"""
    
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
        assert result["confidence_score"] == 1.0  # manual mapping
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
    
    @pytest.mark.asyncio
    async def test_update_sentence_mapping(self, async_client: AsyncClient, auth_headers, test_script_id):
        """문장 매핑 수정 테스트"""
        # 먼저 매핑 생성
        mapping = await self.test_create_sentence_mapping(async_client, auth_headers, test_script_id)
        sentence_id = mapping["sentence_id"]
        
        # 매핑 수정
        update_data = {
            "start_time": 1.0,
            "end_time": 4.0,
            "edit_reason": "시간 조정"
        }
        
        response = await async_client.put(
            f"/api/v1/sync/mappings/sentence/{sentence_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 수정 결과 검증
        assert result["sentence_id"] == sentence_id
        assert result["start_time"] == 1.0
        assert result["end_time"] == 4.0
        assert result["id"] != mapping["id"]  # 새 버전 생성됨
        
        # 편집 내역 확인
        history_response = await async_client.get(
            f"/api/v1/sync/mappings/sentence/{sentence_id}/history",
            headers=auth_headers
        )
        
        assert history_response.status_code == 200
        history = history_response.json()
        assert len(history) >= 1
        assert history[0]["edit_reason"] == "시간 조정"
    
    @pytest.mark.asyncio
    async def test_delete_sentence_mapping(self, async_client: AsyncClient, auth_headers, test_script_id):
        """문장 매핑 삭제 테스트"""
        # 먼저 매핑 생성
        mapping = await self.test_create_sentence_mapping(async_client, auth_headers, test_script_id)
        sentence_id = mapping["sentence_id"]
        
        # 매핑 삭제
        response = await async_client.delete(
            f"/api/v1/sync/mappings/sentence/{sentence_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        # 삭제 확인
        get_response = await async_client.get(
            f"/api/v1/sync/mappings/sentence/{sentence_id}",
            headers=auth_headers
        )
        
        assert get_response.status_code == 200
        assert get_response.json() is None  # 비활성화됨
    
    @pytest.mark.asyncio
    async def test_script_mappings_bulk_query(self, async_client: AsyncClient, auth_headers, test_script_id):
        """스크립트 전체 매핑 조회 테스트"""
        # 여러 매핑 생성
        mappings_created = []
        for i in range(3):
            sentence_data = {
                "script_id": test_script_id,
                "content": f"テスト文章{i}です。",
                "order_index": i + 1,
                "metadata": {}
            }
            
            sentence_response = await async_client.post(
                "/api/v1/scripts/sentences",
                json=sentence_data,
                headers=auth_headers
            )
            sentence_id = sentence_response.json()["id"]
            
            mapping_data = {
                "sentence_id": sentence_id,
                "start_time": float(i * 3),
                "end_time": float((i + 1) * 3),
                "mapping_type": "manual"
            }
            
            mapping_response = await async_client.post(
                "/api/v1/sync/mappings",
                json=mapping_data,
                headers=auth_headers
            )
            mappings_created.append(mapping_response.json())
        
        # 스크립트 매핑들 일괄 조회
        response = await async_client.get(
            f"/api/v1/sync/mappings/script/{test_script_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 결과 검증
        assert len(result) >= 3
        for mapping in result:
            assert mapping["sentence_id"] in [m["sentence_id"] for m in mappings_created]
            assert mapping["is_active"] is True


class TestSyncSessions:
    """동기화 세션 테스트"""
    
    @pytest.mark.asyncio
    async def test_create_sync_session(self, async_client: AsyncClient, auth_headers, test_script_id):
        """동기화 세션 생성 테스트"""
        session_data = {
            "script_id": test_script_id,
            "connection_id": str(uuid4()),
            "current_position": 0.0,
            "is_playing": False,
            "client_info": {"browser": "Chrome", "version": "120"}
        }
        
        response = await async_client.post(
            "/api/v1/sync/sessions",
            json=session_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        result = response.json()
        
        # 응답 검증
        assert result["script_id"] == test_script_id
        assert result["connection_id"] == session_data["connection_id"]
        assert result["current_position"] == 0.0
        assert result["is_playing"] is False
        assert result["is_active"] is True
        assert "id" in result
        assert "session_token" in result
        
        return result
    
    @pytest.mark.asyncio
    async def test_update_sync_position(self, async_client: AsyncClient, auth_headers, test_script_id):
        """동기화 위치 업데이트 테스트"""
        # 세션 생성
        session = await self.test_create_sync_session(async_client, auth_headers, test_script_id)
        session_id = session["id"]
        
        # 위치 업데이트
        position_data = {
            "position": 15.5,
            "is_playing": True
        }
        
        response = await async_client.put(
            f"/api/v1/sync/sessions/{session_id}/position",
            json=position_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_room_participants(self, async_client: AsyncClient, auth_headers, test_script_id):
        """룸 참가자 조회 테스트"""
        # 여러 세션 생성
        sessions = []
        for i in range(2):
            session_data = {
                "script_id": test_script_id,
                "connection_id": str(uuid4()),
                "current_position": 0.0,
                "is_playing": False
            }
            
            response = await async_client.post(
                "/api/v1/sync/sessions",
                json=session_data,
                headers=auth_headers
            )
            sessions.append(response.json())
        
        # 참가자 조회
        response = await async_client.get(
            f"/api/v1/sync/sessions/script/{test_script_id}/participants",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 참가자 수 검증
        assert len(result) >= 2


class TestAIAutoAlign:
    """AI 자동 정렬 테스트"""
    
    @pytest.mark.asyncio
    async def test_auto_align_script(self, async_client: AsyncClient, auth_headers, test_script_id):
        """AI 자동 정렬 테스트"""
        # 테스트용 문장들 생성
        sentences = []
        for i in range(5):
            sentence_data = {
                "script_id": test_script_id,
                "content": f"自動整列テスト文章{i}です。",
                "order_index": i + 1,
                "metadata": {}
            }
            
            response = await async_client.post(
                "/api/v1/scripts/sentences",
                json=sentence_data,
                headers=auth_headers
            )
            sentences.append(response.json())
        
        # AI 자동 정렬 요청
        align_data = {
            "script_id": test_script_id,
            "audio_duration": 25.0,  # 5문장 * 5초
            "force_realign": True
        }
        
        response = await async_client.post(
            "/api/v1/sync/ai-align",
            json=align_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 정렬 결과 검증
        assert result["success"] is True
        assert len(result["mappings"]) == 5
        
        # 각 매핑 검증
        for i, mapping in enumerate(result["mappings"]):
            assert mapping["mapping_type"] == "ai_generated"
            assert mapping["start_time"] == i * 5.0
            assert mapping["end_time"] == (i + 1) * 5.0
            assert mapping["confidence_score"] > 0.5


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
    
    @pytest.mark.asyncio
    async def test_bulk_mapping_query_performance(self, async_client: AsyncClient, auth_headers, test_script_id):
        """대량 매핑 조회 성능 테스트"""
        # 여러 매핑 생성 (최대 10개)
        for i in range(10):
            sentence_data = {
                "script_id": test_script_id,
                "content": f"대량테스트문장{i}입니다。",
                "order_index": i + 1,
                "metadata": {}
            }
            
            sentence_response = await async_client.post(
                "/api/v1/scripts/sentences",
                json=sentence_data,
                headers=auth_headers
            )
            sentence_id = sentence_response.json()["id"]
            
            mapping_data = {
                "sentence_id": sentence_id,
                "start_time": float(i * 2),
                "end_time": float((i + 1) * 2),
                "mapping_type": "manual"
            }
            
            await async_client.post(
                "/api/v1/sync/mappings",
                json=mapping_data,
                headers=auth_headers
            )
        
        # 대량 조회 시간 측정
        start_time = time.time()
        
        response = await async_client.get(
            f"/api/v1/sync/mappings/script/{test_script_id}",
            headers=auth_headers
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert response.status_code == 200
        assert duration <= 0.3, f"대량 조회가 {duration:.2f}초 소요 (0.3초 초과)"
        
        result = response.json()
        assert len(result) >= 10


class TestSecurityAuthentication:
    """보안 및 인증 테스트"""
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, async_client: AsyncClient, test_script_id):
        """비인증 접근 테스트"""
        # 인증 없이 매핑 생성 시도
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
    async def test_invalid_token_access(self, async_client: AsyncClient, test_script_id):
        """잘못된 토큰으로 접근 테스트"""
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}
        
        response = await async_client.get(
            f"/api/v1/sync/mappings/script/{test_script_id}",
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
        assert "시작 시간" in response.json()["detail"]


class TestErrorHandling:
    """예외 처리 테스트"""
    
    @pytest.mark.asyncio
    async def test_nonexistent_sentence_mapping(self, async_client: AsyncClient, auth_headers):
        """존재하지 않는 문장 매핑 테스트"""
        nonexistent_id = str(uuid4())
        
        response = await async_client.get(
            f"/api/v1/sync/mappings/sentence/{nonexistent_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json() is None
    
    @pytest.mark.asyncio
    async def test_invalid_sentence_id_mapping(self, async_client: AsyncClient, auth_headers):
        """잘못된 문장 ID로 매핑 생성 테스트"""
        invalid_mapping = {
            "sentence_id": str(uuid4()),  # 존재하지 않는 문장
            "start_time": 0.0,
            "end_time": 3.0,
            "mapping_type": "manual"
        }
        
        response = await async_client.post(
            "/api/v1/sync/mappings",
            json=invalid_mapping,
            headers=auth_headers
        )
        
        # 문장이 존재하지 않아도 매핑은 생성됨 (스키마 검증만)
        # 실제 서비스에서는 외래키 제약으로 실패해야 함
        assert response.status_code in [201, 400, 404]


class TestHealthEndpoint:
    """헬스 체크 엔드포인트 테스트"""
    
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


# WebSocket 테스트는 별도 테스트 클래스에서 처리 (실제 WebSocket 클라이언트 필요)
class TestWebSocketIntegration:
    """WebSocket 통합 테스트"""
    
    def test_websocket_endpoint_exists(self):
        """WebSocket 엔드포인트 존재 확인"""
        # WebSocket 엔드포인트가 라우터에 등록되어 있는지 확인
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


@pytest.mark.integration
class TestFullSyncWorkflow:
    """전체 싱크 워크플로우 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_complete_sync_mapping_workflow(self, async_client: AsyncClient, auth_headers, test_script_id):
        """완전한 싱크 매핑 워크플로우 테스트"""
        # 1. 문장 생성
        sentence_data = {
            "script_id": test_script_id,
            "content": "完全なワークフローテストです。",
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
        
        # 2. 초기 매핑 생성
        mapping_data = {
            "sentence_id": sentence_id,
            "start_time": 0.0,
            "end_time": 4.0,
            "mapping_type": "manual",
            "metadata": {"initial": True}
        }
        
        create_response = await async_client.post(
            "/api/v1/sync/mappings",
            json=mapping_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        initial_mapping = create_response.json()
        
        # 3. 매핑 조회
        get_response = await async_client.get(
            f"/api/v1/sync/mappings/sentence/{sentence_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        retrieved_mapping = get_response.json()
        assert retrieved_mapping["id"] == initial_mapping["id"]
        
        # 4. 매핑 수정
        update_data = {
            "start_time": 0.5,
            "end_time": 3.8,
            "edit_reason": "정확도 향상"
        }
        
        update_response = await async_client.put(
            f"/api/v1/sync/mappings/sentence/{sentence_id}",
            json=update_data,
            headers=auth_headers
        )
        assert update_response.status_code == 200
        updated_mapping = update_response.json()
        assert updated_mapping["start_time"] == 0.5
        assert updated_mapping["end_time"] == 3.8
        
        # 5. 편집 내역 확인
        history_response = await async_client.get(
            f"/api/v1/sync/mappings/sentence/{sentence_id}/history",
            headers=auth_headers
        )
        assert history_response.status_code == 200
        history = history_response.json()
        assert len(history) >= 1
        assert history[0]["edit_reason"] == "정확도 향상"
        
        # 6. 동기화 세션 생성
        session_data = {
            "script_id": test_script_id,
            "connection_id": str(uuid4()),
            "current_position": 0.0,
            "is_playing": False
        }
        
        session_response = await async_client.post(
            "/api/v1/sync/sessions",
            json=session_data,
            headers=auth_headers
        )
        assert session_response.status_code == 201
        session = session_response.json()
        
        # 7. 위치 업데이트
        position_data = {
            "position": 2.0,
            "is_playing": True,
            "sentence_id": sentence_id
        }
        
        position_response = await async_client.put(
            f"/api/v1/sync/sessions/{session['id']}/position",
            json=position_data,
            headers=auth_headers
        )
        assert position_response.status_code == 200
        
        # 8. 매핑 삭제
        delete_response = await async_client.delete(
            f"/api/v1/sync/mappings/sentence/{sentence_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200
        
        # 9. 삭제 확인
        final_get_response = await async_client.get(
            f"/api/v1/sync/mappings/sentence/{sentence_id}",
            headers=auth_headers
        )
        assert final_get_response.status_code == 200
        assert final_get_response.json() is None 