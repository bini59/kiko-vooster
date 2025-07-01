"""
스크립트 관련 API 엔드포인트

라디오 스크립트 조회, 문장 싱크, 재생 관리를 담당합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.api.v1.endpoints.auth import oauth2_scheme

router = APIRouter()

# 모델 정의
class Sentence(BaseModel):
    """문장 모델"""
    id: str
    text: str
    reading: Optional[str] = None     # 후리가나
    translation: str
    start_time: float                 # 시작 시간 (초)
    end_time: float                   # 종료 시간 (초)
    difficulty_level: str = "beginner"  # beginner, intermediate, advanced

class Script(BaseModel):
    """스크립트 모델"""
    id: str
    title: str
    description: str
    audio_url: str
    thumbnail_url: Optional[str] = None
    duration: int                     # 총 재생 시간 (초)
    difficulty_level: str = "beginner"
    category: str                     # news, anime, podcast, etc.
    language: str = "japanese"
    created_at: datetime
    sentences: List[Sentence]

class PlaybackProgress(BaseModel):
    """재생 진행률 모델"""
    script_id: str
    current_time: float               # 현재 재생 시간 (초)
    completed_sentences: List[str]    # 완료한 문장 ID 목록
    last_played: datetime

@router.get("/", response_model=List[Script])
async def get_scripts(
    category: Optional[str] = Query(None, description="카테고리 필터"),
    difficulty: Optional[str] = Query(None, description="난이도 필터"),
    limit: int = Query(20, ge=1, le=100, description="결과 개수 제한"),
    offset: int = Query(0, ge=0, description="오프셋")
):
    """
    스크립트 목록 조회
    
    카테고리, 난이도 등으로 필터링된 스크립트 목록을 반환합니다.
    """
    # TODO: 실제 DB에서 스크립트 목록 조회
    
    # 임시 스크립트 데이터 (개발 단계)
    sample_sentences = [
        Sentence(
            id="sent_1",
            text="今日は良い天気ですね。",
            reading="きょうはいいてんきですね。",
            translation="오늘은 좋은 날씨네요.",
            start_time=0.0,
            end_time=3.5,
            difficulty_level="beginner"
        ),
        Sentence(
            id="sent_2", 
            text="明日雨が降るかもしれません。",
            reading="あしたあめがふるかもしれません。",
            translation="내일 비가 올지도 모릅니다.",
            start_time=4.0,
            end_time=8.2,
            difficulty_level="intermediate"
        )
    ]
    
    sample_scripts = [
        Script(
            id="script_1",
            title="NHK 뉴스 - 오늘의 날씨",
            description="일본 전국의 오늘 날씨를 전해드립니다.",
            audio_url="https://example.com/audio/news_weather.mp3",
            thumbnail_url="https://example.com/thumbnails/news.jpg",
            duration=120,
            difficulty_level="beginner",
            category="news",
            language="japanese",
            created_at=datetime.utcnow(),
            sentences=sample_sentences
        )
    ]
    
    return sample_scripts

@router.get("/{script_id}", response_model=Script)
async def get_script(script_id: str):
    """
    특정 스크립트 상세 조회
    
    스크립트 ID로 상세 정보와 모든 문장을 반환합니다.
    """
    # TODO: 실제 DB에서 스크립트 조회
    
    if script_id != "script_1":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="스크립트를 찾을 수 없습니다."
        )
    
    # 임시 스크립트 데이터
    sample_sentences = [
        Sentence(
            id="sent_1",
            text="今日は良い天気ですね。",
            reading="きょうはいいてんきですね。",
            translation="오늘은 좋은 날씨네요.",
            start_time=0.0,
            end_time=3.5,
            difficulty_level="beginner"
        ),
        Sentence(
            id="sent_2",
            text="明日雨が降るかもしれません。",
            reading="あしたあめがふるかもしれません。",
            translation="내일 비가 올지도 모릅니다.",
            start_time=4.0,
            end_time=8.2,
            difficulty_level="intermediate"
        )
    ]
    
    return Script(
        id=script_id,
        title="NHK 뉴스 - 오늘의 날씨",
        description="일본 전국의 오늘 날씨를 전해드립니다.",
        audio_url="https://example.com/audio/news_weather.mp3",
        thumbnail_url="https://example.com/thumbnails/news.jpg",
        duration=120,
        difficulty_level="beginner",
        category="news",
        language="japanese",
        created_at=datetime.utcnow(),
        sentences=sample_sentences
    )

@router.get("/{script_id}/sentences", response_model=List[Sentence])
async def get_script_sentences(script_id: str):
    """
    스크립트의 문장 목록 조회
    
    특정 스크립트의 모든 문장을 타임스탬프와 함께 반환합니다.
    """
    # TODO: 실제 DB에서 문장 목록 조회
    
    # 임시 문장 데이터
    return [
        Sentence(
            id="sent_1",
            text="今日は良い天気ですね。",
            reading="きょうはいいてんきですね。",
            translation="오늘은 좋은 날씨네요.",
            start_time=0.0,
            end_time=3.5,
            difficulty_level="beginner"
        ),
        Sentence(
            id="sent_2",
            text="明日雨が降るかもしれません。",
            reading="あしたあめがふるかもしれません。",
            translation="내일 비가 올지도 모릅니다.",
            start_time=4.0,
            end_time=8.2,
            difficulty_level="intermediate"
        )
    ]

@router.post("/{script_id}/progress")
async def update_playback_progress(
    script_id: str,
    progress: PlaybackProgress,
    token: str = Depends(oauth2_scheme)
):
    """
    재생 진행률 업데이트
    
    사용자의 스크립트 재생 진행률을 저장합니다.
    """
    # TODO: JWT에서 사용자 ID 추출 및 실제 DB 업데이트
    
    return {
        "message": "재생 진행률이 저장되었습니다.",
        "script_id": script_id,
        "current_time": progress.current_time,
        "completed_sentences": len(progress.completed_sentences)
    }

@router.get("/{script_id}/progress")
async def get_playback_progress(
    script_id: str,
    token: str = Depends(oauth2_scheme)
):
    """
    재생 진행률 조회
    
    사용자의 특정 스크립트 재생 진행률을 반환합니다.
    """
    # TODO: 실제 DB에서 진행률 조회
    
    # 임시 진행률 데이터
    return PlaybackProgress(
        script_id=script_id,
        current_time=45.5,
        completed_sentences=["sent_1"],
        last_played=datetime.utcnow()
    )

@router.get("/categories/")
async def get_categories():
    """
    스크립트 카테고리 목록 조회
    
    사용 가능한 모든 카테고리를 반환합니다.
    """
    return {
        "categories": [
            {"id": "news", "name": "뉴스", "count": 25},
            {"id": "anime", "name": "애니메이션", "count": 18},
            {"id": "podcast", "name": "팟캐스트", "count": 12},
            {"id": "drama", "name": "드라마", "count": 8},
            {"id": "music", "name": "음악", "count": 15}
        ]
    }

@router.post("/{script_id}/bookmark")
async def bookmark_script(
    script_id: str,
    token: str = Depends(oauth2_scheme)
):
    """
    스크립트 북마크 추가
    
    사용자의 북마크 목록에 스크립트를 추가합니다.
    """
    # TODO: 실제 북마크 추가 로직
    
    return {"message": f"스크립트 {script_id}가 북마크에 추가되었습니다."}

@router.delete("/{script_id}/bookmark")
async def remove_bookmark(
    script_id: str,
    token: str = Depends(oauth2_scheme)
):
    """
    스크립트 북마크 제거
    
    사용자의 북마크 목록에서 스크립트를 제거합니다.
    """
    # TODO: 실제 북마크 제거 로직
    
    return {"message": f"스크립트 {script_id}가 북마크에서 제거되었습니다."} 