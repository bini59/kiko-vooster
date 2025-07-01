"""
스크립트-오디오 싱크 매핑 API

문장별 타임코드 매핑, 편집 내역, 동기화 세션 관련 엔드포인트
"""

from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import JSONResponse
import logging
import time

from app.core.auth import get_current_user, get_optional_user
from app.core.database import get_database
from app.core.cache.cache_manager import get_cache_manager
from app.services.sync import get_sync_mapping_service
from app.models.user import User
from app.models.sync import (
    SentenceMappingCreate, SentenceMappingUpdate, SentenceMappingResponse,
    MappingEditResponse, SyncSessionCreate, SyncSessionResponse, 
    SyncPositionUpdate, RoomParticipant, AutoAlignRequest, AutoAlignResponse,
    SyncOperationResponse, SyncError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sync", tags=["sync"])


# =============================================================================
# 문장 매핑 CRUD 엔드포인트
# =============================================================================

@router.post("/mappings", response_model=SentenceMappingResponse)
async def create_sentence_mapping(
    mapping_data: SentenceMappingCreate,
    current_user: User = Depends(get_current_user)
):
    """
    새 문장 매핑 생성
    
    - **sentence_id**: 문장 ID
    - **start_time**: 시작 시간 (초)
    - **end_time**: 종료 시간 (초)
    - **mapping_type**: 매핑 생성 방식 (manual, auto, ai_generated)
    - **metadata**: 추가 메타데이터
    """
    try:
        sync_service = get_sync_mapping_service()
        
        # 시간 유효성 검사
        if mapping_data.start_time >= mapping_data.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="시작 시간은 종료 시간보다 작아야 합니다."
            )
        
        # 매핑 생성
        mapping = await sync_service.create_sentence_mapping(
            sentence_id=mapping_data.sentence_id,
            start_time=mapping_data.start_time,
            end_time=mapping_data.end_time,
            user_id=current_user.id,
            mapping_type=mapping_data.mapping_type.value,
            metadata=mapping_data.metadata
        )
        
        return SentenceMappingResponse(**mapping)
        
    except ValueError as e:
        logger.warning(f"Invalid mapping data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating sentence mapping: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="매핑 생성 중 오류가 발생했습니다."
        )


@router.get("/mappings/sentence/{sentence_id}", response_model=Optional[SentenceMappingResponse])
async def get_sentence_mapping(
    sentence_id: UUID,
    user: Optional[User] = Depends(get_optional_user)
):
    """
    문장 매핑 조회
    
    - **sentence_id**: 문장 ID
    """
    try:
        sync_service = get_sync_mapping_service()
        mapping = await sync_service.get_sentence_mapping(sentence_id)
        
        if not mapping:
            return None
        
        return SentenceMappingResponse(**mapping)
        
    except Exception as e:
        logger.error(f"Error getting sentence mapping: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="매핑 조회 중 오류가 발생했습니다."
        )


