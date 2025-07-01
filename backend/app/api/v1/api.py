"""
API v1 메인 라우터

모든 v1 API 엔드포인트를 여기서 통합 관리합니다.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, scripts, words, users

# 메인 API 라우터 생성
api_router = APIRouter()

# 각 도메인별 라우터 등록
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(scripts.router, prefix="/scripts", tags=["scripts"])
api_router.include_router(words.router, prefix="/words", tags=["words"]) 