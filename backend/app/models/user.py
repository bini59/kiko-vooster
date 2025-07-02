"""
사용자 관련 데이터 모델

사용자 정보, 인증, 프로필 관련 Pydantic 모델들을 정의합니다.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum


class AuthProvider(str, Enum):
    """인증 제공자 열거형"""
    EMAIL = "email"
    GOOGLE = "google"
    APPLE = "apple"


class JapaneseLevel(str, Enum):
    """일본어 레벨 열거형"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# =============================================================================
# 사용자 기본 모델
# =============================================================================

class User(BaseModel):
    """사용자 기본 모델"""
    id: UUID = Field(..., description="사용자 고유 ID")
    email: EmailStr = Field(..., description="이메일 주소")
    name: str = Field(..., description="사용자 이름", min_length=1, max_length=100)
    avatar_url: Optional[str] = Field(None, description="프로필 이미지 URL")
    provider: AuthProvider = Field(AuthProvider.EMAIL, description="인증 제공자")
    provider_id: Optional[str] = Field(None, description="제공자별 사용자 ID")
    is_verified: bool = Field(False, description="이메일 인증 여부")
    japanese_level: JapaneseLevel = Field(JapaneseLevel.BEGINNER, description="일본어 레벨")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="사용자 설정")
    created_at: datetime = Field(..., description="계정 생성일")
    updated_at: datetime = Field(..., description="정보 수정일")
    last_login: Optional[datetime] = Field(None, description="마지막 로그인")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "name": "김영희",
                "avatar_url": "https://example.com/avatar.jpg",
                "provider": "google",
                "provider_id": "google_123456789",
                "is_verified": True,
                "japanese_level": "beginner",
                "preferences": {
                    "theme": "light",
                    "font_size": "medium",
                    "daily_goal_minutes": 30
                }
            }
        }


# =============================================================================
# OAuth 관련 모델
# =============================================================================

class OAuthUserInfo(BaseModel):
    """OAuth 제공자로부터 받은 사용자 정보"""
    provider: AuthProvider = Field(..., description="인증 제공자")
    provider_id: str = Field(..., description="제공자별 사용자 ID")
    email: EmailStr = Field(..., description="이메일 주소")
    name: str = Field(..., description="사용자 이름")
    avatar_url: Optional[str] = Field(None, description="프로필 이미지 URL")
    is_verified: bool = Field(True, description="OAuth 사용자는 기본적으로 인증됨")
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "google",
                "provider_id": "google_123456789",
                "email": "user@gmail.com",
                "name": "김영희",
                "avatar_url": "https://lh3.googleusercontent.com/...",
                "is_verified": True
            }
        }


class GoogleOAuthResponse(BaseModel):
    """Google OAuth 응답 모델"""
    id: str = Field(..., description="Google 사용자 ID")
    email: EmailStr = Field(..., description="이메일 주소")
    name: str = Field(..., description="사용자 이름")
    picture: Optional[str] = Field(None, description="프로필 이미지 URL")
    verified_email: bool = Field(False, description="이메일 인증 여부")


class AppleOAuthResponse(BaseModel):
    """Apple OAuth 응답 모델"""
    sub: str = Field(..., description="Apple 사용자 ID")
    email: Optional[EmailStr] = Field(None, description="이메일 주소")
    name: Optional[str] = Field(None, description="사용자 이름")
    email_verified: Optional[bool] = Field(None, description="이메일 인증 여부")


# =============================================================================
# 인증 요청/응답 모델
# =============================================================================

class OAuthLoginRequest(BaseModel):
    """OAuth 로그인 요청"""
    provider: AuthProvider = Field(..., description="인증 제공자")
    authorization_code: Optional[str] = Field(None, description="OAuth 인증 코드")
    id_token: Optional[str] = Field(None, description="ID 토큰 (Apple용)")
    redirect_uri: Optional[str] = Field(None, description="리다이렉트 URI")
    
    @validator('authorization_code', 'id_token')
    def validate_auth_data(cls, v, values):
        provider = values.get('provider')
        if provider == AuthProvider.GOOGLE and not values.get('authorization_code'):
            raise ValueError('Google 로그인에는 authorization_code가 필요합니다.')
        if provider == AuthProvider.APPLE and not values.get('id_token'):
            raise ValueError('Apple 로그인에는 id_token이 필요합니다.')
        return v


