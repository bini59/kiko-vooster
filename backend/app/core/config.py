"""
애플리케이션 설정 관리
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    # 애플리케이션 기본 설정
    APP_NAME: str = Field(default="Kiko Vooster API", description="애플리케이션 이름")
    VERSION: str = Field(default="1.0.0", description="API 버전")
    DESCRIPTION: str = Field(default="일본어 학습 플랫폼 API", description="API 설명")
    
    # 환경 설정
    ENVIRONMENT: str = Field(default="development", description="실행 환경 (development, staging, production)")
    DEBUG: bool = Field(default=False, description="디버그 모드 활성화")
    
    @validator("DEBUG", pre=True)
    def parse_debug(cls, v):
        """환경변수에서 DEBUG 값을 적절히 파싱"""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)
    
    # 서버 설정
    HOST: str = Field(default="0.0.0.0", description="서버 호스트")
    PORT: int = Field(default=8000, description="서버 포트")
    WORKERS: int = Field(default=1, description="Uvicorn 워커 수")
    
    # CORS 설정
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "https://kiko-vooster.vercel.app"
        ],
        description="허용할 CORS 도메인들"
    )
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """환경변수에서 쉼표로 구분된 CORS origins 파싱"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    # Supabase 설정
    SUPABASE_URL: str = Field(..., description="Supabase 프로젝트 URL")
    SUPABASE_ANON_KEY: str = Field(..., description="Supabase 익명 키")
    SUPABASE_SERVICE_KEY: Optional[str] = Field(None, description="Supabase 서비스 키 (관리자용)")
    
    # JWT 설정
    JWT_SECRET_KEY: str = Field(..., description="JWT 토큰 서명용 비밀 키")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT 알고리즘")
    JWT_EXPIRE_MINUTES: int = Field(default=1440, description="JWT 토큰 만료 시간 (분)")
    
    # OAuth 설정
    GOOGLE_CLIENT_ID: Optional[str] = Field(None, description="Google OAuth 클라이언트 ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(None, description="Google OAuth 클라이언트 시크릿")
    APPLE_CLIENT_ID: Optional[str] = Field(None, description="Apple OAuth 클라이언트 ID")
    APPLE_TEAM_ID: Optional[str] = Field(None, description="Apple 팀 ID")
    APPLE_KEY_ID: Optional[str] = Field(None, description="Apple 키 ID")
    APPLE_PRIVATE_KEY: Optional[str] = Field(None, description="Apple 개인 키")
    
    # 로깅 설정
    LOG_LEVEL: str = Field(default="INFO", description="로그 레벨")
    LOG_FORMAT: str = Field(default="json", description="로그 포맷 (json, text)")
    
    # 파일 업로드 설정
    MAX_UPLOAD_SIZE: int = Field(default=50 * 1024 * 1024, description="최대 업로드 파일 크기 (50MB)")
    ALLOWED_AUDIO_FORMATS: List[str] = Field(
        default=["mp3", "wav", "m4a", "flac"],
        description="허용할 오디오 파일 형식들"
    )
    
    # 캐시 설정
    REDIS_URL: Optional[str] = Field(None, description="Redis 연결 URL")
    CACHE_TTL: int = Field(default=300, description="기본 캐시 TTL (초)")
    
    # 모니터링 설정
    SENTRY_DSN: Optional[str] = Field(None, description="Sentry DSN")
    ENABLE_METRICS: bool = Field(default=True, description="메트릭 수집 활성화")
    
    # 개발/테스트 설정
    ENABLE_API_DOCS: bool = Field(default=True, description="API 문서 활성화")
    ENABLE_OPENAPI: bool = Field(default=True, description="OpenAPI 스키마 활성화")
    
    @property
    def is_development(self) -> bool:
        """개발 환경 여부"""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """프로덕션 환경 여부"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_testing(self) -> bool:
        """테스트 환경 여부"""
        return self.ENVIRONMENT.lower() in ("test", "testing")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 글로벌 설정 인스턴스
settings = Settings()


def get_settings() -> Settings:
    """설정 인스턴스 반환 (의존성 주입용)"""
    return settings 