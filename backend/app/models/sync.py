"""
스크립트-오디오 싱크 매핑 모델

문장별 타임코드 매핑, 편집 내역, 동기화 세션 관련 모델
"""

from uuid import UUID
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# =============================================================================
# Enum 타입 정의
# =============================================================================

class MappingType(str, Enum):
    """매핑 생성 방식"""
    MANUAL = "manual"              # 사용자 수동 편집
    AUTO = "auto"                  # 자동 생성 (기본값)
    AI_GENERATED = "ai_generated"  # AI 자동 정렬


class EditType(str, Enum):
    """편집 유형"""
    MANUAL = "manual"              # 수동 편집
    AI_CORRECTION = "ai_correction"  # AI 수정
    BULK_EDIT = "bulk_edit"        # 일괄 편집


class SessionType(str, Enum):
    """세션 유형"""
    INDIVIDUAL = "individual"      # 개인 학습
    GROUP = "group"               # 그룹 학습
    CLASSROOM = "classroom"       # 교실 학습


# =============================================================================
# 문장 매핑 모델
# =============================================================================

class SentenceMappingBase(BaseModel):
    """문장 매핑 기본 모델"""
    start_time: float = Field(..., description="시작 시간 (초)", ge=0)
    end_time: float = Field(..., description="종료 시간 (초)", ge=0)
    mapping_type: MappingType = Field(MappingType.MANUAL, description="매핑 생성 방식")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 메타데이터")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start_time": 10.5,
                "end_time": 15.2,
                "mapping_type": "manual",
                "metadata": {
                    "confidence": 0.95,
                    "edit_reason": "정확한 타이밍 조정"
                }
            }
        }
    )


class SentenceMappingCreate(SentenceMappingBase):
    """문장 매핑 생성 요청"""
    sentence_id: UUID = Field(..., description="문장 ID")


class SentenceMappingUpdate(BaseModel):
    """문장 매핑 수정 요청"""
    start_time: Optional[float] = Field(None, description="시작 시간 (초)", ge=0)
    end_time: Optional[float] = Field(None, description="종료 시간 (초)", ge=0)
    mapping_type: Optional[MappingType] = Field(None, description="매핑 생성 방식")
    edit_reason: Optional[str] = Field(None, description="편집 사유", max_length=500)
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 메타데이터")


class SentenceMappingResponse(SentenceMappingBase):
    """문장 매핑 응답"""
    id: UUID = Field(..., description="매핑 ID")
    sentence_id: UUID = Field(..., description="문장 ID")
    version: int = Field(..., description="매핑 버전", ge=1)
    confidence_score: float = Field(..., description="매핑 신뢰도 (0.0-1.0)", ge=0, le=1)
    created_by: Optional[UUID] = Field(None, description="생성자 ID")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")
    is_active: bool = Field(True, description="활성 상태")

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 편집 내역 모델
# =============================================================================

class MappingEditResponse(BaseModel):
    """매핑 편집 내역 응답"""
    id: UUID = Field(..., description="편집 ID")
    sentence_id: UUID = Field(..., description="문장 ID")
    user_id: UUID = Field(..., description="편집자 ID")
    old_mapping_id: Optional[UUID] = Field(None, description="이전 매핑 ID")
    new_mapping_id: UUID = Field(..., description="새 매핑 ID")
    old_start_time: Optional[float] = Field(None, description="이전 시작 시간")
    old_end_time: Optional[float] = Field(None, description="이전 종료 시간")
    new_start_time: float = Field(..., description="새 시작 시간")
    new_end_time: float = Field(..., description="새 종료 시간")
    edit_reason: Optional[str] = Field(None, description="편집 사유")
    edit_type: EditType = Field(..., description="편집 유형")
    client_info: Dict[str, Any] = Field(default_factory=dict, description="클라이언트 정보")
    created_at: datetime = Field(..., description="편집 시간")

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 동기화 세션 모델
# =============================================================================

class SyncSessionCreate(BaseModel):
    """동기화 세션 생성 요청"""
    script_id: UUID = Field(..., description="스크립트 ID")
    connection_id: str = Field(..., description="연결 ID", min_length=1, max_length=100)
    current_position: Optional[float] = Field(0.0, description="현재 재생 위치 (초)", ge=0)
    is_playing: Optional[bool] = Field(False, description="재생 상태")
    session_token: Optional[str] = Field(None, description="세션 토큰", max_length=255)
    session_type: Optional[SessionType] = Field(SessionType.INDIVIDUAL, description="세션 유형")
    client_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="클라이언트 정보")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "script_id": "550e8400-e29b-41d4-a716-446655440000",
                "connection_id": "ws_conn_12345",
                "current_position": 0.0,
                "is_playing": False,
                "session_type": "individual",
                "client_info": {
                    "browser": "Chrome",
                    "user_agent": "Mozilla/5.0...",
                    "ip_address": "192.168.1.1"
                }
            }
        }
    )


class SyncPositionUpdate(BaseModel):
    """동기화 위치 업데이트 요청"""
    position: float = Field(..., description="현재 재생 위치 (초)", ge=0)
    is_playing: Optional[bool] = Field(None, description="재생 상태")
    sentence_id: Optional[UUID] = Field(None, description="현재 문장 ID")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "position": 45.6,
                "is_playing": True,
                "sentence_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
    )


