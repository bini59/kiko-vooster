"""
인증 관련 API 엔드포인트

OAuth 소셜 로그인, JWT 토큰 관리를 담당합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, ValidationError
from typing import Optional
import jwt
from datetime import datetime, timedelta
import logging

from app.core.config import settings
from app.core.auth import get_current_user
from app.models.user import (
    User, OAuthLoginRequest, AuthResponse, UserProfile,
    AuthProvider
)
from app.services.auth.oauth_service import oauth_service
from app.services.users.user_service import user_service

logger = logging.getLogger(__name__)

router = APIRouter()

# OAuth2 스킴 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

# 기존 호환성을 위한 레거시 모델들
class UserLogin(BaseModel):
    """사용자 로그인 요청 모델 (레거시)"""
    email: str
    password: str

class UserRegister(BaseModel):
    """사용자 회원가입 요청 모델 (레거시)"""
    email: str
    password: str
    name: str
    japanese_level: Optional[str] = "beginner"

class Token(BaseModel):
    """JWT 토큰 응답 모델 (레거시)"""
    access_token: str
    token_type: str
    expires_in: int

# =============================================================================
# OAuth 소셜 로그인 엔드포인트
# =============================================================================

@router.post("/oauth/login", response_model=AuthResponse)
async def oauth_login(login_request: OAuthLoginRequest):
    """
    OAuth 소셜 로그인 (Google, Apple)
    
    OAuth 제공자를 통한 사용자 인증 및 로그인을 처리합니다.
    """
    try:
        oauth_user = None
        
        # 제공자별 OAuth 처리
        if login_request.provider == AuthProvider.GOOGLE:
            if not login_request.authorization_code or not login_request.redirect_uri:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Google 로그인에는 authorization_code와 redirect_uri가 필요합니다."
                )
            
            oauth_user = await oauth_service.google_login(
                login_request.authorization_code,
                login_request.redirect_uri
            )
            
        elif login_request.provider == AuthProvider.APPLE:
            if not login_request.id_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Apple 로그인에는 id_token이 필요합니다."
                )
            
            oauth_user = await oauth_service.apple_login(login_request.id_token)
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="지원하지 않는 OAuth 제공자입니다."
            )
        
        # 사용자 생성 또는 업데이트
        user, is_new_user = await oauth_service.create_or_update_user(oauth_user)
        
        # JWT 토큰 생성
        token_data = oauth_service.generate_jwt_token(user)
        
        logger.info(f"✅ OAuth 로그인 성공: {user.email} ({'신규' if is_new_user else '기존'} 사용자)")
        
        return AuthResponse(
            access_token=token_data["access_token"],
            token_type=token_data["token_type"],
            expires_in=token_data["expires_in"],
            user=user,
            is_new_user=is_new_user
        )
        
    except ValueError as e:
        # OAuth 서비스에서 발생한 에러
        logger.warning(f"⚠️ OAuth 로그인 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # 예상치 못한 에러
        logger.error(f"❌ OAuth 로그인 중 서버 에러: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 처리 중 오류가 발생했습니다."
        )


# =============================================================================
# 레거시 회원가입 엔드포인트 (이메일 기반)
# =============================================================================

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    사용자 회원가입 (레거시)
    
    이메일 기반 사용자 등록 - OAuth 로그인 권장
    """
    # TODO: Supabase를 통한 실제 사용자 등록 구현
    # 현재는 OAuth 로그인을 우선적으로 사용하는 것을 권장
    
    logger.warning("⚠️ 레거시 회원가입 엔드포인트 사용됨 - OAuth 로그인 권장")
    
    # 임시 응답 (개발 단계)
    token_data = {
        "sub": user_data.email,
        "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    }
    
    access_token = jwt.encode(
        token_data, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_EXPIRE_MINUTES * 60
    }

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """
    사용자 로그인
    
    이메일과 비밀번호로 로그인하고 JWT 토큰을 반환합니다.
    """
    # TODO: Supabase를 통한 실제 사용자 인증 구현
    
    # 임시 인증 로직 (개발 단계)
    if user_data.email == "test@example.com" and user_data.password == "password":
        token_data = {
            "sub": user_data.email,
            "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        }
        
        access_token = jwt.encode(
            token_data, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_MINUTES * 60
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 표준 토큰 엔드포인트
    
    OAuth2PasswordRequestForm을 사용한 로그인
    """
    user_data = UserLogin(email=form_data.username, password=form_data.password)
    return await login(user_data)

@router.get("/me", response_model=UserProfile)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    현재 사용자 정보 조회
    
    JWT 토큰을 통해 현재 로그인한 사용자의 정보를 반환합니다.
    """
    try:
        # UserService를 통해 프로필 조회
        profile = await user_service.get_user_profile(current_user.id)
        
        if not profile:
            logger.error(f"❌ 사용자 프로필 조회 실패: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자 프로필을 찾을 수 없습니다."
            )
        
        logger.info(f"✅ 사용자 정보 조회 성공: {current_user.email}")
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 사용자 정보 조회 중 서버 에러: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 정보 조회 중 오류가 발생했습니다."
        )

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """
    사용자 로그아웃
    
    클라이언트 측에서 토큰을 삭제하도록 안내합니다.
    """
    # JWT는 stateless이므로 서버에서 직접 무효화할 수 없음
    # 실제로는 토큰 블랙리스트나 짧은 만료 시간을 사용
    return {"message": "로그아웃되었습니다. 클라이언트에서 토큰을 삭제해주세요."}

@router.post("/refresh", response_model=Token)
async def refresh_token(token: str = Depends(oauth2_scheme)):
    """
    토큰 갱신
    
    기존 토큰으로 새로운 토큰을 발급받습니다.
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다."
            )
        
        # 새 토큰 생성
        new_token_data = {
            "sub": email,
            "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        }
        
        new_access_token = jwt.encode(
            new_token_data, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_MINUTES * 60
        }
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다."
        ) 