class AuthResponse(BaseModel):
    """인증 성공 응답"""
    access_token: str = Field(..., description="JWT 액세스 토큰")
    token_type: str = Field("bearer", description="토큰 타입")
    expires_in: int = Field(..., description="토큰 만료 시간 (초)")
    user: User = Field(..., description="사용자 정보")
    is_new_user: bool = Field(False, description="신규 사용자 여부")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "user@example.com",
                    "name": "김영희",
                    "provider": "google"
                },
                "is_new_user": False
            }
        }


# =============================================================================
# 프로필 관련 모델
# =============================================================================

class UserProfile(BaseModel):
    """사용자 프로필 모델"""
    id: UUID = Field(..., description="사용자 ID")
    email: EmailStr = Field(..., description="이메일 주소")
    name: str = Field(..., description="사용자 이름")
    avatar_url: Optional[str] = Field(None, description="프로필 이미지 URL")
    japanese_level: JapaneseLevel = Field(..., description="일본어 레벨")
    bio: Optional[str] = Field(None, description="자기소개")
    created_at: datetime = Field(..., description="계정 생성일")
    last_login: Optional[datetime] = Field(None, description="마지막 로그인")

    class Config:
        from_attributes = True


class UpdateProfile(BaseModel):
    """프로필 업데이트 요청"""
    name: Optional[str] = Field(None, description="사용자 이름", min_length=1, max_length=100)
    japanese_level: Optional[JapaneseLevel] = Field(None, description="일본어 레벨")
    bio: Optional[str] = Field(None, description="자기소개", max_length=500)
    avatar_url: Optional[str] = Field(None, description="프로필 이미지 URL")


class UserStats(BaseModel):
    """사용자 학습 통계"""
    total_listening_time: int = Field(0, description="총 청취 시간 (분)")
    words_learned: int = Field(0, description="학습한 단어 수")
    scripts_completed: int = Field(0, description="완료한 스크립트 수")
    current_streak: int = Field(0, description="현재 연속 학습 일수")
    level_progress: float = Field(0.0, description="레벨 진행률 (0-100)")
    last_activity: Optional[datetime] = Field(None, description="마지막 활동일")

    class Config:
        json_schema_extra = {
            "example": {
                "total_listening_time": 120,
                "words_learned": 45,
                "scripts_completed": 3,
                "current_streak": 5,
                "level_progress": 23.5,
                "last_activity": "2024-01-15T10:30:00Z"
            }
        }


class UserPreferences(BaseModel):
    """사용자 설정"""
    theme: str = Field("light", description="테마 (light, dark)")
    font_size: str = Field("medium", description="폰트 크기 (small, medium, large)")
    auto_play: bool = Field(True, description="자동 재생")
    repeat_mode: str = Field("sentence", description="반복 모드 (none, sentence, word)")
    daily_goal_minutes: int = Field(30, description="일일 학습 목표 (분)", ge=5, le=300)
    notifications: Dict[str, bool] = Field(
        default_factory=lambda: {"email": True, "web_push": False},
        description="알림 설정"
    )

    @validator('theme')
    def validate_theme(cls, v):
        if v not in ['light', 'dark', 'auto']:
            raise ValueError('테마는 light, dark, auto 중 하나여야 합니다.')
        return v

    @validator('font_size')
    def validate_font_size(cls, v):
        if v not in ['small', 'medium', 'large']:
            raise ValueError('폰트 크기는 small, medium, large 중 하나여야 합니다.')
        return v

    @validator('repeat_mode')
    def validate_repeat_mode(cls, v):
        if v not in ['none', 'sentence', 'word']:
            raise ValueError('반복 모드는 none, sentence, word 중 하나여야 합니다.')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "theme": "light",
                "font_size": "medium",
                "auto_play": True,
                "repeat_mode": "sentence",
                "daily_goal_minutes": 30,
                "notifications": {
                    "email": True,
                    "web_push": False
                }
            }
        } 