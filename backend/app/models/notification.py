"""
알림 관련 데이터 모델

학습 리마인더, 웹푸시, 이메일 알림 관련 Pydantic 모델들을 정의합니다.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, time
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum


# =============================================================================
# 열거형 정의
# =============================================================================

class NotificationType(str, Enum):
    """알림 유형 열거형"""
    LEARNING_REMINDER = "learning_reminder"
    ACHIEVEMENT = "achievement"
    VOCABULARY_REVIEW = "vocabulary_review"
    STREAK_REMINDER = "streak_reminder"
    SYSTEM_ANNOUNCEMENT = "system_announcement"


class NotificationChannel(str, Enum):
    """알림 채널 열거형"""
    EMAIL = "email"
    WEB_PUSH = "web_push"
    IN_APP = "in_app"


class NotificationStatus(str, Enum):
    """알림 상태 열거형"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduleFrequency(str, Enum):
    """스케줄 빈도 열거형"""
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class DeviceType(str, Enum):
    """디바이스 유형 열거형"""
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"


# =============================================================================
# 알림 기본 모델
# =============================================================================

class Notification(BaseModel):
    """개별 알림 모델"""
    id: UUID = Field(..., description="알림 고유 ID")
    user_id: UUID = Field(..., description="사용자 ID")
    type: NotificationType = Field(..., description="알림 유형")
    channel: NotificationChannel = Field(..., description="발송 채널")
    title: str = Field(..., description="알림 제목", min_length=1, max_length=200)
    message: str = Field(..., description="알림 메시지")
    action_url: Optional[str] = Field(None, description="클릭 시 이동할 URL")
    template_variables: Dict[str, Any] = Field(default_factory=dict, description="템플릿 변수")
    status: NotificationStatus = Field(NotificationStatus.PENDING, description="발송 상태")
    sent_at: Optional[datetime] = Field(None, description="발송 시간")
    delivered_at: Optional[datetime] = Field(None, description="전달 시간")
    opened_at: Optional[datetime] = Field(None, description="읽음 시간")
    retry_count: int = Field(0, description="재시도 횟수", ge=0)
    max_retries: int = Field(3, description="최대 재시도 횟수", ge=0)
    failure_reason: Optional[str] = Field(None, description="실패 사유")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "type": "learning_reminder",
                "channel": "web_push",
                "title": "일본어 학습 시간이에요! 🌸",
                "message": "김영희님, 오늘 30분 학습 목표를 달성해보세요!",
                "action_url": "https://app.kiko.com/study",
                "template_variables": {
                    "user_name": "김영희",
                    "target_minutes": 30
                },
                "status": "sent"
            }
        }


class NotificationCreate(BaseModel):
    """알림 생성 요청 모델"""
    user_id: UUID = Field(..., description="사용자 ID")
    type: NotificationType = Field(..., description="알림 유형")
    channel: NotificationChannel = Field(..., description="발송 채널")
    title: str = Field(..., description="알림 제목", min_length=1, max_length=200)
    message: str = Field(..., description="알림 메시지")
    action_url: Optional[str] = Field(None, description="클릭 시 이동할 URL")
    template_variables: Dict[str, Any] = Field(default_factory=dict, description="템플릿 변수")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")

    @validator('action_url')
    def validate_action_url(cls, v):
        if v and not v.startswith(('http://', 'https://', '/')):
            raise ValueError('올바른 URL 형식이 아닙니다.')
        return v


class NotificationUpdate(BaseModel):
    """알림 업데이트 모델"""
    status: Optional[NotificationStatus] = Field(None, description="상태 업데이트")
    failure_reason: Optional[str] = Field(None, description="실패 사유")


# =============================================================================
# 알림 스케줄 모델
# =============================================================================

