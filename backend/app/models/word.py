"""
단어장 관련 Pydantic 모델

단어 검색, 사용자 단어장, 복습 기능에 사용되는 모든 데이터 모델을 정의합니다.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class DifficultyLevel(str, Enum):
    """난이도 레벨"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class PartOfSpeech(str, Enum):
    """품사"""
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PARTICLE = "particle"
    INTERJECTION = "interjection"
    CONJUNCTION = "conjunction"
    PRONOUN = "pronoun"
    AUXILIARY = "auxiliary"
    COUNTER = "counter"
    PREFIX = "prefix"
    SUFFIX = "suffix"
    UNKNOWN = "unknown"


class SearchType(str, Enum):
    """검색 타입"""
    ALL = "all"
    KANJI = "kanji"
    HIRAGANA = "hiragana"
    MEANING = "meaning"


class ReviewMode(str, Enum):
    """복습 모드"""
    NEW = "new"
    REVIEW = "review"
    MIXED = "mixed"


# ===================
# 기본 단어 모델
# ===================

class Word(BaseModel):
    """기본 단어 모델"""
    id: str
    text: str = Field(..., description="일본어 단어")
    reading: Optional[str] = Field(None, description="히라가나 읽기")
    meaning: str = Field(..., description="한국어 뜻")
    part_of_speech: PartOfSpeech = Field(default=PartOfSpeech.UNKNOWN, description="품사")
    difficulty_level: DifficultyLevel = Field(default=DifficultyLevel.BEGINNER, description="난이도")
    example_sentence: Optional[str] = Field(None, description="예문")
    example_translation: Optional[str] = Field(None, description="예문 번역")
    audio_url: Optional[str] = Field(None, description="발음 오디오 URL")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class UserWord(BaseModel):
    """사용자 단어장 단어 모델"""
    id: str
    user_id: str
    word_id: str
    word: Optional[Word] = None
    mastery_level: int = Field(default=0, ge=0, le=5, description="숙련도 (0-5)")
    review_count: int = Field(default=0, ge=0, description="복습 횟수")
    tags: List[str] = Field(default_factory=list, description="사용자 태그")
    notes: Optional[str] = Field(None, description="사용자 메모")
    added_at: datetime
    last_reviewed: Optional[datetime] = None
    next_review: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @validator('tags')
    def validate_tags(cls, v):
        """태그 검증"""
        if len(v) > 10:
            raise ValueError("태그는 최대 10개까지 허용됩니다")
        for tag in v:
            if len(tag) > 20:
                raise ValueError("각 태그는 20자 이내로 제한됩니다")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


# ===================
# 단어 검색 관련 모델
# ===================

class WordSearchRequest(BaseModel):
    """단어 검색 요청 모델"""
    query: str = Field(..., min_length=1, max_length=50, description="검색어")
    search_type: SearchType = Field(default=SearchType.ALL, description="검색 타입")
    limit: int = Field(default=20, ge=1, le=100, description="결과 개수 제한")


class WordSearchResponse(BaseModel):
    """단어 검색 응답 모델"""
    results: List[Word]
    total: int
    query: str
    search_type: SearchType


# ===================
# 단어장 관리 관련 모델
# ===================

class AddWordRequest(BaseModel):
    """단어 추가 요청 모델"""
    word_text: str = Field(..., min_length=1, max_length=50, description="추가할 단어")
    tags: List[str] = Field(default_factory=list, description="태그 목록")
    notes: Optional[str] = Field(None, max_length=500, description="사용자 메모")

    @validator('word_text')
    def validate_word_text(cls, v):
        """단어 텍스트 검증"""
        if not v.strip():
            raise ValueError("단어를 입력해주세요")
        return v.strip()


class AddWordResponse(BaseModel):
    """단어 추가 응답 모델"""
    message: str
    word: UserWord


