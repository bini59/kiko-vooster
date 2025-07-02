"""
사용자 관리 서비스

사용자 프로필, 통계, 설정 관리를 담당합니다.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from uuid import UUID

from app.core.database import get_database
from app.models.user import (
    User, UserProfile, UpdateProfile, UserStats, UserPreferences,
    JapaneseLevel
)

logger = logging.getLogger(__name__)


class UserService:
    """사용자 관리 서비스"""

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        ID로 사용자 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            User: 사용자 정보 또는 None
        """
        try:
            db = await get_database()
            
            result = await db.client.from_("users")\
                .select("*")\
                .eq("id", str(user_id))\
                .single()\
                .execute()
            
            if result.data:
                return User(**result.data)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 사용자 조회 실패 (ID: {user_id}): {str(e)}")
            return None

    async def get_user_profile(self, user_id: UUID) -> Optional[UserProfile]:
        """
        사용자 프로필 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            UserProfile: 사용자 프로필 또는 None
        """
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return None
            
            # User 모델에서 UserProfile로 변환
            profile_data = {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "avatar_url": user.avatar_url,
                "japanese_level": user.japanese_level,
                "bio": user.preferences.get("bio"),  # preferences에서 bio 추출
                "created_at": user.created_at,
                "last_login": user.last_login
            }
            
            return UserProfile(**profile_data)
            
        except Exception as e:
            logger.error(f"❌ 사용자 프로필 조회 실패 (ID: {user_id}): {str(e)}")
            return None

    async def update_user_profile(self, user_id: UUID, profile_data: UpdateProfile) -> Optional[UserProfile]:
        """
        사용자 프로필 업데이트
        
        Args:
            user_id: 사용자 ID
            profile_data: 업데이트할 프로필 데이터
            
        Returns:
            UserProfile: 업데이트된 프로필 또는 None
        """
        try:
            db = await get_database()
            
            # 업데이트할 필드만 포함
            update_fields = {}
            if profile_data.name is not None:
                update_fields["name"] = profile_data.name
            if profile_data.japanese_level is not None:
                update_fields["japanese_level"] = profile_data.japanese_level.value
            if profile_data.avatar_url is not None:
                update_fields["avatar_url"] = profile_data.avatar_url
                
            # bio는 preferences에 저장
            if profile_data.bio is not None:
                # 기존 preferences 조회
                user = await self.get_user_by_id(user_id)
                if user:
                    preferences = user.preferences.copy()
                    preferences["bio"] = profile_data.bio
                    update_fields["preferences"] = preferences
            
            if not update_fields:
                # 업데이트할 필드가 없으면 기존 프로필 반환
                return await self.get_user_profile(user_id)
            
            # updated_at 추가
            update_fields["updated_at"] = datetime.utcnow().isoformat()
            
            # 데이터베이스 업데이트
            result = await db.client.from_("users")\
                .update(update_fields)\
                .eq("id", str(user_id))\
                .execute()
            
            if not result.data:
                logger.error(f"❌ 프로필 업데이트 실패: 업데이트된 데이터가 없음")
                return None
            
            # 업데이트된 프로필 반환
            return await self.get_user_profile(user_id)
            
        except Exception as e:
            logger.error(f"❌ 사용자 프로필 업데이트 실패 (ID: {user_id}): {str(e)}")
            return None

    async def get_user_stats(self, user_id: UUID) -> UserStats:
        """
        사용자 학습 통계 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            UserStats: 사용자 학습 통계
        """
        try:
            db = await get_database()
            
            # 1. 총 청취 시간 계산
            total_listening_time = await self._calculate_listening_time(user_id)
            
            # 2. 학습한 단어 수 계산
            words_learned = await self._calculate_words_learned(user_id)
            
            # 3. 완료한 스크립트 수 계산
            scripts_completed = await self._calculate_scripts_completed(user_id)
            
            # 4. 연속 학습 일수 계산
            current_streak = await self._calculate_current_streak(user_id)
            
            # 5. 레벨 진행률 계산
            level_progress = await self._calculate_level_progress(user_id)
            
            # 6. 마지막 활동일 조회
            last_activity = await self._get_last_activity(user_id)
            
            return UserStats(
                total_listening_time=total_listening_time,
                words_learned=words_learned,
                scripts_completed=scripts_completed,
                current_streak=current_streak,
                level_progress=level_progress,
                last_activity=last_activity
            )
            
        except Exception as e:
            logger.error(f"❌ 사용자 통계 조회 실패 (ID: {user_id}): {str(e)}")
            return UserStats()  # 기본값 반환

    async def get_user_preferences(self, user_id: UUID) -> Optional[UserPreferences]:
        """
        사용자 설정 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            UserPreferences: 사용자 설정 또는 None
        """
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return None
            
            # 기본값과 사용자 설정을 병합
            preferences_data = {
                "theme": user.preferences.get("theme", "light"),
                "font_size": user.preferences.get("font_size", "medium"),
                "auto_play": user.preferences.get("auto_play", True),
                "repeat_mode": user.preferences.get("repeat_mode", "sentence"),
                "daily_goal_minutes": user.preferences.get("daily_goal_minutes", 30),
                "notifications": user.preferences.get("notifications", {"email": True, "web_push": False})
            }
            
            return UserPreferences(**preferences_data)
            
        except Exception as e:
            logger.error(f"❌ 사용자 설정 조회 실패 (ID: {user_id}): {str(e)}")
            return None

    async def update_user_preferences(self, user_id: UUID, preferences: UserPreferences) -> Optional[UserPreferences]:
        """
        사용자 설정 업데이트
        
        Args:
            user_id: 사용자 ID
            preferences: 새로운 설정
            
        Returns:
            UserPreferences: 업데이트된 설정 또는 None
        """
        try:
            db = await get_database()
            
            # 기존 preferences와 새 설정 병합
            user = await self.get_user_by_id(user_id)
            if not user:
                return None
            
            current_preferences = user.preferences.copy()
            new_preferences = preferences.dict()
            
            # 새 설정으로 업데이트
            current_preferences.update(new_preferences)
            
            # 데이터베이스 업데이트
            result = await db.client.from_("users")\
                .update({
                    "preferences": current_preferences,
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("id", str(user_id))\
                .execute()
            
            if not result.data:
                return None
            
            return preferences
            
        except Exception as e:
            logger.error(f"❌ 사용자 설정 업데이트 실패 (ID: {user_id}): {str(e)}")
            return None

    # =========================================================================
    # 통계 계산 헬퍼 메서드들
    # =========================================================================

    async def _calculate_listening_time(self, user_id: UUID) -> int:
        """총 청취 시간 계산 (분)"""
        try:
            db = await get_database()
            
            # user_scripts_progress 테이블에서 재생 시간 합계 계산
            result = await db.client.from_("user_scripts_progress")\
                .select("current_time")\
                .eq("user_id", str(user_id))\
                .execute()
            
            if result.data:
                total_seconds = sum(row.get("current_time", 0) for row in result.data)
                return int(total_seconds // 60)  # 분 단위로 변환
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ 청취 시간 계산 실패: {str(e)}")
            return 0

    async def _calculate_words_learned(self, user_id: UUID) -> int:
        """학습한 단어 수 계산"""
        try:
            db = await get_database()
            
            # user_words 테이블에서 단어 수 계산
            result = await db.client.from_("user_words")\
                .select("id", count="exact")\
                .eq("user_id", str(user_id))\
                .execute()
            
            return result.count or 0
            
        except Exception as e:
            logger.error(f"❌ 학습 단어 수 계산 실패: {str(e)}")
            return 0

    async def _calculate_scripts_completed(self, user_id: UUID) -> int:
        """완료한 스크립트 수 계산"""
        try:
            db = await get_database()
            
            # user_scripts_progress 테이블에서 완료된 스크립트 수 계산
            result = await db.client.from_("user_scripts_progress")\
                .select("id", count="exact")\
                .eq("user_id", str(user_id))\
                .eq("completed", True)\
                .execute()
            
            return result.count or 0
            
        except Exception as e:
            logger.error(f"❌ 완료 스크립트 수 계산 실패: {str(e)}")
            return 0

    async def _calculate_current_streak(self, user_id: UUID) -> int:
        """현재 연속 학습 일수 계산"""
        try:
            db = await get_database()
            
            # 최근 7일간의 학습 활동 조회
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            
            result = await db.client.from_("user_scripts_progress")\
                .select("last_played")\
                .eq("user_id", str(user_id))\
                .gte("last_played", seven_days_ago.isoformat())\
                .order("last_played", desc=True)\
                .execute()
            
            if not result.data:
                return 0
            
            # 연속 일수 계산 로직 (간단한 구현)
            unique_dates = set()
            for row in result.data:
                if row.get("last_played"):
                    date_only = datetime.fromisoformat(row["last_played"]).date()
                    unique_dates.add(date_only)
            
            # 오늘부터 역순으로 연속 일수 확인
            today = datetime.utcnow().date()
            streak = 0
            current_date = today
            
            while current_date in unique_dates:
                streak += 1
                current_date -= timedelta(days=1)
                if streak >= 7:  # 최대 7일로 제한
                    break
            
            return streak
            
        except Exception as e:
            logger.error(f"❌ 연속 학습 일수 계산 실패: {str(e)}")
            return 0

    async def _calculate_level_progress(self, user_id: UUID) -> float:
        """레벨 진행률 계산 (0-100)"""
        try:
            # 간단한 진행률 계산: 학습한 단어 수 기반
            words_learned = await self._calculate_words_learned(user_id)
            
            # 레벨별 목표 단어 수
            level_targets = {
                "beginner": 100,     # 초급: 100개
                "intermediate": 500, # 중급: 500개
                "advanced": 1000     # 고급: 1000개
            }
            
            user = await self.get_user_by_id(user_id)
            if not user:
                return 0.0
            
            target = level_targets.get(user.japanese_level.value, 100)
            progress = (words_learned / target) * 100
            
            return min(progress, 100.0)  # 최대 100%
            
        except Exception as e:
            logger.error(f"❌ 레벨 진행률 계산 실패: {str(e)}")
            return 0.0

    async def _get_last_activity(self, user_id: UUID) -> Optional[datetime]:
        """마지막 활동일 조회"""
        try:
            db = await get_database()
            
            # user_scripts_progress에서 가장 최근 활동 조회
            result = await db.client.from_("user_scripts_progress")\
                .select("last_played")\
                .eq("user_id", str(user_id))\
                .order("last_played", desc=True)\
                .limit(1)\
                .execute()
            
            if result.data and result.data[0].get("last_played"):
                return datetime.fromisoformat(result.data[0]["last_played"])
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 마지막 활동일 조회 실패: {str(e)}")
            return None


# 싱글톤 인스턴스
user_service = UserService() 