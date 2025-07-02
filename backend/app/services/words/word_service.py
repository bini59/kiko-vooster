"""
단어 관련 서비스

단어 검색, 생성, 조회 등 기본적인 단어 관리 기능을 담당합니다.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from app.core.database import DatabaseManager
from .jmdict_service import JMdictService

logger = logging.getLogger(__name__)


class WordService:
    """단어 관련 비즈니스 로직을 처리하는 서비스"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.jmdict = JMdictService()
    
    async def search_words(
        self, 
        query: str, 
        search_type: str = "all",
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        단어 검색
        
        Args:
            query: 검색 단어
            search_type: 검색 타입 (all, kanji, hiragana, meaning)
            limit: 결과 개수 제한
            
        Returns:
            검색 결과 딕셔너리
        """
        try:
            # 1. 로컬 DB에서 검색
            local_results = await self._search_local_words(query, search_type, limit)
            
            # 2. JMdict API에서 검색 (로컬 결과가 부족한 경우)
            external_results = []
            if len(local_results) < limit // 2:
                external_results = await self.jmdict.search_words(
                    query, limit - len(local_results)
                )
                
                # 새로운 단어들을 로컬 DB에 저장
                for word_data in external_results:
                    await self._create_word_if_not_exists(word_data)
            
            # 3. 결과 통합 및 중복 제거
            all_results = local_results + external_results
            unique_results = self._deduplicate_words(all_results)
            
            logger.info(f"✅ 단어 검색 완료: '{query}', 결과: {len(unique_results)}개")
            
            return {
                "results": unique_results[:limit],
                "total": len(unique_results),
                "query": query,
                "search_type": search_type
            }
            
        except Exception as e:
            logger.error(f"❌ 단어 검색 실패: {str(e)}")
            raise
    
    async def get_word_by_id(self, word_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 단어 조회
        
        Args:
            word_id: 단어 ID
            
        Returns:
            단어 정보
        """
        try:
            word = await self.db.get_word_by_id(word_id)
            
            if word:
                logger.info(f"✅ 단어 조회 성공: {word_id}")
            else:
                logger.warning(f"⚠️ 단어를 찾을 수 없음: {word_id}")
            
            return word
            
        except Exception as e:
            logger.error(f"❌ 단어 조회 실패: {str(e)}")
            return None
    
    async def get_word_by_text(self, word_text: str) -> Optional[Dict[str, Any]]:
        """
        텍스트로 단어 조회
        
        Args:
            word_text: 단어 텍스트
            
        Returns:
            단어 정보
        """
        try:
            word = await self.db.get_word_by_text(word_text)
            
            if word:
                logger.info(f"✅ 단어 텍스트 조회 성공: {word_text}")
            else:
                logger.info(f"ℹ️ 단어 텍스트를 찾을 수 없음: {word_text}")
            
            return word
            
        except Exception as e:
            logger.error(f"❌ 단어 텍스트 조회 실패: {str(e)}")
            return None
    
    async def create_word(self, word_data: Dict[str, Any]) -> Dict[str, Any]:
        """새 단어 생성"""
        try:
            # 중복 체크
            existing = await self.get_word_by_text(word_data["text"])
            if existing:
                logger.info(f"⚠️ 이미 존재하는 단어: {word_data['text']}")
                return existing
            
            # 단어 데이터 준비
            create_data = {
                "id": str(uuid4()),
                "text": word_data["text"],
                "reading": word_data.get("reading"),
                "meaning": word_data["meaning"],
                "part_of_speech": word_data["part_of_speech"],
                "difficulty_level": word_data.get("difficulty_level", "beginner"),
                "example_sentence": word_data.get("example_sentence"),
                "example_translation": word_data.get("example_translation"),
                "audio_url": word_data.get("audio_url"),
                "metadata": word_data.get("metadata", {}),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # DB에 저장
            result = self.db.client.from_("words").insert(create_data).execute()
            
            if result.data:
                created_word = result.data[0]
                logger.info(f"✅ 새 단어 생성 성공: {word_data['text']}")
                return self._format_word_response(created_word)
            
            raise Exception("단어 생성 실패")
            
        except Exception as e:
            logger.error(f"❌ 단어 생성 실패: {str(e)}")
            raise
    
    # ===================
    # Private Methods
    # ===================
    
    async def _search_local_words(
        self, 
        query: str, 
        search_type: str, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """로컬 DB에서 단어 검색"""
        try:
            query_builder = self.db.client.from_("words").select("*")
            
            if search_type == "kanji":
                query_builder = query_builder.ilike("text", f"%{query}%")
            elif search_type == "hiragana":
                query_builder = query_builder.ilike("reading", f"%{query}%")
            elif search_type == "meaning":
                query_builder = query_builder.ilike("meaning", f"%{query}%")
            else:  # "all"
                query_builder = query_builder.or_(
                    f"text.ilike.%{query}%,reading.ilike.%{query}%,meaning.ilike.%{query}%"
                )
            
            result = query_builder.limit(limit).execute()
            
            words = []
            if result.data:
                for word in result.data:
                    words.append(self._format_word_response(word))
            
            return words
            
        except Exception as e:
            logger.error(f"❌ 로컬 단어 검색 실패: {str(e)}")
            return []
    
    async def _create_word_if_not_exists(self, word_data: Dict[str, Any]) -> Optional[str]:
        """단어가 없으면 생성하고 ID 반환"""
        try:
            existing = await self.get_word_by_text(word_data["text"])
            if existing:
                return existing["id"]
            
            created = await self.create_word(word_data)
            return created["id"]
            
        except Exception as e:
            logger.error(f"❌ 단어 생성 실패: {str(e)}")
            return None
    
    def _deduplicate_words(self, words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """단어 결과 중복 제거"""
        seen_texts = set()
        unique_words = []
        
        for word in words:
            text = word["text"]
            if text not in seen_texts:
                seen_texts.add(text)
                unique_words.append(word)
        
        return unique_words
    
    def _format_word_response(self, word: Dict[str, Any]) -> Dict[str, Any]:
        """단어 응답 포맷"""
        return {
            "id": word["id"],
            "text": word["text"],
            "reading": word.get("reading"),
            "meaning": word["meaning"],
            "part_of_speech": word["part_of_speech"],
            "difficulty_level": word.get("difficulty_level", "beginner"),
            "example_sentence": word.get("example_sentence"),
            "example_translation": word.get("example_translation"),
            "audio_url": word.get("audio_url"),
            "metadata": word.get("metadata", {}),
            "created_at": word.get("created_at"),
            "updated_at": word.get("updated_at")
        } 