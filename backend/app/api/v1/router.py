"""
Kiko API v1 메인 라우터

모든 API 엔드포인트를 통합하는 메인 라우터입니다.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, scripts, words, users, audio
from app.api.v1 import sync

# 메인 API 라우터 생성
api_router = APIRouter()

# 각 도메인별 라우터 등록
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    users.router,
    prefix="/users", 
    tags=["users"]
)

api_router.include_router(
    scripts.router,
    prefix="/scripts",
    tags=["scripts"]
)

api_router.include_router(
    words.router,
    prefix="/words",
    tags=["vocabulary"]
)

api_router.include_router(
    audio.router,
    prefix="/audio",
    tags=["audio"]
)

# 스크립트-오디오 싱크 매핑 API
api_router.include_router(
    sync.router,
    prefix="/sync",
    tags=["sync"]
) 