@router.put("/mappings/sentence/{sentence_id}", response_model=SentenceMappingResponse)
async def update_sentence_mapping(
    sentence_id: UUID,
    mapping_update: SentenceMappingUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    문장 매핑 수정
    
    - **sentence_id**: 문장 ID
    - **start_time**: 새 시작 시간 (선택)
    - **end_time**: 새 종료 시간 (선택)
    - **mapping_type**: 매핑 생성 방식 (선택)
    - **edit_reason**: 편집 사유 (선택)
    - **metadata**: 추가 메타데이터 (선택)
    """
    try:
        sync_service = get_sync_mapping_service()
        
        # 기존 매핑 확인
        existing_mapping = await sync_service.get_sentence_mapping(sentence_id)
        if not existing_mapping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 문장의 매핑을 찾을 수 없습니다."
            )
        
        # 업데이트할 값 결정
        start_time = mapping_update.start_time or existing_mapping['start_time']
        end_time = mapping_update.end_time or existing_mapping['end_time']
        mapping_type = mapping_update.mapping_type.value if mapping_update.mapping_type else existing_mapping['mapping_type']
        
        # 시간 유효성 검사
        if start_time >= end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="시작 시간은 종료 시간보다 작아야 합니다."
            )
        
        # 매핑 업데이트
        updated_mapping = await sync_service.update_sentence_mapping(
            sentence_id=sentence_id,
            start_time=start_time,
            end_time=end_time,
            user_id=current_user.id,
            mapping_type=mapping_type,
            edit_reason=mapping_update.edit_reason,
            metadata=mapping_update.metadata
        )
        
        return SentenceMappingResponse(**updated_mapping)
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid mapping update data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating sentence mapping: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="매핑 수정 중 오류가 발생했습니다."
        )


@router.delete("/mappings/sentence/{sentence_id}", response_model=SyncOperationResponse)
async def delete_sentence_mapping(
    sentence_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    문장 매핑 삭제 (비활성화)
    
    - **sentence_id**: 문장 ID
    """
    try:
        sync_service = get_sync_mapping_service()
        
        success = await sync_service.delete_sentence_mapping(
            sentence_id=sentence_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 문장의 매핑을 찾을 수 없습니다."
            )
        
        return SyncOperationResponse(
            success=True,
            message="매핑이 성공적으로 삭제되었습니다.",
            data={"sentence_id": str(sentence_id)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting sentence mapping: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="매핑 삭제 중 오류가 발생했습니다."
        )


@router.get("/mappings/script/{script_id}", response_model=List[SentenceMappingResponse])
async def get_script_mappings(
    script_id: UUID,
    include_inactive: bool = Query(False, description="비활성 매핑 포함 여부"),
    user: Optional[User] = Depends(get_optional_user)
):
    """
    스크립트의 모든 문장 매핑 조회
    
    - **script_id**: 스크립트 ID
    - **include_inactive**: 비활성 매핑 포함 여부
    """
    try:
        sync_service = get_sync_mapping_service()
        mappings = await sync_service.get_script_mappings(
            script_id=script_id,
            include_inactive=include_inactive
        )
        
        return [SentenceMappingResponse(**mapping) for mapping in mappings]
        
    except Exception as e:
        logger.error(f"Error getting script mappings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="스크립트 매핑 조회 중 오류가 발생했습니다."
        )


# =============================================================================
# 편집 내역 엔드포인트
# =============================================================================

@router.get("/mappings/sentence/{sentence_id}/history", response_model=List[MappingEditResponse])
async def get_mapping_edit_history(
    sentence_id: UUID,
    limit: int = Query(50, description="조회할 편집 내역 수", ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    문장 매핑 편집 내역 조회
    
    - **sentence_id**: 문장 ID
    - **limit**: 조회할 편집 내역 수 (최대 100개)
    """
    try:
        sync_service = get_sync_mapping_service()
        edits = await sync_service.get_mapping_edit_history(
            sentence_id=sentence_id,
            limit=limit
        )
        
        return [MappingEditResponse(**edit) for edit in edits]
        
    except Exception as e:
        logger.error(f"Error getting mapping edit history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="편집 내역 조회 중 오류가 발생했습니다."
        )


# =============================================================================
# 동기화 세션 엔드포인트
# =============================================================================

@router.post("/sessions", response_model=SyncSessionResponse)
async def create_sync_session(
    session_data: SyncSessionCreate,
    user: Optional[User] = Depends(get_optional_user)
):
    """
    동기화 세션 생성
    
    - **script_id**: 스크립트 ID
    - **connection_id**: 연결 ID (WebSocket 연결 식별자)
    - **current_position**: 현재 재생 위치 (초)
    - **is_playing**: 재생 상태
    - **session_token**: 세션 토큰 (익명 사용자용)
    - **session_type**: 세션 유형
    - **client_info**: 클라이언트 정보
    """
    try:
        sync_service = get_sync_mapping_service()
        
        session = await sync_service.create_sync_session(
            script_id=session_data.script_id,
            connection_id=session_data.connection_id,
            user_id=user.id if user else None,
            current_position=session_data.current_position or 0.0,
            is_playing=session_data.is_playing or False,
            session_token=session_data.session_token,
            client_info=session_data.client_info
        )
        
        return SyncSessionResponse(**session)
        
    except ValueError as e:
        logger.warning(f"Invalid session data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating sync session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="동기화 세션 생성 중 오류가 발생했습니다."
        )


@router.put("/sessions/{session_id}/position", response_model=SyncOperationResponse)
async def update_sync_position(
    session_id: UUID,
    position_update: SyncPositionUpdate,
    user: Optional[User] = Depends(get_optional_user)
):
    """
    동기화 세션 위치 업데이트
    
    - **session_id**: 세션 ID
    - **position**: 현재 재생 위치 (초)
    - **is_playing**: 재생 상태 (선택)
    - **sentence_id**: 현재 문장 ID (선택)
    """
    try:
        sync_service = get_sync_mapping_service()
        
        success = await sync_service.update_sync_position(
            session_id=session_id,
            position=position_update.position,
            is_playing=position_update.is_playing,
            sentence_id=position_update.sentence_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="세션을 찾을 수 없거나 이미 종료되었습니다."
            )
        
        return SyncOperationResponse(
            success=True,
            message="위치가 성공적으로 업데이트되었습니다.",
            data={
                "session_id": str(session_id),
                "position": position_update.position,
                "is_playing": position_update.is_playing
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating sync position: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="위치 업데이트 중 오류가 발생했습니다."
        )


@router.get("/sessions/script/{script_id}/participants", response_model=List[RoomParticipant])
async def get_room_participants(
    script_id: UUID,
    user: Optional[User] = Depends(get_optional_user)
):
    """
    룸 참가자 목록 조회
    
    - **script_id**: 스크립트 ID
    """
    try:
        sync_service = get_sync_mapping_service()
        participants = await sync_service.get_room_participants(script_id)
        
        return [RoomParticipant(**participant) for participant in participants]
        
    except Exception as e:
        logger.error(f"Error getting room participants: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="참가자 목록 조회 중 오류가 발생했습니다."
        )


# =============================================================================
# AI 자동 정렬 엔드포인트
# =============================================================================

@router.post("/ai-align", response_model=AutoAlignResponse)
async def auto_align_script(
    align_request: AutoAlignRequest,
    current_user: User = Depends(get_current_user)
):
    """
    AI 기반 스크립트 자동 정렬
    
    - **script_id**: 스크립트 ID
    - **audio_duration**: 오디오 총 길이 (초)
    - **confidence_threshold**: 신뢰도 임계값 (0.0-1.0)
    
    ⚠️ 현재는 균등 분할 방식으로 시뮬레이션됩니다. 향후 AI 모델 연동 예정.
    """
    try:
        start_time = time.time()
        sync_service = get_sync_mapping_service()
        
        # AI 자동 정렬 실행
        mappings = await sync_service.auto_align_script(
            script_id=align_request.script_id,
            audio_duration=align_request.audio_duration,
            user_id=current_user.id
        )
        
        processing_time = time.time() - start_time
        
        # 통계 계산
        total_sentences = len(mappings)
        aligned_sentences = len([m for m in mappings if m.get('confidence_score', 0) >= align_request.confidence_threshold])
        average_confidence = sum(m.get('confidence_score', 0) for m in mappings) / total_sentences if total_sentences > 0 else 0
        
        return AutoAlignResponse(
            script_id=align_request.script_id,
            total_sentences=total_sentences,
            aligned_sentences=aligned_sentences,
            average_confidence=average_confidence,
            processing_time=processing_time,
            mappings=[SentenceMappingResponse(**mapping) for mapping in mappings]
        )
        
    except ValueError as e:
        logger.warning(f"Invalid auto-align request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error auto-aligning script: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="자동 정렬 중 오류가 발생했습니다."
        )


# =============================================================================
# 헬스체크 및 상태 엔드포인트
# =============================================================================

@router.get("/health", response_model=dict)
async def sync_health_check():
    """
    동기화 서비스 헬스체크
    """
    try:
        # 캐시 연결 확인
        cache_manager = get_cache_manager()
        await cache_manager.set("health_check", "ok", ttl=10)
        cache_status = await cache_manager.get("health_check")
        
        # DB 연결 확인
        db = await get_database()
        db_result = await db.client.from_('sentence_mappings').select('count', count='exact').limit(1).execute()
        db_status = "ok" if db_result else "error"
        
        return {
            "status": "healthy",
            "service": "sync_mapping",
            "timestamp": time.time(),
            "cache_status": "ok" if cache_status == "ok" else "error",
            "database_status": db_status,
            "features": {
                "mapping_crud": True,
                "realtime_sync": True,
                "edit_history": True,
                "ai_alignment": True
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "sync_mapping",
                "error": str(e),
                "timestamp": time.time()
            }
        ) 