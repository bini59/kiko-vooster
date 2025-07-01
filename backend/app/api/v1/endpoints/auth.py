"""
인증 관련 API 엔드포인트

사용자 로그인, 회원가입, JWT 토큰 관리를 담당합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
import jwt
from datetime import datetime, timedelta

from app.core.config import settings

router = APIRouter()

# OAuth2 스킴 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

# 요청/응답 모델
class UserLogin(BaseModel):
    """사용자 로그인 요청 모델"""
    email: str
    password: str

class UserRegister(BaseModel):
    """사용자 회원가입 요청 모델"""
    email: str
    password: str
    name: str
    japanese_level: Optional[str] = "beginner"

class Token(BaseModel):
    """JWT 토큰 응답 모델"""
    access_token: str
    token_type: str
    expires_in: int

class UserProfile(BaseModel):
    """사용자 프로필 모델"""
    id: str
    email: str
    name: str
    japanese_level: str
    created_at: datetime
    last_login: Optional[datetime] = None

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    사용자 회원가입
    
    새로운 사용자를 등록하고 JWT 토큰을 반환합니다.
    """
    # TODO: Supabase를 통한 실제 사용자 등록 구현
    
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
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    현재 사용자 정보 조회
    
    JWT 토큰을 통해 현재 로그인한 사용자의 정보를 반환합니다.
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
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다."
        )
    
    # TODO: Supabase에서 실제 사용자 정보 조회
    # 임시 사용자 정보 (개발 단계)
    return UserProfile(
        id="user_123",
        email=email,
        name="테스트 사용자",
        japanese_level="beginner",
        created_at=datetime.utcnow(),
        last_login=datetime.utcnow()
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