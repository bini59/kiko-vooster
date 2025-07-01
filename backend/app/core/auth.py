"""
인증 및 권한 관리

JWT 토큰 검증, 사용자 인증, WebSocket 인증
"""

from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import logging

from app.core.config import settings
from app.core.database import get_database
from app.models.user import User

logger = logging.getLogger(__name__)

# HTTP Bearer 토큰 스키마
security = HTTPBearer(auto_error=False)


async def verify_jwt_token(token: str) -> Optional[dict]:
    """JWT 토큰 검증"""
    try:
        # JWT 토큰 디코딩
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # 사용자 ID 추출
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        return {"user_id": user_id, "payload": payload}
        
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.JWTError as e:
        logger.warning(f"JWT validation failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in token verification: {str(e)}")
        return None


async def get_user_by_id(user_id: UUID) -> Optional[User]:
    """ID로 사용자 조회"""
    try:
        db = await get_database()
        
        result = await db.client.from_("users")\
            .select("*")\
            .eq("id", str(user_id))\
            .single()\
            .execute()
        
        if not result.data:
            return None
        
        return User(**result.data)
        
    except Exception as e:
        logger.error(f"Error getting user by ID: {str(e)}")
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """현재 인증된 사용자 조회 (필수)"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 토큰 검증
    token_data = await verify_jwt_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 사용자 조회
    user = await get_user_by_id(UUID(token_data["user_id"]))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """현재 인증된 사용자 조회 (선택적)"""
    if not credentials:
        return None
    
    # 토큰 검증
    token_data = await verify_jwt_token(credentials.credentials)
    if not token_data:
        return None
    
    # 사용자 조회
    user = await get_user_by_id(UUID(token_data["user_id"]))
    return user


async def get_current_user_websocket(token: str) -> User:
    """WebSocket용 현재 인증된 사용자 조회 (필수)"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 토큰이 필요합니다."
        )
    
    # 토큰 검증
    token_data = await verify_jwt_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다."
        )
    
    # 사용자 조회
    user = await get_user_by_id(UUID(token_data["user_id"]))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다."
        )
    
    return user


async def get_optional_user_websocket(token: Optional[str] = None) -> Optional[User]:
    """WebSocket용 현재 인증된 사용자 조회 (선택적)"""
    if not token:
        return None
    
    # 토큰 검증
    token_data = await verify_jwt_token(token)
    if not token_data:
        return None
    
    # 사용자 조회
    user = await get_user_by_id(UUID(token_data["user_id"]))
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """관리자 권한 필수"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    return current_user


def require_verified(current_user: User = Depends(get_current_user)) -> User:
    """이메일 인증 필수"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이메일 인증이 필요합니다."
        )
    return current_user 