class SyncSessionResponse(BaseModel):
    """동기화 세션 응답"""
    id: UUID = Field(..., description="세션 ID")
    script_id: UUID = Field(..., description="스크립트 ID")
    user_id: Optional[UUID] = Field(None, description="사용자 ID")
    connection_id: str = Field(..., description="연결 ID")
    room_id: str = Field(..., description="룸 ID")
    current_position: float = Field(..., description="현재 재생 위치 (초)")
    is_playing: bool = Field(..., description="재생 상태")
    current_sentence_id: Optional[UUID] = Field(None, description="현재 문장 ID")
    session_token: Optional[str] = Field(None, description="세션 토큰")
    session_type: SessionType = Field(..., description="세션 유형")
    client_info: Dict[str, Any] = Field(default_factory=dict, description="클라이언트 정보")
    is_active: bool = Field(True, description="활성 상태")
    joined_at: datetime = Field(..., description="참가 시간")
    last_activity: datetime = Field(..., description="마지막 활동 시간")
    left_at: Optional[datetime] = Field(None, description="나간 시간")

    model_config = ConfigDict(from_attributes=True)


class RoomParticipant(BaseModel):
    """룸 참가자 정보"""
    user_id: Optional[UUID] = Field(None, description="사용자 ID")
    connection_id: str = Field(..., description="연결 ID")
    current_position: float = Field(..., description="현재 재생 위치")
    is_playing: bool = Field(..., description="재생 상태")
    joined_at: datetime = Field(..., description="참가 시간")
    user_info: Optional[Dict[str, Any]] = Field(None, description="사용자 정보")

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# AI 자동 정렬 모델
# =============================================================================

class AutoAlignRequest(BaseModel):
    """AI 자동 정렬 요청"""
    script_id: UUID = Field(..., description="스크립트 ID")
    audio_duration: float = Field(..., description="오디오 총 길이 (초)", gt=0)
    confidence_threshold: Optional[float] = Field(0.7, description="신뢰도 임계값", ge=0, le=1)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "script_id": "550e8400-e29b-41d4-a716-446655440000",
                "audio_duration": 300.5,
                "confidence_threshold": 0.7
            }
        }
    )


class AutoAlignResponse(BaseModel):
    """AI 자동 정렬 응답"""
    script_id: UUID = Field(..., description="스크립트 ID")
    total_sentences: int = Field(..., description="총 문장 수", ge=0)
    aligned_sentences: int = Field(..., description="정렬된 문장 수", ge=0)
    average_confidence: float = Field(..., description="평균 신뢰도", ge=0, le=1)
    processing_time: float = Field(..., description="처리 시간 (초)", ge=0)
    mappings: List[SentenceMappingResponse] = Field(..., description="생성된 매핑 목록")

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# WebSocket 메시지 모델
# =============================================================================

class WebSocketMessageType(str, Enum):
    """WebSocket 메시지 타입"""
    MAPPING_UPDATE = "mapping_update"        # 매핑 업데이트
    MAPPING_DELETE = "mapping_delete"        # 매핑 삭제
    POSITION_UPDATE = "position_update"      # 위치 업데이트
    SESSION_JOIN = "session_join"            # 세션 참가
    SESSION_LEAVE = "session_leave"          # 세션 나가기
    SYNC_STATE = "sync_state"               # 동기화 상태
    ERROR = "error"                         # 오류


class WebSocketMessage(BaseModel):
    """WebSocket 메시지"""
    type: WebSocketMessageType = Field(..., description="메시지 타입")
    room_id: str = Field(..., description="룸 ID")
    data: Dict[str, Any] = Field(..., description="메시지 데이터")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="타임스탬프")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "position_update",
                "room_id": "sync_550e8400e29b41d4a716446655440000",
                "data": {
                    "session_id": "123e4567-e89b-12d3-a456-426614174000",
                    "position": 45.6,
                    "is_playing": True,
                    "sentence_id": "456e7890-e12f-34g5-h678-901234567890"
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    )


# =============================================================================
# 응답 및 에러 모델
# =============================================================================

class SyncOperationResponse(BaseModel):
    """동기화 작업 응답"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[Dict[str, Any]] = Field(None, description="응답 데이터")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "매핑이 성공적으로 생성되었습니다.",
                "data": {
                    "mapping_id": "550e8400-e29b-41d4-a716-446655440000",
                    "confidence_score": 0.95
                }
            }
        }
    )


class SyncError(BaseModel):
    """동기화 오류"""
    error_code: str = Field(..., description="오류 코드")
    error_message: str = Field(..., description="오류 메시지")
    details: Optional[Dict[str, Any]] = Field(None, description="오류 상세 정보")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="오류 발생 시간")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error_code": "MAPPING_CONFLICT",
                "error_message": "해당 문장에 이미 활성 매핑이 존재합니다.",
                "details": {
                    "sentence_id": "550e8400-e29b-41d4-a716-446655440000",
                    "existing_mapping_id": "123e4567-e89b-12d3-a456-426614174000"
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    ) 