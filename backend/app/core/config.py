"""
Kiko API 설정 모듈

환경 변수를 통해 애플리케이션 설정을 관리합니다.
"""

from typing import List
from pydantic import BaseSettings, validator
import os
from pathlib import Path

class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # 기본 설정
    APP_NAME: str = "Kiko API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS 설정
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    # JWT 설정
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    
    # Supabase 설정
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_ANON_KEY: str = ""
    
    # 데이터베이스 설정
    DATABASE_URL: str = ""
    
    # OAuth 설정
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    APPLE_CLIENT_ID: str = ""
    APPLE_CLIENT_SECRET: str = ""
    
    # Redis 설정 (선택사항)
    REDIS_URL: str = "redis://localhost:6379"
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    
    # 파일 업로드 설정
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_FILE_TYPES: List[str] = [".mp3", ".wav", ".m4a", ".aac"]
    
    # Supabase Storage 설정
    STORAGE_BUCKET: str = "audio-files"
    STORAGE_SIGNED_URL_EXPIRES: int = 14400  # 4시간
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        """CORS origins 검증 및 변환"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """환경 설정 검증"""
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"Environment must be one of {allowed_envs}")
        return v
    
    @validator("JWT_SECRET_KEY")
    def validate_jwt_secret(cls, v):
        """JWT 시크릿 키 검증"""
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        return v
    
    @property
    def is_development(self) -> bool:
        """개발 환경 여부"""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """프로덕션 환경 여부"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_testing(self) -> bool:
        """테스트 환경 여부"""
        return self.ENVIRONMENT == "testing"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# 글로벌 설정 인스턴스
settings = Settings()

def get_settings() -> Settings:
    """설정 인스턴스 반환 (의존성 주입용)"""
    return settings 