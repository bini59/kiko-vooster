"""
사용자 단어장 관리 서비스

사용자별 단어장 CRUD, 태그 관리, 학습 진행상황 관리를 담당합니다.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from app.core.database import DatabaseManager
from .word_service import WordService

logger = logging.getLogger(__name__)


class VocabularyService:
    """사용자 단어장 관리 서비스"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.word_service = WordService(db_manager)
    
    async def get_user_vocabulary(
        self,
        user_id: str,
        tags: Optional[List[str]] = None,
        mastery_level: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        사용자 단어장 조회
        
        Args:
            user_id: 사용자 ID
            tags: 필터링할 태그 목록
            mastery_level: 숙련도 필터 (0-5)
            limit: 결과 개수 제한
            offset: 오프셋
            
        Returns:
            단어장 데이터
        """
        try:
            # 기본 쿼리 구성
            query_builder = self.db.client.from_("user_words").select(
                "*, words(*)"
            ).eq("user_id", user_id)
            
            # 필터 적용
            if mastery_level is not None:
                query_builder = query_builder.eq("mastery_level", mastery_level)
            
            if tags:
                # PostgreSQL 배열 연산자 사용
                for tag in tags:
                    query_builder = query_builder.contains("tags", [tag])
            
            # 정렬 및 페이징
            result = query_builder.order("added_at", desc=True).range(
                offset, offset + limit - 1
            ).execute()
            
            if not result.data:
                return {"words": [], "total": 0, "has_more": False}
            
            # 응답 포맷
            formatted_words = []
            for user_word in result.data:
                formatted_word = self._format_user_word_response(user_word)
                formatted_words.append(formatted_word)
            
            # 전체 개수 조회
            count_query = self.db.client.from_("user_words").select(
                "id", count="exact"
            ).eq("user_id", user_id)
            
            if mastery_level is not None:
                count_query = count_query.eq("mastery_level", mastery_level)
            
            if tags:
                for tag in tags:
                    count_query = count_query.contains("tags", [tag])
            
            count_result = count_query.execute()
            total = count_result.count if count_result.count else 0
            
            logger.info(f"✅ 사용자 단어장 조회 성공: {user_id}, {len(formatted_words)}개")
            
            return {
                "words": formatted_words,
                "total": total,
                "has_more": offset + len(formatted_words) < total,
                "offset": offset,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"❌ 사용자 단어장 조회 실패: {str(e)}")
            raise
    
    async def add_word_to_vocabulary(
        self,
        user_id: str,
        word_text: str,
        tags: List[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        단어장에 단어 추가
        
        Args:
            user_id: 사용자 ID
            word_text: 추가할 단어 텍스트
            tags: 태그 목록
            notes: 사용자 메모
            
        Returns:
            추가된 단어 정보
        """
        try:
            # 1. 단어 찾기 또는 생성
            word = await self.word_service.get_word_by_text(word_text)
            if not word:
                # JMdict에서 검색하여 단어 생성
                search_results = await self.word_service.search_words(word_text, limit=1)
                if not search_results["results"]:
                    raise ValueError(f"단어를 찾을 수 없습니다: {word_text}")
                
                word = search_results["results"][0]
            
            # 2. 중복 체크
            existing = await self._get_user_word(user_id, word["id"])
            if existing:
                logger.warning(f"⚠️ 이미 단어장에 있는 단어: {word_text}")
                return self._format_user_word_response(existing)
            
            # 3. 사용자 단어장에 추가
            user_word_data = {
                "id": str(uuid4()),
                "user_id": user_id,
                "word_id": word["id"],
                "mastery_level": 0,
                "review_count": 0,
                "tags": tags or [],
                "notes": notes,
                "added_at": datetime.utcnow().isoformat(),
                "last_reviewed": None,
                "next_review": None
            }
            
            result = self.db.client.from_("user_words").insert(user_word_data).execute()
            
            if result.data:
                created_user_word = result.data[0]
                # words 테이블 정보도 함께 조회
                user_word_with_word = await self._get_user_word_with_details(
                    user_id, word["id"]
                )
                
                logger.info(f"✅ 단어장 추가 성공: {user_id}, {word_text}")
                return self._format_user_word_response(user_word_with_word)
            
            raise Exception("단어장 추가 실패")
            
        except Exception as e:
            logger.error(f"❌ 단어장 추가 실패: {str(e)}")
            raise
    
    async def update_vocabulary_word(
        self,
        user_id: str,
        word_id: str,
        mastery_level: Optional[int] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        단어장 단어 정보 업데이트
        
        Args:
            user_id: 사용자 ID
            word_id: 단어 ID
            mastery_level: 숙련도 (0-5)
            tags: 태그 목록
            notes: 사용자 메모
            
        Returns:
            업데이트된 단어 정보
        """
        try:
            # 기존 단어 확인
            existing = await self._get_user_word(user_id, word_id)
            if not existing:
                raise ValueError("단어장에서 해당 단어를 찾을 수 없습니다")
            
            # 업데이트 데이터 구성
            update_data = {"updated_at": datetime.utcnow().isoformat()}
            
            if mastery_level is not None:
                update_data["mastery_level"] = mastery_level
            if tags is not None:
                update_data["tags"] = tags
            if notes is not None:
                update_data["notes"] = notes
            
            # DB 업데이트
            result = self.db.client.from_("user_words").update(update_data).eq(
                "user_id", user_id
            ).eq("word_id", word_id).execute()
            
            if result.data:
                # 업데이트된 정보 조회
                updated_user_word = await self._get_user_word_with_details(user_id, word_id)
                
                logger.info(f"✅ 단어장 업데이트 성공: {user_id}, {word_id}")
                return self._format_user_word_response(updated_user_word)
            
            raise Exception("단어장 업데이트 실패")
            
        except Exception as e:
            logger.error(f"❌ 단어장 업데이트 실패: {str(e)}")
            raise
    
    async def remove_word_from_vocabulary(self, user_id: str, word_id: str) -> bool:
        """
        단어장에서 단어 제거
        
        Args:
            user_id: 사용자 ID
            word_id: 단어 ID
            
        Returns:
            제거 성공 여부
        """
        try:
            # 기존 단어 확인
            existing = await self._get_user_word(user_id, word_id)
            if not existing:
                logger.warning(f"⚠️ 제거할 단어를 찾을 수 없음: {word_id}")
                return False
            
            # DB에서 삭제
            result = self.db.client.from_("user_words").delete().eq(
                "user_id", user_id
            ).eq("word_id", word_id).execute()
            
            success = bool(result.data)
            if success:
                logger.info(f"✅ 단어장 제거 성공: {user_id}, {word_id}")
            else:
                logger.error(f"❌ 단어장 제거 실패: {user_id}, {word_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 단어장 제거 실패: {str(e)}")
            return False
    
    async def get_vocabulary_stats(self, user_id: str) -> Dict[str, Any]:
        """사용자 단어장 통계 조회"""
        try:
            # 전체 단어 수
            total_result = self.db.client.from_("user_words").select(
                "id", count="exact"
            ).eq("user_id", user_id).execute()
            
            total_words = total_result.count if total_result.count else 0
            
            # 숙련도별 분포
            mastery_distribution = {}
            for level in range(6):
                level_result = self.db.client.from_("user_words").select(
                    "id", count="exact"
                ).eq("user_id", user_id).eq("mastery_level", level).execute()
                
                mastery_distribution[str(level)] = level_result.count if level_result.count else 0
            
            # 최근 7일간 추가된 단어
            week_ago = (datetime.utcnow() - datetime.timedelta(days=7)).isoformat()
            recent_result = self.db.client.from_("user_words").select(
                "id", count="exact"
            ).eq("user_id", user_id).gte("added_at", week_ago).execute()
            
            recent_additions = recent_result.count if recent_result.count else 0
            
            # 태그별 통계
            tags_result = self.db.client.from_("user_words").select("tags").eq(
                "user_id", user_id
            ).execute()
            
            tag_counts = {}
            if tags_result.data:
                for user_word in tags_result.data:
                    for tag in user_word.get("tags", []):
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            favorite_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            logger.info(f"✅ 단어장 통계 조회 성공: {user_id}")
            
            return {
                "user_id": user_id,
                "total_words": total_words,
                "mastery_distribution": mastery_distribution,
                "recent_additions": recent_additions,
                "favorite_tags": [tag for tag, count in favorite_tags],
                "tag_counts": dict(favorite_tags),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 단어장 통계 조회 실패: {str(e)}")
            raise
    
    async def get_vocabulary_tags(self, user_id: str) -> Dict[str, Any]:
        """사용자 단어장 태그 목록 조회"""
        try:
            result = self.db.client.from_("user_words").select("tags").eq(
                "user_id", user_id
            ).execute()
            
            tag_counts = {}
            if result.data:
                for user_word in result.data:
                    for tag in user_word.get("tags", []):
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            tags_list = [
                {"name": tag, "count": count} 
                for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            ]
            
            logger.info(f"✅ 단어장 태그 조회 성공: {user_id}, {len(tags_list)}개")
            
            return {
                "user_id": user_id,
                "tags": tags_list,
                "total_tags": len(tags_list),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 단어장 태그 조회 실패: {str(e)}")
            raise
    
    # ===================
    # Private Methods
    # ===================
    
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
    
    async def _get_user_word_with_details(
        self, 
        user_id: str, 
        word_id: str
    ) -> Optional[Dict[str, Any]]:
        """단어 상세 정보와 함께 사용자 단어 조회"""
        try:
            result = self.db.client.from_("user_words").select(
                "*, words(*)"
            ).eq("user_id", user_id).eq("word_id", word_id).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"❌ 사용자 단어 상세 조회 실패: {str(e)}")
            return None
    
    def _format_user_word_response(self, user_word: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 단어 응답 포맷"""
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