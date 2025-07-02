"""
복습 관리 서비스

간격 반복 학습법(Spaced Repetition) 기반의 복습 시스템을 담당합니다.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from app.core.database import DatabaseManager

logger = logging.getLogger(__name__)


class ReviewService:
    """복습 시스템 관리 서비스"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def get_review_words(
        self,
        user_id: str,
        count: int = 10,
        mode: str = "mixed"
    ) -> Dict[str, Any]:
        """
        복습할 단어 목록 조회
        
        Args:
            user_id: 사용자 ID
            count: 복습할 단어 개수
            mode: 복습 모드 (new, review, mixed)
            
        Returns:
            복습 단어 목록
        """
        try:
            words = []
            
            if mode == "new":
                # 새로운 단어들만 (mastery_level = 0)
                words = await self._get_new_words(user_id, count)
            elif mode == "review":
                # 복습 필요한 단어들만
                words = await self._get_due_words(user_id, count)
            else:  # mixed
                # 복습 필요한 단어 우선, 나머지는 새 단어로 채움
                due_words = await self._get_due_words(user_id, count // 2)
                remaining_count = count - len(due_words)
                
                if remaining_count > 0:
                    new_words = await self._get_new_words(user_id, remaining_count)
                    words = due_words + new_words
                else:
                    words = due_words[:count]
            
            # 전체 복습 예정 단어 수 계산
            total_due = await self._count_due_words(user_id)
            
            logger.info(f"✅ 복습 단어 조회 성공: {user_id}, {len(words)}개")
            
            return {
                "words": words,
                "total_due": total_due,
                "mode": mode,
                "user_id": user_id,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 복습 단어 조회 실패: {str(e)}")
            raise
    
    async def submit_review_result(
        self,
        user_id: str,
        word_id: str,
        correct: bool,
        response_time: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        복습 결과 제출 및 숙련도 업데이트
        
        Args:
            user_id: 사용자 ID
            word_id: 단어 ID
            correct: 정답 여부
            response_time: 응답 시간 (초)
            
        Returns:
            업데이트된 단어 정보
        """
        try:
            # 기존 user_word 조회
            user_word = await self._get_user_word(user_id, word_id)
            if not user_word:
                raise ValueError("해당 단어를 단어장에서 찾을 수 없습니다")
            
            current_mastery = user_word.get("mastery_level", 0)
            review_count = user_word.get("review_count", 0)
            
            # 숙련도 업데이트 알고리즘
            new_mastery_level = self._calculate_new_mastery_level(
                current_mastery, correct, response_time
            )
            
            # 다음 복습 날짜 계산 (DB 트리거에서도 계산되지만 명시적으로 계산)
            next_review_date = self._calculate_next_review_date(new_mastery_level)
            
            # DB 업데이트
            update_data = {
                "mastery_level": new_mastery_level,
                "review_count": review_count + 1,
                "last_reviewed": datetime.utcnow().isoformat(),
                "next_review": next_review_date.isoformat() if next_review_date else None
            }
            
            result = self.db.client.from_("user_words").update(update_data).eq(
                "user_id", user_id
            ).eq("word_id", word_id).execute()
            
            if not result.data:
                raise Exception("복습 결과 업데이트 실패")
            
            logger.info(f"✅ 복습 결과 제출 성공: {user_id}, {word_id}, 정답: {correct}")
            
            return {
                "message": "복습 결과가 기록되었습니다.",
                "user_id": user_id,
                "word_id": word_id,
                "correct": correct,
                "old_mastery_level": current_mastery,
                "new_mastery_level": new_mastery_level,
                "response_time": response_time,
                "next_review": next_review_date.isoformat() if next_review_date else None,
                "reviewed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 복습 결과 제출 실패: {str(e)}")
            raise
    
    async def get_review_stats(self, user_id: str) -> Dict[str, Any]:
        """사용자 복습 통계 조회"""
        try:
            # 오늘 복습한 단어 수
            today = datetime.utcnow().date()
            today_start = datetime.combine(today, datetime.min.time())
            
            today_reviews = self.db.client.from_("user_words").select(
                "id", count="exact"
            ).eq("user_id", user_id).gte(
                "last_reviewed", today_start.isoformat()
            ).execute()
            
            today_count = today_reviews.count if today_reviews.count else 0
            
            # 복습 예정 단어 수
            due_count = await self._count_due_words(user_id)
            
            # 연속 복습 일수 계산
            streak = await self._calculate_review_streak(user_id)
            
            # 숙련도별 분포
            mastery_distribution = {}
            for level in range(6):
                level_result = self.db.client.from_("user_words").select(
                    "id", count="exact"
                ).eq("user_id", user_id).eq("mastery_level", level).execute()
                
                mastery_distribution[str(level)] = level_result.count if level_result.count else 0
            
            logger.info(f"✅ 복습 통계 조회 성공: {user_id}")
            
            return {
                "user_id": user_id,
                "today_reviews": today_count,
                "due_for_review": due_count,
                "review_streak": streak,
                "mastery_distribution": mastery_distribution,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 복습 통계 조회 실패: {str(e)}")
            raise
    
    # ===================
    # Private Methods
    # ===================
    
    async def _get_new_words(self, user_id: str, count: int) -> List[Dict[str, Any]]:
        """새로운 단어들 조회 (mastery_level = 0)"""
        try:
            result = self.db.client.from_("user_words").select(
                "*, words(*)"
            ).eq("user_id", user_id).eq("mastery_level", 0).order(
                "added_at"
            ).limit(count).execute()
            
            words = []
            if result.data:
                for user_word in result.data:
                    words.append(self._format_review_word(user_word))
            
            return words
            
        except Exception as e:
            logger.error(f"❌ 새 단어 조회 실패: {str(e)}")
            return []
    
    async def _get_due_words(self, user_id: str, count: int) -> List[Dict[str, Any]]:
        """복습 예정인 단어들 조회"""
        try:
            now = datetime.utcnow().isoformat()
            
            result = self.db.client.from_("user_words").select(
                "*, words(*)"
            ).eq("user_id", user_id).lte("next_review", now).order(
                "next_review"
            ).limit(count).execute()
            
            words = []
            if result.data:
                for user_word in result.data:
                    words.append(self._format_review_word(user_word))
            
            return words
            
        except Exception as e:
            logger.error(f"❌ 복습 예정 단어 조회 실패: {str(e)}")
            return []
    
    async def _count_due_words(self, user_id: str) -> int:
        """복습 예정 단어 수 계산"""
        try:
            now = datetime.utcnow().isoformat()
            
            result = self.db.client.from_("user_words").select(
                "id", count="exact"
            ).eq("user_id", user_id).lte("next_review", now).execute()
            
            return result.count if result.count else 0
            
        except Exception as e:
            logger.error(f"❌ 복습 예정 단어 수 계산 실패: {str(e)}")
            return 0
    
    async def _get_user_word(self, user_id: str, word_id: str) -> Optional[Dict[str, Any]]:
        """사용자 단어 조회"""
        try:
            result = self.db.client.from_("user_words").select("*").eq(
                "user_id", user_id
            ).eq("word_id", word_id).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"❌ 사용자 단어 조회 실패: {str(e)}")
            return None
    
    async def _calculate_review_streak(self, user_id: str) -> int:
        """연속 복습 일수 계산"""
        try:
            # 최근 30일간의 복습 기록 조회
            days_ago_30 = datetime.utcnow() - timedelta(days=30)
            
            result = self.db.client.from_("user_words").select(
                "last_reviewed"
            ).eq("user_id", user_id).gte(
                "last_reviewed", days_ago_30.isoformat()
            ).order("last_reviewed", desc=True).execute()
            
            if not result.data:
                return 0
            
            # 날짜별로 그룹화하여 연속 일수 계산
            review_dates = set()
            for record in result.data:
                if record.get("last_reviewed"):
                    review_date = datetime.fromisoformat(
                        record["last_reviewed"].replace("Z", "+00:00")
                    ).date()
                    review_dates.add(review_date)
            
            # 연속 일수 계산
            sorted_dates = sorted(review_dates, reverse=True)
            streak = 0
            current_date = datetime.utcnow().date()
            
            for review_date in sorted_dates:
                if review_date == current_date or review_date == current_date - timedelta(days=streak):
                    streak += 1
                    current_date = review_date
                else:
                    break
            
            return streak
            
        except Exception as e:
            logger.error(f"❌ 복습 연속 일수 계산 실패: {str(e)}")
            return 0
    
    def _calculate_new_mastery_level(
        self, 
        current_level: int, 
        correct: bool, 
        response_time: Optional[float] = None
    ) -> int:
        """
        새로운 숙련도 계산
        
        간격 반복 학습법 알고리즘 적용:
        - 정답: 레벨 상승
        - 오답: 레벨 하락
        - 응답 시간 고려 (빠른 응답 = 더 높은 숙련도)
        """
        new_level = current_level
        
        if correct:
            # 정답인 경우 레벨 상승
            if current_level < 5:
                new_level = current_level + 1
                
                # 응답 시간이 빠르면 추가 보너스 (3초 이내)
                if response_time and response_time < 3.0 and current_level >= 2:
                    new_level = min(5, current_level + 1)
        else:
            # 오답인 경우 레벨 하락
            if current_level > 0:
                # 높은 레벨일수록 더 많이 하락
                if current_level >= 4:
                    new_level = max(0, current_level - 2)
                else:
                    new_level = max(0, current_level - 1)
        
        return new_level
    
    def _calculate_next_review_date(self, mastery_level: int) -> Optional[datetime]:
        """
        다음 복습 날짜 계산
        
        간격 반복 학습법 간격:
        - Level 0: 1일
        - Level 1: 3일
        - Level 2: 7일 (1주)
        - Level 3: 14일 (2주)
        - Level 4: 30일 (1달)
        - Level 5: 90일 (3달)
        """
        interval_days = {
            0: 1,
            1: 3,
            2: 7,
            3: 14,
            4: 30,
            5: 90
        }
        
        days = interval_days.get(mastery_level, 1)
        return datetime.utcnow() + timedelta(days=days)
    
    def _format_review_word(self, user_word: Dict[str, Any]) -> Dict[str, Any]:
        """복습용 단어 응답 포맷"""
        word_data = user_word.get("words") or {}
        
        return {
            "word": {
                "id": word_data.get("id"),
                "text": word_data.get("text"),
                "reading": word_data.get("reading"),
                "meaning": word_data.get("meaning"),
                "part_of_speech": word_data.get("part_of_speech"),
                "difficulty_level": word_data.get("difficulty_level", "beginner"),
                "example_sentence": word_data.get("example_sentence"),
                "example_translation": word_data.get("example_translation"),
                "audio_url": word_data.get("audio_url")
            },
            "added_at": user_word.get("added_at"),
            "mastery_level": user_word.get("mastery_level", 0),
            "review_count": user_word.get("review_count", 0),
            "last_reviewed": user_word.get("last_reviewed"),
            "next_review": user_word.get("next_review"),
            "tags": user_word.get("tags", []),
            "notes": user_word.get("notes")
        } 