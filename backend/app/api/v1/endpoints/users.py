"""
사용자 관련 API 엔드포인트

사용자 프로필 관리, 학습 통계, 설정 등을 담당합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from datetime import datetime
import logging

from app.core.auth import get_current_user
from app.models.user import (
    User, UserProfile, UpdateProfile, UserStats, UserPreferences
)
from app.services.users.user_service import user_service

logger = logging.getLogger(__name__)

router = APIRouter()

# =============================================================================
# 사용자 프로필 관리 엔드포인트
# =============================================================================

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    사용자 프로필 조회
    
    현재 로그인한 사용자의 프로필 정보를 반환합니다.
    """
    try:
        profile = await user_service.get_user_profile(current_user.id)
        
        if not profile:
            logger.error(f"❌ 사용자 프로필 조회 실패: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="프로필을 찾을 수 없습니다."
            )
        
        logger.info(f"✅ 프로필 조회 성공: {current_user.email}")
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 프로필 조회 중 서버 에러: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="프로필 조회 중 오류가 발생했습니다."
        )

@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    profile_data: UpdateProfile,
    current_user: User = Depends(get_current_user)
):
    """
    사용자 프로필 업데이트
    
    사용자 프로필 정보를 수정합니다.
    """
    try:
        updated_profile = await user_service.update_user_profile(
            current_user.id, profile_data
        )
        
        if not updated_profile:
            logger.error(f"❌ 프로필 업데이트 실패: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="프로필 업데이트에 실패했습니다."
            )
        
        logger.info(f"✅ 프로필 업데이트 성공: {current_user.email}")
        return updated_profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 프로필 업데이트 중 서버 에러: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="프로필 업데이트 중 오류가 발생했습니다."
        )

# =============================================================================
# 사용자 학습 통계 엔드포인트
# =============================================================================

@router.get("/stats", response_model=UserStats)
async def get_user_stats(current_user: User = Depends(get_current_user)):
    """
    사용자 학습 통계 조회
    
    총 청취 시간, 학습 단어 수, 연속 학습 일수 등을 반환합니다.
    """
    try:
        stats = await user_service.get_user_stats(current_user.id)
        
        logger.info(f"✅ 학습 통계 조회 성공: {current_user.email}")
        return stats
        
    except Exception as e:
        logger.error(f"❌ 학습 통계 조회 중 서버 에러: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="학습 통계 조회 중 오류가 발생했습니다."
        )


# =============================================================================
# 사용자 설정 관리 엔드포인트
# =============================================================================

@router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences(current_user: User = Depends(get_current_user)):
    """
    사용자 설정 조회
    
    테마, 폰트 크기, 자동 재생 등의 사용자 설정을 반환합니다.
    """
    try:
        preferences = await user_service.get_user_preferences(current_user.id)
        
        if not preferences:
            logger.error(f"❌ 사용자 설정 조회 실패: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자 설정을 찾을 수 없습니다."
            )
        
        logger.info(f"✅ 사용자 설정 조회 성공: {current_user.email}")
        return preferences
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 사용자 설정 조회 중 서버 에러: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 설정 조회 중 오류가 발생했습니다."
        )

@router.put("/preferences", response_model=UserPreferences)
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: User = Depends(get_current_user)
):
    """
    사용자 설정 업데이트
    
    사용자의 학습 설정을 수정합니다.
    """
    try:
        updated_preferences = await user_service.update_user_preferences(
            current_user.id, preferences
        )
        
        if not updated_preferences:
            logger.error(f"❌ 사용자 설정 업데이트 실패: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="사용자 설정 업데이트에 실패했습니다."
            )
        
        logger.info(f"✅ 사용자 설정 업데이트 성공: {current_user.email}")
        return updated_preferences
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 사용자 설정 업데이트 중 서버 에러: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 설정 업데이트 중 오류가 발생했습니다."
        )

# =============================================================================
# 학습 진행상황 엔드포인트
# =============================================================================

@router.get("/progress")
async def get_learning_progress(current_user: User = Depends(get_current_user)):
    """
    학습 진행상황 조회
    
    최근 학습 기록과 진행률을 반환합니다.
    """
    try:
        # TODO: 실제 학습 기록 데이터를 DB에서 조회하도록 구현
        
        # 임시 진행상황 데이터 (개발 단계)
        progress_data = {
            "recent_activities": [
                {
                    "type": "script_completed",
                    "title": "NHK 뉴스 - 날씨 예보",
                    "completed_at": datetime.utcnow().isoformat(),
                    "duration_minutes": 15
                },
                {
                    "type": "word_learned",
                    "word": "天気",
                    "meaning": "날씨",
                    "learned_at": datetime.utcnow().isoformat()
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
        
        logger.info(f"✅ 학습 진행상황 조회 성공: {current_user.email}")
        return progress_data
        
    except Exception as e:
        logger.error(f"❌ 학습 진행상황 조회 중 서버 에러: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="학습 진행상황 조회 중 오류가 발생했습니다."
        )


# =============================================================================
# 계정 관리 엔드포인트
# =============================================================================

@router.delete("/account")
async def delete_user_account(current_user: User = Depends(get_current_user)):
    """
    계정 삭제
    
    사용자 계정과 모든 관련 데이터를 삭제합니다.
    """
    try:
        # TODO: 실제 계정 삭제 로직 구현 (GDPR 준수)
        # 1. 사용자 데이터 백업
        # 2. 관련 테이블에서 데이터 삭제
        # 3. 계정 비활성화 또는 삭제
        
        logger.warning(f"⚠️ 계정 삭제 요청: {current_user.email}")
        
        return {
            "message": "계정 삭제 요청이 접수되었습니다. 24시간 내에 처리됩니다.",
            "user_id": str(current_user.id),
            "requested_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 계정 삭제 요청 중 서버 에러: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="계정 삭제 요청 중 오류가 발생했습니다."
        ) 