class NotificationSchedule(BaseModel):
    """알림 스케줄 모델"""
    id: UUID = Field(..., description="스케줄 고유 ID")
    user_id: UUID = Field(..., description="사용자 ID")
    type: NotificationType = Field(..., description="알림 유형")
    name: str = Field(..., description="스케줄 이름", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="스케줄 설명")
    is_enabled: bool = Field(True, description="활성화 여부")
    frequency: ScheduleFrequency = Field(..., description="빈도")
    preferred_time: time = Field(..., description="선호 시간")
    timezone: str = Field("Asia/Seoul", description="타임존")
    days_of_week: List[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5], description="요일 (1=월요일)")
    custom_interval_hours: Optional[int] = Field(None, description="커스텀 간격 (시간)", ge=1, le=168)
    next_execution: Optional[datetime] = Field(None, description="다음 실행 시간")
    last_executed: Optional[datetime] = Field(None, description="마지막 실행 시간")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="실행 조건")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")

    @validator('days_of_week')
    def validate_days_of_week(cls, v):
        if not all(1 <= day <= 7 for day in v):
            raise ValueError('요일은 1(월요일)부터 7(일요일) 사이의 값이어야 합니다.')
        return v

    @validator('timezone')
    def validate_timezone(cls, v):
        import pytz
        try:
            pytz.timezone(v)
        except pytz.UnknownTimeZoneError:
            raise ValueError('올바른 타임존이 아닙니다.')
        return v

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "type": "learning_reminder",
                "name": "일일 학습 리마인더",
                "description": "매일 오전 9시에 학습 리마인더 알림",
                "is_enabled": True,
                "frequency": "daily",
                "preferred_time": "09:00:00",
                "timezone": "Asia/Seoul",
                "days_of_week": [1, 2, 3, 4, 5]
            }
        }


class NotificationScheduleCreate(BaseModel):
    """알림 스케줄 생성 모델"""
    type: NotificationType = Field(..., description="알림 유형")
    name: str = Field(..., description="스케줄 이름", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="스케줄 설명")
    is_enabled: bool = Field(True, description="활성화 여부")
    frequency: ScheduleFrequency = Field(..., description="빈도")
    preferred_time: time = Field(..., description="선호 시간")
    timezone: str = Field("Asia/Seoul", description="타임존")
    days_of_week: List[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5], description="요일")
    custom_interval_hours: Optional[int] = Field(None, description="커스텀 간격 (시간)", ge=1, le=168)
    conditions: Dict[str, Any] = Field(default_factory=dict, description="실행 조건")

    @validator('days_of_week')
    def validate_days_of_week(cls, v):
        if not all(1 <= day <= 7 for day in v):
            raise ValueError('요일은 1(월요일)부터 7(일요일) 사이의 값이어야 합니다.')
        return v


class NotificationScheduleUpdate(BaseModel):
    """알림 스케줄 업데이트 모델"""
    name: Optional[str] = Field(None, description="스케줄 이름", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="스케줄 설명")
    is_enabled: Optional[bool] = Field(None, description="활성화 여부")
    frequency: Optional[ScheduleFrequency] = Field(None, description="빈도")
    preferred_time: Optional[time] = Field(None, description="선호 시간")
    timezone: Optional[str] = Field(None, description="타임존")
    days_of_week: Optional[List[int]] = Field(None, description="요일")
    custom_interval_hours: Optional[int] = Field(None, description="커스텀 간격 (시간)", ge=1, le=168)
    conditions: Optional[Dict[str, Any]] = Field(None, description="실행 조건")


# =============================================================================
# 웹푸시 구독 모델
# =============================================================================

class NotificationSubscription(BaseModel):
    """웹푸시 구독 모델"""
    id: UUID = Field(..., description="구독 고유 ID")
    user_id: UUID = Field(..., description="사용자 ID")
    endpoint: str = Field(..., description="Push service endpoint")
    p256dh_key: str = Field(..., description="공개키")
    auth_key: str = Field(..., description="인증키")
    user_agent: Optional[str] = Field(None, description="User Agent")
    browser_name: Optional[str] = Field(None, description="브라우저 이름")
    browser_version: Optional[str] = Field(None, description="브라우저 버전")
    device_type: Optional[DeviceType] = Field(None, description="디바이스 유형")
    is_active: bool = Field(True, description="활성화 여부")
    notification_types: List[str] = Field(default_factory=list, description="구독할 알림 유형들")
    permission_granted_at: datetime = Field(..., description="권한 허용 시간")
    last_used_at: datetime = Field(..., description="마지막 사용 시간")
    error_count: int = Field(0, description="에러 횟수", ge=0)
    last_error: Optional[str] = Field(None, description="마지막 에러")
    last_error_at: Optional[datetime] = Field(None, description="마지막 에러 시간")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")

    class Config:
        from_attributes = True


