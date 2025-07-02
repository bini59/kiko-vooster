"""
JMdict 일본어 사전 API 연동 서비스

외부 일본어 사전 API와 연동하여 단어 정보를 가져옵니다.
"""

import logging
import asyncio
import aiohttp
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import quote

logger = logging.getLogger(__name__)


class JMdictService:
    """JMdict 사전 API 연동 서비스"""
    
    def __init__(self):
        # 캐시 설정 (메모리 기반 단순 캐시)
        self._cache = {}
        self._cache_timeout = timedelta(hours=24)  # 24시간 캐시
        
        # API 설정
        self.api_base_url = "https://jisho.org/api/v1/search/words"
        self.timeout = aiohttp.ClientTimeout(total=10)
    
    async def search_words(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        JMdict API에서 단어 검색
        
        Args:
            query: 검색 단어
            limit: 결과 개수 제한
            
        Returns:
            단어 정보 리스트
        """
        try:
            # 캐시 확인
            cache_key = f"search_{query}_{limit}"
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info(f"✅ 캐시에서 단어 검색 결과 반환: {query}")
                return cached_result
            
            # API 호출
            words = await self._fetch_from_jisho(query, limit)
            
            # 캐시에 저장
            self._save_to_cache(cache_key, words)
            
            logger.info(f"✅ JMdict API 단어 검색 성공: '{query}', {len(words)}개")
            return words
            
        except Exception as e:
            logger.error(f"❌ JMdict API 단어 검색 실패: {str(e)}")
            # 실패 시 빈 결과 반환
            return []
    
    async def get_word_details(self, word_text: str) -> Optional[Dict[str, Any]]:
        """
        특정 단어의 상세 정보 조회
        
        Args:
            word_text: 단어 텍스트
            
        Returns:
            단어 상세 정보
        """
        try:
            results = await self.search_words(word_text, limit=1)
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"❌ JMdict 단어 상세 조회 실패: {str(e)}")
            return None
    
    async def _fetch_from_jisho(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Jisho.org API에서 단어 정보 가져오기"""
        try:
            url = f"{self.api_base_url}?keyword={quote(query)}"
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_jisho_response(data, limit)
                    else:
                        logger.warning(f"⚠️ Jisho API 응답 오류: {response.status}")
                        return []
                        
        except asyncio.TimeoutError:
            logger.error("❌ Jisho API 요청 타임아웃")
            return []
        except Exception as e:
            logger.error(f"❌ Jisho API 요청 실패: {str(e)}")
            return []
    
    def _parse_jisho_response(self, data: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Jisho API 응답 파싱"""
        words = []
        
        try:
            jisho_data = data.get("data", [])
            
            for item in jisho_data[:limit]:
                # 일본어 표기 추출
                japanese = item.get("japanese", [])
                if not japanese:
                    continue
                
                primary_japanese = japanese[0]
                word_text = primary_japanese.get("word") or primary_japanese.get("reading", "")
                reading = primary_japanese.get("reading", "")
                
                # 의미 추출
                senses = item.get("senses", [])
                if not senses:
                    continue
                
                primary_sense = senses[0]
                meanings = primary_sense.get("english_definitions", [])
                parts_of_speech = primary_sense.get("parts_of_speech", [])
                
                if not meanings:
                    continue
                
                # 한국어 의미는 영어 의미를 기반으로 임시 처리
                # 실제로는 한국어 사전 API를 사용해야 함
                korean_meaning = self._translate_to_korean(meanings[0])
                
                # 품사 매핑
                part_of_speech = self._map_part_of_speech(parts_of_speech)
                
                # 난이도 추정 (단어 길이와 빈도 기반 임시 로직)
                difficulty = self._estimate_difficulty(word_text)
                
                word_info = {
                    "text": word_text,
                    "reading": reading if reading != word_text else None,
                    "meaning": korean_meaning,
                    "part_of_speech": part_of_speech,
                    "difficulty_level": difficulty,
                    "example_sentence": None,  # Jisho에서 예문 제공하지 않음
                    "example_translation": None,
                    "audio_url": None,  # 별도 TTS 서비스 필요
                    "metadata": {
                        "source": "jisho",
                        "english_meanings": meanings,
                        "jlpt_level": self._extract_jlpt_level(item),
                        "common": item.get("is_common", False)
                    }
                }
                
                words.append(word_info)
            
            return words
            
        except Exception as e:
            logger.error(f"❌ Jisho 응답 파싱 실패: {str(e)}")
            return []
    
    def _translate_to_korean(self, english_meaning: str) -> str:
        """
        영어 의미를 한국어로 번역 (임시 매핑)
        실제로는 번역 API나 한-일 사전 API 사용 필요
        """
        # 기본적인 단어 매핑 (확장 필요)
        translation_map = {
            "weather": "날씨",
            "today": "오늘",
            "tomorrow": "내일",
            "yesterday": "어제",
            "morning": "아침",
            "afternoon": "오후",
            "evening": "저녁",
            "night": "밤",
            "water": "물",
            "fire": "불",
            "earth": "땅",
            "wind": "바람",
            "rain": "비",
            "snow": "눈",
            "sun": "태양",
            "moon": "달",
            "star": "별",
            "mountain": "산",
            "sea": "바다",
            "river": "강",
            "tree": "나무",
            "flower": "꽃",
            "grass": "풀",
            "animal": "동물",
            "bird": "새",
            "fish": "물고기",
            "dog": "개",
            "cat": "고양이",
            "person": "사람",
            "man": "남자",
            "woman": "여자",
            "child": "아이",
            "family": "가족",
            "friend": "친구",
            "teacher": "선생님",
            "student": "학생",
            "house": "집",
            "school": "학교",
            "car": "자동차",
            "train": "기차",
            "food": "음식",
            "rice": "쌀",
            "bread": "빵",
            "meat": "고기",
            "vegetable": "채소"
        }
        
        # 매핑에서 찾기
        lower_meaning = english_meaning.lower().strip()
        if lower_meaning in translation_map:
            return translation_map[lower_meaning]
        
        # 매핑에 없으면 영어 그대로 반환 (임시)
        return english_meaning
    
    def _map_part_of_speech(self, parts_of_speech: List[str]) -> str:
        """품사 매핑"""
        if not parts_of_speech:
            return "기타"
        
        pos_map = {
            "noun": "명사",
            "verb": "동사", 
            "adjective": "형용사",
            "adverb": "부사",
            "particle": "조사",
            "interjection": "감탄사",
            "conjunction": "접속사",
            "pronoun": "대명사",
            "preposition": "전치사",
            "counter": "수사",
            "prefix": "접두사",
            "suffix": "접미사",
            "auxiliary verb": "보조동사",
            "i-adjective": "이형용사",
            "na-adjective": "나형용사"
        }
        
        # 첫 번째 품사 매핑
        primary_pos = parts_of_speech[0].lower()
        for key, value in pos_map.items():
            if key in primary_pos:
                return value
        
        return "기타"
    
    def _estimate_difficulty(self, word_text: str) -> str:
        """단어 난이도 추정 (임시 로직)"""
        # 히라가나/카타카나만 있으면 초급
        if all(ord(char) >= 0x3040 and ord(char) <= 0x30FF for char in word_text):
            return "beginner"
        
        # 한자 포함 길이 기반 추정
        length = len(word_text)
        if length <= 2:
            return "beginner"
        elif length <= 4:
            return "intermediate"
        else:
            return "advanced"
    
    def _extract_jlpt_level(self, item: Dict[str, Any]) -> Optional[str]:
        """JLPT 레벨 추출"""
        tags = item.get("tags", [])
        for tag in tags:
            if "JLPT" in tag:
                return tag
        return None
    
    def _get_from_cache(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """캐시에서 데이터 조회"""
        if key in self._cache:
            cached_item = self._cache[key]
            if datetime.utcnow() - cached_item["timestamp"] < self._cache_timeout:
                return cached_item["data"]
            else:
                # 만료된 캐시 삭제
                del self._cache[key]
        return None
    
    def _save_to_cache(self, key: str, data: List[Dict[str, Any]]):
        """캐시에 데이터 저장"""
        self._cache[key] = {
            "data": data,
            "timestamp": datetime.utcnow()
        }
        
        # 캐시 크기 제한 (최대 1000개 항목)
        if len(self._cache) > 1000:
            # 가장 오래된 항목 삭제
            oldest_key = min(
                self._cache.keys(), 
                key=lambda k: self._cache[k]["timestamp"]
            )
            del self._cache[oldest_key] 