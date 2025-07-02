"""
의존성 주입 모듈

FastAPI 의존성들을 정의합니다.
- 데이터베이스 연결
- 인증 관련 의존성
- 공통 유틸리티 의존성
"""

import logging
from typing import Optional, AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.database import SupabaseDatabase
from app.models.user import User
from app.services.users.user_service import UserService
from app.core.database import get_db_manager, DatabaseManager

# 로거 설정
logger = logging.getLogger(__name__)

# JWT 토큰 스키마
security = HTTPBearer()

# 전역 데이터베이스 인스턴스
_database_instance: Optional[SupabaseDatabase] = None

async def get_database() -> SupabaseDatabase:
    """
    데이터베이스 의존성
    
    Supabase 데이터베이스 연결을 반환합니다.
    """
    global _database_instance
    
    if _database_instance is None:
        try:
            _database_instance = SupabaseDatabase(
                url=settings.SUPABASE_URL,
                key=settings.SUPABASE_ANON_KEY
            )
            await _database_instance.connect()
            logger.info("데이터베이스 연결 초기화 완료")
        except Exception as e:
            logger.error(f"데이터베이스 연결 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="데이터베이스에 연결할 수 없습니다"
            )
    
    return _database_instance

async def get_user_service(db: SupabaseDatabase = Depends(get_database)) -> UserService:
    """
    사용자 서비스 의존성
    
    UserService 인스턴스를 반환합니다.
    """
    return UserService(db)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT 액세스 토큰 생성
    
    Args:
        data: 토큰에 포함할 데이터
        expires_delta: 만료 시간 (기본값: 설정값 사용)
    
    Returns:
        JWT 토큰 문자열
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt

def verify_token(token: str) -> dict:
    """
    JWT 토큰 검증
    
    Args:
        token: JWT 토큰 문자열
    
    Returns:
        토큰에서 추출한 페이로드
    
    Raises:
        HTTPException: 토큰이 유효하지 않은 경우
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # 만료 시간 확인
        exp = payload.get("exp")
        if exp is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰에 만료 시간이 없습니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if datetime.utcfromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰이 만료되었습니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
        
    except JWTError as e:
        logger.warning(f"JWT 토큰 검증 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 유효하지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: SupabaseDatabase = Depends(get_database)
) -> User:
    """
    현재 로그인한 사용자 조회
    
    JWT 토큰에서 사용자 정보를 추출하고 검증합니다.
    
    Args:
        credentials: HTTP Bearer 토큰
        db: 데이터베이스 연결
    
    Returns:
        현재 사용자 객체
    
    Raises:
        HTTPException: 인증 실패 시
    """
    # 토큰 검증
    payload = verify_token(credentials.credentials)
    
    # 사용자 정보 추출
    user_identifier = payload.get("sub")
    user_id = payload.get("user_id")
    
    if user_identifier is None:
        logger.warning("토큰에 사용자 식별자가 없음")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰에 사용자 정보가 없습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # 데이터베이스에서 사용자 조회
        user_query = db.client.from_("users")
        
        if user_id:
            # user_id가 있으면 우선 사용
            result = user_query.select("*").eq("id", user_id).execute()
        else:
            # 없으면 이메일로 조회
            result = user_query.select("*").eq("email", user_identifier).execute()
        
        if not result.data:
            logger.warning(f"토큰의 사용자를 DB에서 찾을 수 없음: {user_identifier}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자를 찾을 수 없습니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_data = result.data[0]
        
        # User 객체 생성
        user = User(
            id=user_data["id"],
            email=user_data["email"],
            name=user_data.get("name"),
            profile_image=user_data.get("profile_image"),
            japanese_level=user_data.get("japanese_level"),
            auth_provider=user_data.get("auth_provider"),
            created_at=user_data.get("created_at"),
            updated_at=user_data.get("updated_at")
        )
        
        logger.debug(f"사용자 인증 성공: {user.email}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 조회 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 정보를 조회할 수 없습니다"
        )

async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: SupabaseDatabase = Depends(get_database)
) -> Optional[User]:
    """
    선택적 사용자 인증
    
    토큰이 있으면 사용자를 반환하고, 없으면 None을 반환합니다.
    
    Args:
        credentials: HTTP Bearer 토큰 (선택적)
        db: 데이터베이스 연결
    
    Returns:
        사용자 객체 또는 None
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        # 인증 실패 시 None 반환 (에러 발생시키지 않음)
        return None

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    관리자 권한 확인
    
    현재 사용자가 관리자인지 확인합니다.
    
    Args:
        current_user: 현재 사용자
    
    Returns:
        관리자 사용자 객체
    
    Raises:
        HTTPException: 관리자가 아닌 경우
    """
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        logger.warning(f"관리자 권한 없는 사용자의 접근 시도: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    
    return current_user

async def validate_script_access(
    script_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: SupabaseDatabase = Depends(get_database)
) -> bool:
    """
    스크립트 접근 권한 확인
    
    사용자가 해당 스크립트에 접근할 수 있는지 확인합니다.
    
    Args:
        script_id: 스크립트 ID
        current_user: 현재 사용자 (선택적)
        db: 데이터베이스 연결
    
    Returns:
        접근 가능 여부
    """
    try:
        # 스크립트 존재 여부 확인
        script_result = db.client.from_("scripts").select("id, access_level").eq("id", script_id).execute()
        
        if not script_result.data:
            return False
        
        script_data = script_result.data[0]
        access_level = script_data.get("access_level", "public")
        
        # 공개 스크립트는 누구나 접근 가능
        if access_level == "public":
            return True
        
        # 프리미엄 스크립트는 로그인한 사용자만
        if access_level == "premium" and current_user is not None:
            return True
        
        # 비공개 스크립트는 소유자만
        if access_level == "private" and current_user is not None:
            # 소유자 확인 로직 추가 필요
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"스크립트 접근 권한 확인 실패: {str(e)}")
        return False

def get_database_manager() -> DatabaseManager:
    """데이터베이스 매니저 의존성"""
    return get_db_manager()

# 의존성 클린업
async def cleanup_dependencies():
    """
    애플리케이션 종료 시 의존성들을 정리합니다.
    """
    global _database_instance
    
    if _database_instance:
        try:
            await _database_instance.disconnect()
            _database_instance = None
            logger.info("데이터베이스 연결 정리 완료")
        except Exception as e:
            logger.error(f"데이터베이스 연결 정리 실패: {str(e)}") 