class NotificationSubscriptionCreate(BaseModel):
    """웹푸시 구독 생성 모델"""
    endpoint: str = Field(..., description="Push service endpoint")
    p256dh_key: str = Field(..., description="공개키")
    auth_key: str = Field(..., description="인증키")
    user_agent: Optional[str] = Field(None, description="User Agent")
    browser_name: Optional[str] = Field(None, description="브라우저 이름")
    browser_version: Optional[str] = Field(None, description="브라우저 버전")
    device_type: Optional[DeviceType] = Field(None, description="디바이스 유형")
    notification_types: List[str] = Field(default_factory=lambda: ["learning_reminder", "vocabulary_review"], description="구독할 알림 유형들")

    @validator('endpoint')
    def validate_endpoint(cls, v):
        if not v.startswith('https://'):
            raise ValueError('Push endpoint는 HTTPS URL이어야 합니다.')
        return v


class NotificationSubscriptionUpdate(BaseModel):
    """웹푸시 구독 업데이트 모델"""
    is_active: Optional[bool] = Field(None, description="활성화 여부")
    notification_types: Optional[List[str]] = Field(None, description="구독할 알림 유형들")


# =============================================================================
# 알림 템플릿 모델
# =============================================================================

class NotificationTemplate(BaseModel):
    """알림 템플릿 모델"""
    id: UUID = Field(..., description="템플릿 고유 ID")
    type: str = Field(..., description="알림 유형")
    channel: NotificationChannel = Field(..., description="채널")
    name: str = Field(..., description="템플릿 이름")
    description: Optional[str] = Field(None, description="템플릿 설명")
    subject_template: Optional[str] = Field(None, description="제목 템플릿")
    title_template: str = Field(..., description="타이틀 템플릿")
    message_template: str = Field(..., description="메시지 템플릿")
    action_button_text: Optional[str] = Field(None, description="액션 버튼 텍스트")
    action_url_template: Optional[str] = Field(None, description="액션 URL 템플릿")
    is_active: bool = Field(True, description="활성화 여부")
    language: str = Field("ko", description="언어")
    version: int = Field(1, description="버전")
    ab_test_group: Optional[str] = Field(None, description="A/B 테스트 그룹")
    traffic_percentage: int = Field(100, description="트래픽 비율", ge=0, le=100)
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")

    class Config:
        from_attributes = True


# =============================================================================
# 응답 모델
# =============================================================================

class NotificationListResponse(BaseModel):
    """알림 목록 응답 모델"""
    notifications: List[Notification] = Field(..., description="알림 목록")
    total: int = Field(..., description="전체 개수")
    page: int = Field(..., description="현재 페이지")
    size: int = Field(..., description="페이지 크기")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")


class NotificationStatsResponse(BaseModel):
    """알림 통계 응답 모델"""
    total_sent: int = Field(..., description="총 발송 수")
    total_delivered: int = Field(..., description="총 전달 수")
    total_opened: int = Field(..., description="총 읽음 수")
    delivery_rate: float = Field(..., description="전달률 (%)")
    open_rate: float = Field(..., description="읽음률 (%)")
    last_30_days: Dict[str, int] = Field(..., description="최근 30일 통계")


# =============================================================================
# 웹푸시 페이로드 모델
# =============================================================================

class WebPushPayload(BaseModel):
    """웹푸시 페이로드 모델"""
    title: str = Field(..., description="알림 제목")
    body: str = Field(..., description="알림 내용")
    icon: Optional[str] = Field(None, description="아이콘 URL")
    badge: Optional[str] = Field(None, description="배지 URL")
    image: Optional[str] = Field(None, description="이미지 URL")
    tag: Optional[str] = Field(None, description="알림 태그")
    url: Optional[str] = Field(None, description="클릭 시 이동할 URL")
    actions: Optional[List[Dict[str, str]]] = Field(None, description="액션 버튼들")
    silent: bool = Field(False, description="무음 알림 여부")
    timestamp: Optional[int] = Field(None, description="타임스탬프")
    data: Optional[Dict[str, Any]] = Field(None, description="추가 데이터")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "일본어 학습 시간이에요! 🌸",
                "body": "김영희님, 오늘 30분 학습 목표를 달성해보세요!",
                "icon": "/icons/notification-icon.png",
                "badge": "/icons/badge-icon.png",
                "url": "/study",
                "tag": "learning_reminder",
                "actions": [
                    {"action": "start", "title": "지금 시작"},
                    {"action": "later", "title": "나중에"}
                ]
            }
        } 