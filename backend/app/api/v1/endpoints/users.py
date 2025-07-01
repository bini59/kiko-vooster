"""
사용자 관련 API 엔드포인트

사용자 프로필 관리, 학습 통계 등을 담당합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.api.v1.endpoints.auth import oauth2_scheme

router = APIRouter()

# 모델 정의
class UserStats(BaseModel):
    """사용자 학습 통계 모델"""
    total_listening_time: int  # 총 청취 시간 (분)
    words_learned: int         # 학습한 단어 수
    scripts_completed: int     # 완료한 스크립트 수
    current_streak: int        # 현재 연속 학습 일수
    level_progress: float      # 레벨 진행률 (0-100)

class UserPreferences(BaseModel):
    """사용자 설정 모델"""
    theme: str = "light"                    # light, dark
    font_size: str = "medium"               # small, medium, large
    auto_play: bool = True                  # 자동 재생
    repeat_mode: str = "sentence"           # none, sentence, word
    japanese_level: str = "beginner"        # beginner, intermediate, advanced
    daily_goal_minutes: int = 30            # 일일 학습 목표 (분)

class UpdateProfile(BaseModel):
    """프로필 업데이트 요청 모델"""
    name: Optional[str] = None
    japanese_level: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

@router.get("/profile")
async def get_user_profile(token: str = Depends(oauth2_scheme)):
    """
    사용자 프로필 조회
    
    현재 로그인한 사용자의 프로필 정보를 반환합니다.
    """
    # TODO: JWT에서 사용자 ID 추출 및 실제 DB 조회
    
    # 임시 데이터 (개발 단계)
    return {
        "id": "user_123",
        "email": "test@example.com",
        "name": "테스트 사용자",
        "bio": "일본어 학습에 열정적인 학습자입니다.",
        "avatar_url": None,
        "japanese_level": "beginner",
        "created_at": datetime.utcnow(),
        "last_login": datetime.utcnow()
    }

@router.put("/profile")
async def update_user_profile(
    profile_data: UpdateProfile,
    token: str = Depends(oauth2_scheme)
):
    """
    사용자 프로필 업데이트
    
    사용자 프로필 정보를 수정합니다.
    """
    # TODO: JWT에서 사용자 ID 추출 및 실제 DB 업데이트
    
    return {
        "message": "프로필이 성공적으로 업데이트되었습니다.",
        "updated_fields": profile_data.dict(exclude_unset=True)
    }

@router.get("/stats", response_model=UserStats)
async def get_user_stats(token: str = Depends(oauth2_scheme)):
    """
    사용자 학습 통계 조회
    
    총 청취 시간, 학습한 단어 수 등의 통계를 반환합니다.
    """
    # TODO: 실제 DB에서 통계 데이터 조회
    
    # 임시 통계 데이터 (개발 단계)
    return UserStats(
        total_listening_time=120,  # 2시간
        words_learned=45,
        scripts_completed=3,
        current_streak=5,
        level_progress=23.5
    )

@router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences(token: str = Depends(oauth2_scheme)):
    """
    사용자 설정 조회
    
    테마, 폰트 크기, 자동 재생 등의 설정을 반환합니다.
    """
    # TODO: 실제 DB에서 사용자 설정 조회
    
    # 기본 설정 반환 (개발 단계)
    return UserPreferences()

@router.put("/preferences")
async def update_user_preferences(
    preferences: UserPreferences,
    token: str = Depends(oauth2_scheme)
):
    """
    사용자 설정 업데이트
    
    사용자의 앱 설정을 저장합니다.
    """
    # TODO: 실제 DB에 설정 저장
    
    return {
        "message": "설정이 성공적으로 업데이트되었습니다.",
        "preferences": preferences.dict()
    }

@router.get("/progress")
async def get_learning_progress(token: str = Depends(oauth2_scheme)):
    """
    학습 진행상황 조회
    
    최근 학습 기록과 진행률을 반환합니다.
    """
    # TODO: 실제 학습 기록 데이터 조회
    
    # 임시 진행상황 데이터 (개발 단계)
    return {
        "recent_activities": [
            {
                "type": "script_completed",
                "title": "NHK 뉴스 - 날씨 예보",
                "completed_at": datetime.utcnow(),
                "duration_minutes": 15
            },
            {
                "type": "word_learned",
                "word": "天気",
                "meaning": "날씨",
                "learned_at": datetime.utcnow()
            }
        ],
        "weekly_progress": {
            "goal_minutes": 210,      # 주간 목표 (30분 × 7일)
            "completed_minutes": 85,  # 완료한 시간
            "completion_rate": 40.5   # 달성률
        },
        "streaks": {
            "current": 5,
            "longest": 12
        }
    }

@router.delete("/account")
async def delete_user_account(token: str = Depends(oauth2_scheme)):
    """
    계정 삭제
    
    사용자 계정과 모든 관련 데이터를 삭제합니다.
    """
    # TODO: 실제 계정 삭제 로직 (GDPR 준수)
    
    return {
        "message": "계정 삭제 요청이 접수되었습니다. 24시간 내에 처리됩니다."
    } 