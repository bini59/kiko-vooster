"""
오디오 재생 API Pydantic 모델

요청/응답 데이터 검증 및 직렬화를 위한 모델 정의
"""

from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID


# 품질 옵션
QualityType = Literal["low", "medium", "high"]
FormatType = Literal["hls", "mp3"]
StatusType = Literal["preparing", "ready", "failed"]
PriorityType = Literal["high", "normal", "low"]


class StreamRequest(BaseModel):
    """스트림 요청 모델"""
    quality: QualityType = Field(default="medium", description="오디오 품질")
    format: FormatType = Field(default="hls", description="스트리밍 형식")


class StreamResponse(BaseModel):
    """스트림 응답 모델"""
    stream_url: str = Field(..., description="스트림 URL")
    duration: float = Field(..., description="총 재생 시간 (초)")
    bitrate: int = Field(..., description="비트레이트 (bps)")
    format: FormatType = Field(..., description="스트리밍 형식")
    cached: bool = Field(..., description="캐시 여부")
    expires_at: datetime = Field(..., description="URL 만료 시간")


class PrepareRequest(BaseModel):
    """오디오 준비 요청 모델"""
    priority: PriorityType = Field(default="normal", description="처리 우선순위")
    segments: Optional[List[int]] = Field(default=None, description="프리로드할 세그먼트 시작 시간")


class PrepareResponse(BaseModel):
    """오디오 준비 응답 모델"""
    status: StatusType = Field(..., description="처리 상태")
    progress: int = Field(..., ge=0, le=100, description="진행률 (0-100)")
    estimated_time: Optional[int] = Field(None, description="예상 완료 시간 (초)")
    error: Optional[str] = Field(None, description="에러 메시지")


class PlayRequest(BaseModel):
    """재생 시작 요청 모델"""
    script_id: UUID = Field(..., description="스크립트 ID")
    position: float = Field(default=0, ge=0, description="시작 위치 (초)")
    sentence_id: Optional[UUID] = Field(None, description="문장 ID")


class PlayResponse(BaseModel):
    """재생 시작 응답 모델"""
    session_id: UUID = Field(..., description="재생 세션 ID")
    stream_url: str = Field(..., description="스트림 URL")
    start_position: float = Field(..., description="시작 위치")


class ProgressUpdate(BaseModel):
    """진행률 업데이트 모델"""
    session_id: UUID = Field(..., description="재생 세션 ID")
    position: float = Field(..., ge=0, description="현재 위치 (초)")
    sentence_id: Optional[UUID] = Field(None, description="현재 문장 ID")
    playback_rate: float = Field(default=1.0, ge=0.5, le=2.0, description="재생 속도")


class ProgressResponse(BaseModel):
    """진행률 응답 모델"""
    saved: bool = Field(..., description="저장 여부")
    total_listened: float = Field(..., description="총 청취 시간 (초)")
    progress_percent: float = Field(..., description="진행률 (%)")


class SeekRequest(BaseModel):
    """탐색 요청 모델"""
    session_id: UUID = Field(..., description="재생 세션 ID")
    position: float = Field(..., ge=0, description="이동할 위치 (초)")
    sentence_id: Optional[UUID] = Field(None, description="문장 ID")


class SeekResponse(BaseModel):
    """탐색 응답 모델"""
    success: bool = Field(..., description="성공 여부")
    new_position: float = Field(..., description="새 위치")
    segment_url: Optional[str] = Field(None, description="세그먼트 URL")


class BookmarkRequest(BaseModel):
    """북마크 요청 모델"""
    script_id: UUID = Field(..., description="스크립트 ID")
    position: float = Field(..., ge=0, description="북마크 위치 (초)")
    note: Optional[str] = Field(None, max_length=500, description="메모")


class BookmarkResponse(BaseModel):
    """북마크 응답 모델"""
    id: UUID = Field(..., description="북마크 ID")
    created_at: datetime = Field(..., description="생성 시간")


class LoopRequest(BaseModel):
    """구간 반복 요청 모델"""
    session_id: UUID = Field(..., description="재생 세션 ID")
    start_position: float = Field(..., ge=0, description="시작 위치 (초)")
    end_position: float = Field(..., gt=0, description="종료 위치 (초)")
    repeat_count: int = Field(default=5, ge=1, le=99, description="반복 횟수")
    
    @validator('end_position')
    def validate_positions(cls, v, values):
        """시작/종료 위치 검증"""
        if 'start_position' in values and v <= values['start_position']:
            raise ValueError('end_position must be greater than start_position')
        return v


class LoopResponse(BaseModel):
    """구간 반복 응답 모델"""
    success: bool = Field(..., description="설정 성공 여부")
    loop_id: UUID = Field(..., description="반복 설정 ID")


class AudioSession(BaseModel):
    """오디오 세션 모델"""
    id: UUID
    user_id: UUID
    script_id: UUID
    started_at: datetime
    last_position: float = 0
    total_duration: Optional[float] = None
    playback_rate: float = 1.0
    is_active: bool = True
    ended_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AudioBookmark(BaseModel):
    """오디오 북마크 모델"""
    id: UUID
    user_id: UUID
    script_id: UUID
    position: float
    note: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AudioError(BaseModel):
    """오디오 에러 모델"""
    error_code: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")
    details: Optional[dict] = Field(None, description="상세 정보") 