"""
Kiko API 데이터베이스 연결 모듈

Supabase 클라이언트를 통한 PostgreSQL 데이터베이스 연결과 
기본적인 CRUD 작업을 관리합니다.
"""

import asyncio
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
from uuid import uuid4

from supabase import create_client, Client
from app.core.config import settings

# 로거 설정
logger = logging.getLogger(__name__)

class DatabaseManager:
    """데이터베이스 연결 및 기본 작업을 관리하는 클래스"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._is_connected: bool = False
    
    async def connect(self) -> bool:
        """Supabase 클라이언트 연결"""
        try:
            if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
                logger.error("Supabase 환경 변수가 설정되지 않았습니다.")
                return False
            
            self.client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY
            )
            
            # 연결 테스트
            test_result = self.client.from_("users").select("id").limit(1).execute()
            self._is_connected = True
            
            logger.info("✅ Supabase 데이터베이스 연결 성공")
            return True
            
        except Exception as e:
            logger.error(f"❌ 데이터베이스 연결 실패: {str(e)}")
            self._is_connected = False
            return False
    
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self._is_connected
    
    async def disconnect(self):
        """연결 종료"""
        if self.client:
            # Supabase 클라이언트는 명시적 연결 종료가 필요하지 않음
            self.client = None
            self._is_connected = False
            logger.info("📡 데이터베이스 연결 종료")
    
    # ==================
    # 사용자 관련 메서드
    # ==================
    
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """사용자 생성"""
        try:
            result = self.client.from_("users").insert(user_data).execute()
            if result.data:
                logger.info(f"✅ 사용자 생성 성공: {user_data.get('email')}")
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"❌ 사용자 생성 실패: {str(e)}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """이메일로 사용자 조회"""
        try:
            result = self.client.from_("users").select("*").eq("email", email).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"❌ 사용자 조회 실패: {str(e)}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """ID로 사용자 조회"""
        try:
            result = self.client.from_("users").select("*").eq("id", user_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"❌ 사용자 조회 실패: {str(e)}")
            return None
    
    # ==================
    # 스크립트 관련 메서드
    # ==================
    
    async def get_scripts(
        self, 
        limit: int = 20, 
        offset: int = 0,
        category: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """스크립트 목록 조회"""
        try:
            query = self.client.from_("scripts").select("*")
            
            if category:
                query = query.eq("category", category)
            if difficulty:
                query = query.eq("difficulty_level", difficulty)
                
            result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"❌ 스크립트 목록 조회 실패: {str(e)}")
            return []
    
    async def get_script_by_id(self, script_id: str) -> Optional[Dict[str, Any]]:
        """스크립트 상세 조회"""
        try:
            result = self.client.from_("scripts").select("*").eq("id", script_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"❌ 스크립트 조회 실패: {str(e)}")
            return None
    
    async def get_script_sentences(self, script_id: str) -> List[Dict[str, Any]]:
        """스크립트의 문장들 조회"""
        try:
            result = self.client.from_("sentences").select("*").eq("script_id", script_id).order("order_index").execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"❌ 스크립트 문장 조회 실패: {str(e)}")
            return []
    
    # ==================
    # 단어 관련 메서드
    # ==================
    
    async def search_words(
        self, 
        query: str, 
        search_type: str = "all", 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """단어 검색"""
        try:
            query_builder = self.client.from_("words").select("*")
            
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
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"❌ 단어 검색 실패: {str(e)}")
            return []
    
    async def get_word_by_id(self, word_id: str) -> Optional[Dict[str, Any]]:
        """ID로 단어 조회"""
        try:
            result = self.client.from_("words").select("*").eq("id", word_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"❌ 단어 조회 실패: {str(e)}")
            return None

    async def get_word_by_text(self, word_text: str) -> Optional[Dict[str, Any]]:
        """텍스트로 단어 조회"""
        try:
            result = self.client.from_("words").select("*").eq("text", word_text).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"❌ 단어 텍스트 조회 실패: {str(e)}")
            return None

    async def get_user_word(self, user_id: str, word_id: str) -> Optional[Dict[str, Any]]:
        """사용자 단어 조회"""
        try:
            result = self.client.from_("user_words").select("*").eq(
                "user_id", user_id
            ).eq("word_id", word_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"❌ 사용자 단어 조회 실패: {str(e)}")
            return None
    
    async def create_word(self, word_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """새 단어 생성"""
        try:
            result = self.client.from_("words").insert(word_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"❌ 단어 생성 실패: {str(e)}")
            return None
    
    # ==================
    # 사용자 단어장 관련 메서드
    # ==================
    
    async def add_user_word(self, user_id: str, word_id: str, tags: List[str] = None) -> bool:
        """사용자 단어장에 단어 추가"""
        try:
            data = {
                "user_id": user_id,
                "word_id": word_id,
                "mastery_level": 1,
                "tags": tags or []
            }
            
            result = self.client.from_("user_words").insert(data).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"❌ 단어장 추가 실패: {str(e)}")
            return False
    
    async def get_user_words(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """사용자 단어장 조회"""
        try:
            result = self.client.from_("user_words").select(
                "*, words(*)"
            ).eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"❌ 사용자 단어장 조회 실패: {str(e)}")
            return []
    
    async def get_user_vocabulary(
        self,
        user_id: str,
        tags: Optional[List[str]] = None,
        mastery_level: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """사용자 단어장 조회"""
        try:
            query_builder = self.client.from_("user_words").select(
                "*, words(*)"
            ).eq("user_id", user_id)
            
            if mastery_level is not None:
                query_builder = query_builder.eq("mastery_level", mastery_level)
            
            if tags:
                for tag in tags:
                    query_builder = query_builder.contains("tags", [tag])
            
            result = query_builder.order("added_at", desc=True).range(
                offset, offset + limit - 1
            ).execute()
            
            return {
                "words": result.data if result.data else [],
                "total": len(result.data) if result.data else 0
            }
            
        except Exception as e:
            logger.error(f"❌ 사용자 단어장 조회 실패: {str(e)}")
            return {"words": [], "total": 0}

    async def add_word_to_vocabulary(
        self,
        user_id: str,
        word_id: str,
        tags: List[str] = None,
        notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """단어장에 단어 추가"""
        try:
            user_word_data = {
                "id": str(uuid4()),
                "user_id": user_id,
                "word_id": word_id,
                "mastery_level": 0,
                "review_count": 0,
                "tags": tags or [],
                "notes": notes,
                "added_at": datetime.utcnow().isoformat(),
                "last_reviewed": None,
                "next_review": None
            }
            
            result = self.client.from_("user_words").insert(user_word_data).execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"❌ 단어장 추가 실패: {str(e)}")
            return None

    async def update_user_word(
        self,
        user_id: str,
        word_id: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """사용자 단어 정보 업데이트"""
        try:
            result = self.client.from_("user_words").update(update_data).eq(
                "user_id", user_id
            ).eq("word_id", word_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"❌ 사용자 단어 업데이트 실패: {str(e)}")
            return False

    async def remove_word_from_vocabulary(self, user_id: str, word_id: str) -> bool:
        """단어장에서 단어 제거"""
        try:
            result = self.client.from_("user_words").delete().eq(
                "user_id", user_id
            ).eq("word_id", word_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"❌ 단어장 제거 실패: {str(e)}")
            return False

    # ==================
    # 진행률 관련 메서드
    # ==================
    
    async def update_user_progress(
        self, 
        user_id: str, 
        script_id: str, 
        current_time: float,
        completed_sentences: List[str] = None
    ) -> bool:
        """사용자 학습 진행률 업데이트"""
        try:
            data = {
                "user_id": user_id,
                "script_id": script_id,
                "current_time": current_time,
                "completed_sentences": completed_sentences or []
            }
            
            # UPSERT (존재하면 업데이트, 없으면 생성)
            result = self.client.from_("user_scripts_progress").upsert(data).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"❌ 진행률 업데이트 실패: {str(e)}")
            return False
    
    async def get_user_progress(self, user_id: str, script_id: str) -> Optional[Dict[str, Any]]:
        """사용자 학습 진행률 조회"""
        try:
            result = self.client.from_("user_scripts_progress").select("*").eq(
                "user_id", user_id
            ).eq("script_id", script_id).execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"❌ 진행률 조회 실패: {str(e)}")
            return None

    # 복습 관련 메서드들
    async def get_review_words(
        self,
        user_id: str,
        count: int = 10,
        mode: str = "mixed"
    ) -> List[Dict[str, Any]]:
        """복습할 단어 목록 조회"""
        try:
            if mode == "new":
                # 새로운 단어들만 (mastery_level = 0)
                result = self.client.from_("user_words").select(
                    "*, words(*)"
                ).eq("user_id", user_id).eq("mastery_level", 0).order(
                    "added_at"
                ).limit(count).execute()
            elif mode == "review":
                # 복습 필요한 단어들만
                now = datetime.utcnow().isoformat()
                result = self.client.from_("user_words").select(
                    "*, words(*)"
                ).eq("user_id", user_id).lte("next_review", now).order(
                    "next_review"
                ).limit(count).execute()
            else:  # mixed
                # 복습과 새 단어 혼합
                due_result = self.client.from_("user_words").select(
                    "*, words(*)"
                ).eq("user_id", user_id).lte(
                    "next_review", datetime.utcnow().isoformat()
                ).order("next_review").limit(count // 2).execute()
                
                remaining = count - len(due_result.data if due_result.data else [])
                if remaining > 0:
                    new_result = self.client.from_("user_words").select(
                        "*, words(*)"
                    ).eq("user_id", user_id).eq("mastery_level", 0).order(
                        "added_at"
                    ).limit(remaining).execute()
                    
                    combined_data = (due_result.data or []) + (new_result.data or [])
                    return combined_data
                else:
                    return due_result.data if due_result.data else []
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"❌ 복습 단어 조회 실패: {str(e)}")
            return []

    async def update_review_result(
        self,
        user_id: str,
        word_id: str,
        correct: bool,
        new_mastery_level: int,
        next_review_date: Optional[datetime] = None
    ) -> bool:
        """복습 결과 업데이트"""
        try:
            update_data = {
                "mastery_level": new_mastery_level,
                "last_reviewed": datetime.utcnow().isoformat()
            }
            
            if next_review_date:
                update_data["next_review"] = next_review_date.isoformat()
            
            # review_count 증가
            current_result = self.client.from_("user_words").select("review_count").eq(
                "user_id", user_id
            ).eq("word_id", word_id).execute()
            
            if current_result.data:
                current_count = current_result.data[0].get("review_count", 0)
                update_data["review_count"] = current_count + 1
            
            result = self.client.from_("user_words").update(update_data).eq(
                "user_id", user_id
            ).eq("word_id", word_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"❌ 복습 결과 업데이트 실패: {str(e)}")
            return False

# ======================
# 전역 데이터베이스 인스턴스
# ======================

_database_instance: Optional[DatabaseManager] = None

async def init_database() -> DatabaseManager:
    """데이터베이스 초기화"""
    global _database_instance
    
    if _database_instance is None:
        _database_instance = DatabaseManager()
        await _database_instance.connect()
    
    return _database_instance

async def get_database() -> DatabaseManager:
    """데이터베이스 인스턴스 가져오기"""
    global _database_instance
    
    if _database_instance is None:
        _database_instance = await init_database()
    
    return _database_instance

async def close_database():
    """데이터베이스 연결 종료"""
    global _database_instance
    
    if _database_instance:
        await _database_instance.disconnect()
        _database_instance = None 