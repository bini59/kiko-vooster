"""
단어 관련 API 엔드포인트

단어장 관리, 단어 검색, 복습 모드를 담당합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.api.v1.endpoints.auth import oauth2_scheme

router = APIRouter()

# 모델 정의
class Word(BaseModel):
    """단어 모델"""
    id: str
    text: str                         # 일본어 단어
    reading: Optional[str] = None     # 히라가나 읽기
    meaning: str                      # 한국어 뜻
    part_of_speech: str               # 품사 (명사, 동사, 형용사 등)
    difficulty_level: str = "beginner"
    example_sentence: Optional[str] = None    # 예문
    example_translation: Optional[str] = None # 예문 번역
    audio_url: Optional[str] = None   # 발음 오디오 URL

class UserWord(BaseModel):
    """사용자 단어장 단어 모델"""
    word: Word
    added_at: datetime
    mastery_level: int = 0            # 숙련도 (0-5)
    review_count: int = 0             # 복습 횟수
    last_reviewed: Optional[datetime] = None
    tags: List[str] = []              # 사용자 태그
    notes: Optional[str] = None       # 사용자 메모

class WordSearch(BaseModel):
    """단어 검색 요청 모델"""
    query: str
    search_type: str = "all"          # all, kanji, hiragana, meaning

class AddWordRequest(BaseModel):
    """단어 추가 요청 모델"""
    word_text: str
    tags: List[str] = []
    notes: Optional[str] = None

class UpdateWordRequest(BaseModel):
    """단어 업데이트 요청 모델"""
    mastery_level: Optional[int] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None

@router.get("/search")
async def search_words(
    q: str = Query(..., description="검색 단어"),
    limit: int = Query(20, ge=1, le=100, description="결과 개수 제한")
):
    """
    단어 검색
    
    일본어 단어를 검색하여 뜻과 예문을 반환합니다.
    """
    # TODO: 실제 사전 API 연동 (JMdict 등)
    
    # 임시 검색 결과 (개발 단계)
    if q in ["天気", "てんき"]:
        return {
            "results": [
                Word(
                    id="word_1",
                    text="天気",
                    reading="てんき",
                    meaning="날씨",
                    part_of_speech="명사",
                    difficulty_level="beginner",
                    example_sentence="今日は良い天気ですね。",
                    example_translation="오늘은 좋은 날씨네요.",
                    audio_url="https://example.com/audio/tenki.mp3"
                )
            ],
            "total": 1
        }
    
    return {"results": [], "total": 0}

@router.get("/vocabulary", response_model=List[UserWord])
async def get_user_vocabulary(
    tags: Optional[str] = Query(None, description="태그 필터 (쉼표로 구분)"),
    mastery_level: Optional[int] = Query(None, ge=0, le=5, description="숙련도 필터"),
    limit: int = Query(50, ge=1, le=200, description="결과 개수 제한"),
    offset: int = Query(0, ge=0, description="오프셋"),
    token: str = Depends(oauth2_scheme)
):
    """
    사용자 단어장 조회
    
    사용자가 저장한 단어들을 태그, 숙련도 등으로 필터링하여 반환합니다.
    """
    # TODO: JWT에서 사용자 ID 추출 및 실제 DB 조회
    
    # 임시 단어장 데이터 (개발 단계)
    sample_word = Word(
        id="word_1",
        text="天気",
        reading="てんき",
        meaning="날씨",
        part_of_speech="명사",
        difficulty_level="beginner",
        example_sentence="今日は良い天気ですね。",
        example_translation="오늘은 좋은 날씨네요.",
        audio_url="https://example.com/audio/tenki.mp3"
    )
    
    return [
        UserWord(
            word=sample_word,
            added_at=datetime.utcnow(),
            mastery_level=2,
            review_count=5,
            last_reviewed=datetime.utcnow(),
            tags=["날씨", "기본단어"],
            notes="뉴스에서 자주 나오는 단어"
        )
    ]

@router.post("/vocabulary")
async def add_word_to_vocabulary(
    request: AddWordRequest,
    token: str = Depends(oauth2_scheme)
):
    """
    단어장에 단어 추가
    
    새로운 단어를 사용자 단어장에 추가합니다.
    """
    # TODO: 단어 검색 후 단어장에 추가
    
    return {
        "message": f"단어 '{request.word_text}'가 단어장에 추가되었습니다.",
        "word_text": request.word_text,
        "tags": request.tags
    }

@router.put("/vocabulary/{word_id}")
async def update_vocabulary_word(
    word_id: str,
    request: UpdateWordRequest,
    token: str = Depends(oauth2_scheme)
):
    """
    단어장 단어 정보 업데이트
    
    숙련도, 태그, 메모 등을 수정합니다.
    """
    # TODO: 실제 DB 업데이트
    
    return {
        "message": f"단어 {word_id}가 업데이트되었습니다.",
        "updated_fields": request.dict(exclude_unset=True)
    }

@router.delete("/vocabulary/{word_id}")
async def remove_word_from_vocabulary(
    word_id: str,
    token: str = Depends(oauth2_scheme)
):
    """
    단어장에서 단어 제거
    
    사용자 단어장에서 특정 단어를 삭제합니다.
    """
    # TODO: 실제 DB에서 단어 삭제
    
    return {"message": f"단어 {word_id}가 단어장에서 제거되었습니다."}

@router.get("/review")
async def get_review_words(
    count: int = Query(10, ge=1, le=50, description="복습할 단어 개수"),
    mode: str = Query("mixed", description="복습 모드: mixed, new, review"),
    token: str = Depends(oauth2_scheme)
):
    """
    복습할 단어 목록 조회
    
    복습이 필요한 단어들을 우선순위에 따라 반환합니다.
    """
    # TODO: 알고리즘에 따른 복습 단어 선정
    
    # 임시 복습 단어 데이터
    sample_word = Word(
        id="word_1",
        text="天気",
        reading="てんき", 
        meaning="날씨",
        part_of_speech="명사",
        difficulty_level="beginner",
        example_sentence="今日は良い天気ですね。",
        example_translation="오늘은 좋은 날씨네요."
    )
    
    return {
        "words": [
            UserWord(
                word=sample_word,
                added_at=datetime.utcnow(),
                mastery_level=1,
                review_count=3,
                last_reviewed=datetime.utcnow(),
                tags=["날씨"],
                notes="복습 필요"
            )
        ],
        "total_due": 5,
        "mode": mode
    }

@router.post("/review/{word_id}/result")
async def submit_review_result(
    word_id: str,
    correct: bool,
    response_time: Optional[float] = None,
    token: str = Depends(oauth2_scheme)
):
    """
    복습 결과 제출
    
    사용자의 복습 결과를 기록하고 숙련도를 업데이트합니다.
    """
    # TODO: 복습 결과에 따른 숙련도 업데이트 알고리즘
    
    new_mastery_level = 2 if correct else 1
    
    return {
        "message": "복습 결과가 기록되었습니다.",
        "word_id": word_id,
        "correct": correct,
        "new_mastery_level": new_mastery_level,
        "next_review": "2024-01-02T10:00:00Z"
    }

@router.get("/stats")
async def get_vocabulary_stats(token: str = Depends(oauth2_scheme)):
    """
    단어장 통계 조회
    
    총 단어 수, 숙련도별 분포, 복습 통계 등을 반환합니다.
    """
    # TODO: 실제 DB에서 통계 계산
    
    return {
        "total_words": 45,
        "mastery_distribution": {
            "0": 5,   # 새 단어
            "1": 10,  # 익숙하지 않음
            "2": 15,  # 어느정도 알고 있음
            "3": 10,  # 잘 알고 있음
            "4": 4,   # 매우 잘 알고 있음
            "5": 1    # 완전히 숙련됨
        },
        "recent_additions": 8,        # 최근 7일간 추가된 단어
        "due_for_review": 12,         # 복습 예정 단어
        "review_streak": 5,           # 연속 복습 일수
        "favorite_tags": ["날씨", "음식", "교통", "가족"]
    }

@router.get("/tags")
async def get_vocabulary_tags(token: str = Depends(oauth2_scheme)):
    """
    사용자 단어장 태그 목록 조회
    
    사용자가 사용한 모든 태그와 각 태그의 단어 개수를 반환합니다.
    """
    # TODO: 실제 DB에서 태그 목록 조회
    
    return {
        "tags": [
            {"name": "날씨", "count": 8},
            {"name": "음식", "count": 12},
            {"name": "교통", "count": 6},
            {"name": "가족", "count": 9},
            {"name": "기본단어", "count": 15}
        ]
    } 