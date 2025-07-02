"""
스크립트 관련 API 엔드포인트

라디오 스크립트 조회, 문장 싱크, 재생 관리를 담당합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

from app.core.auth import get_current_user
from app.models.user import User
from app.core.dependencies import get_database

logger = logging.getLogger(__name__)

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

@router.get("/")
async def get_scripts(
    search: Optional[str] = Query(None, description="검색어"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    level: Optional[str] = Query(None, description="난이도 필터"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지 크기")
):
    """
    스크립트 목록 조회
    
    카테고리, 난이도 등으로 필터링된 스크립트 목록을 반환합니다.
    """
    try:
        # Supabase에서 스크립트 목록 조회
        db = await get_database()
        
        # 기본 필터링 조건
        query = db.client.from_("scripts").select("*")
        
        # 검색어가 있으면 제목이나 설명에서 검색
        if search:
            query = query.or_(f"title.ilike.%{search}%,description.ilike.%{search}%")
        
        # 카테고리 필터
        if category:
            query = query.eq("category", category)
        
        # 레벨 필터  
        if level:
            query = query.eq("difficulty_level", level)
        
        # 정렬 및 페이징
        offset = (page - 1) * limit
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        
        result = query.execute()
        
        if not result.data:
            # 데이터가 없을 경우 더미 데이터 반환 (개발용)
            logger.info("DB에 스크립트가 없음. 더미 데이터 반환")
            # ... existing code ...
            sample_sentences = [
                Sentence(
                    id="sent_1",
                    text="今日は良い天気ですね。",
                    reading="きょうはいいてんきですね。",
                    translation="오늘은 좋은 날씨네요.",
                    start_time=0.0,
                    end_time=3.5,
                    difficulty_level="beginner"
                )
            ]
            
            mock_scripts = [
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
            
            return {
                "scripts": mock_scripts,
                "total": len(mock_scripts),
                "page": page,
                "limit": limit,
                "has_next": False
            }
        
        # 총 개수 조회 (페이징용)
        total_query = db.client.from_("scripts").select("id", count="exact")
        if search:
            total_query = total_query.or_(f"title.ilike.%{search}%,description.ilike.%{search}%")
        if category:
            total_query = total_query.eq("category", category)
        if level:
            total_query = total_query.eq("difficulty_level", level)
            
        total_result = total_query.execute()
        total_count = total_result.count or 0
        
        logger.info(f"스크립트 목록 조회 성공: {len(result.data)}개 (전체 {total_count}개)")
        
        return {
            "scripts": result.data,
            "total": total_count,
            "page": page,
            "limit": limit,
            "has_next": (page * limit) < total_count
        }
        
    except Exception as e:
        logger.error(f"스크립트 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="스크립트 목록을 불러올 수 없습니다"
        )

@router.get("/{script_id}", response_model=Script)
async def get_script(script_id: str):
    """
    특정 스크립트 상세 조회
    
    스크립트 ID로 상세 정보와 모든 문장을 반환합니다.
    """
    try:
        # Supabase에서 스크립트 조회
        db = await get_database()
        
        # 스크립트 기본 정보 조회
        script_result = db.client.from_("scripts").select("*").eq("id", script_id).execute()
        
        if not script_result.data:
            # 개발용 더미 데이터 반환
            if script_id == "script_1":
                logger.info(f"DB에 스크립트 없음. 더미 데이터 반환: {script_id}")
                # ... existing dummy data code ...
                sample_sentences = [
                    Sentence(
                        id="sent_1",
                        text="今日は良い天気ですね。",
                        reading="きょうはいいてんきですね。",
                        translation="오늘은 좋은 날씨네요.",
                        start_time=0.0,
                        end_time=3.5,
                        difficulty_level="beginner"
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
            else:
                logger.warning(f"존재하지 않는 스크립트 요청: {script_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="스크립트를 찾을 수 없습니다."
                )
        
        script_data = script_result.data[0]
        
        # 관련 문장들 조회
        sentences_result = db.client.from_("sentences").select("*").eq("script_id", script_id).order("start_time").execute()
        
        logger.info(f"스크립트 조회 성공: {script_id}")
        
        return Script(
            **script_data,
            sentences=sentences_result.data or []
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스크립트 조회 실패: {script_id}, 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="스크립트를 불러올 수 없습니다"
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
    current_user: User = Depends(get_current_user)
):
    """
    재생 진행률 업데이트
    
    사용자의 스크립트 재생 진행률을 저장합니다.
    """
    try:
        # TODO: 실제 DB에 사용자별 재생 진행률 저장
        
        logger.info(f"✅ 재생 진행률 업데이트 성공: {current_user.email}, 스크립트: {script_id}")
        
        return {
            "message": "재생 진행률이 저장되었습니다.",
            "script_id": script_id,
            "user_id": str(current_user.id),
            "current_time": progress.current_time,
            "completed_sentences": len(progress.completed_sentences),
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 재생 진행률 업데이트 중 서버 에러: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="재생 진행률 업데이트 중 오류가 발생했습니다."
        )

@router.get("/{script_id}/progress")
async def get_playback_progress(
    script_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    재생 진행률 조회
    
    사용자의 특정 스크립트 재생 진행률을 반환합니다.
    """
    try:
        # TODO: 실제 DB에서 사용자별 진행률 조회
        
        logger.info(f"✅ 재생 진행률 조회 성공: {current_user.email}, 스크립트: {script_id}")
        
        # 임시 진행률 데이터
        return PlaybackProgress(
            script_id=script_id,
            current_time=45.5,
            completed_sentences=["sent_1"],
            last_played=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"❌ 재생 진행률 조회 중 서버 에러: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="재생 진행률 조회 중 오류가 발생했습니다."
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
    current_user: User = Depends(get_current_user)
):
    """
    스크립트 북마크 추가
    
    사용자의 북마크 목록에 스크립트를 추가합니다.
    """
    try:
        # TODO: 실제 북마크 추가 로직 구현
        
        logger.info(f"✅ 스크립트 북마크 추가 성공: {current_user.email}, 스크립트: {script_id}")
        
        return {
            "message": f"스크립트 {script_id}가 북마크에 추가되었습니다.",
            "user_id": str(current_user.id),
            "script_id": script_id,
            "bookmarked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 스크립트 북마크 추가 중 서버 에러: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="북마크 추가 중 오류가 발생했습니다."
        )

@router.delete("/{script_id}/bookmark")
async def remove_bookmark(
    script_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    스크립트 북마크 제거
    
    사용자의 북마크 목록에서 스크립트를 제거합니다.
    """
    try:
        # TODO: 실제 북마크 제거 로직 구현
        
        logger.info(f"✅ 스크립트 북마크 제거 성공: {current_user.email}, 스크립트: {script_id}")
        
        return {
            "message": f"스크립트 {script_id}가 북마크에서 제거되었습니다.",
            "user_id": str(current_user.id),
            "script_id": script_id,
            "removed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 스크립트 북마크 제거 중 서버 에러: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="북마크 제거 중 오류가 발생했습니다."
        ) 