class UpdateWordRequest(BaseModel):
    """단어 업데이트 요청 모델"""
    mastery_level: Optional[int] = Field(None, ge=0, le=5, description="숙련도")
    tags: Optional[List[str]] = Field(None, description="태그 목록")
    notes: Optional[str] = Field(None, max_length=500, description="사용자 메모")


class UpdateWordResponse(BaseModel):
    """단어 업데이트 응답 모델"""
    message: str
    word: UserWord


class VocabularyStatsResponse(BaseModel):
    """단어장 통계 응답 모델"""
    total_words: int
    mastery_distribution: Dict[str, int]  # "0": 5, "1": 10, ...
    recent_additions: int  # 최근 7일간 추가된 단어
    due_for_review: int  # 복습 예정 단어
    favorite_tags: List[str]  # 자주 사용하는 태그
    tag_counts: Dict[str, int]  # 태그별 단어 개수


class VocabularyTagsResponse(BaseModel):
    """단어장 태그 응답 모델"""
    tags: List[Dict[str, Any]]  # [{"name": "태그명", "count": 개수}, ...]
    total_tags: int


# ===================
# 복습 관련 모델
# ===================

class ReviewWordsRequest(BaseModel):
    """복습 단어 요청 모델"""
    count: int = Field(default=10, ge=1, le=50, description="복습할 단어 개수")
    mode: ReviewMode = Field(default=ReviewMode.MIXED, description="복습 모드")


class ReviewWordsResponse(BaseModel):
    """복습 단어 응답 모델"""
    words: List[UserWord]
    total_due: int  # 전체 복습 예정 단어 수
    mode: ReviewMode
    session_id: Optional[str] = None  # 복습 세션 ID


class ReviewResultRequest(BaseModel):
    """복습 결과 요청 모델"""
    word_id: str = Field(..., description="단어 ID")
    correct: bool = Field(..., description="정답 여부")
    response_time: Optional[float] = Field(None, ge=0, description="응답 시간 (초)")
    session_id: Optional[str] = Field(None, description="복습 세션 ID")


class ReviewResultResponse(BaseModel):
    """복습 결과 응답 모델"""
    message: str
    correct: bool
    new_mastery_level: int
    next_review: Optional[datetime] = None
    response_time: Optional[float] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ReviewStatsResponse(BaseModel):
    """복습 통계 응답 모델"""
    total_words: int
    words_reviewed: int  # 복습을 시작한 단어 수
    due_for_review: int  # 복습 예정 단어 수
    new_words: int  # 신규 단어 수
    mastered_words: int  # 숙련된 단어 수 (레벨 4 이상)
    average_mastery_level: float  # 평균 숙련도
    recent_reviews: int  # 최근 7일간 복습한 단어 수
    review_completion_rate: float  # 복습 완료율 (%)


# ===================
# 유틸리티 모델
# ===================

class TagInfo(BaseModel):
    """태그 정보 모델"""
    name: str
    count: int
    color: Optional[str] = None  # UI에서 사용할 색상


class WordValidationResult(BaseModel):
    """단어 검증 결과 모델"""
    is_valid: bool
    is_japanese: bool
    char_types: Dict[str, int]
    estimated_difficulty: DifficultyLevel
    cleaned_text: str
    reading: Optional[str] = None
    errors: List[str] = Field(default_factory=list)


class JMdictEntry(BaseModel):
    """JMdict 사전 항목 모델"""
    word: str
    reading: Optional[str] = None
    meanings: List[str]
    part_of_speech: List[str] = Field(default_factory=list)
    jlpt_level: Optional[str] = None
    frequency_rank: Optional[int] = None


# ===================
# 에러 응답 모델
# ===================

class ErrorResponse(BaseModel):
    """에러 응답 모델"""
    detail: str
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ValidationErrorResponse(BaseModel):
    """검증 에러 응답 모델"""
    detail: str
    errors: List[Dict[str, Any]]
    code: str = "VALIDATION_ERROR"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 