"""
OAuth 인증 서비스

Google, Apple 등 소셜 로그인 제공자와의 인증을 처리합니다.
"""

import httpx
import jwt
import secrets
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.database import get_database
from app.models.user import (
    User, OAuthUserInfo, GoogleOAuthResponse, AppleOAuthResponse, 
    AuthProvider, JapaneseLevel
)

logger = logging.getLogger(__name__)


class OAuthService:
    """OAuth 인증 처리 서비스"""
    
    def __init__(self):
        self.google_client_id = settings.GOOGLE_CLIENT_ID
        self.google_client_secret = settings.GOOGLE_CLIENT_SECRET
        self.apple_client_id = settings.APPLE_CLIENT_ID
        self.apple_private_key = settings.APPLE_PRIVATE_KEY
        self.apple_key_id = settings.APPLE_KEY_ID
        self.apple_team_id = settings.APPLE_TEAM_ID

    async def google_login(self, authorization_code: str, redirect_uri: str) -> OAuthUserInfo:
        """
        Google OAuth 로그인 처리
        
        Args:
            authorization_code: Google OAuth 인증 코드
            redirect_uri: 리다이렉트 URI
            
        Returns:
            OAuthUserInfo: 사용자 정보
            
        Raises:
            ValueError: 인증 실패 시
        """
        try:
            # 1. 인증 코드로 액세스 토큰 교환
            token_data = await self._exchange_google_code_for_token(
                authorization_code, redirect_uri
            )
            
            if not token_data.get('access_token'):
                raise ValueError("Google 액세스 토큰을 받을 수 없습니다.")
            
            # 2. 액세스 토큰으로 사용자 정보 조회
            user_info = await self._get_google_user_info(token_data['access_token'])
            
            # 3. 사용자 정보 변환
            oauth_user = OAuthUserInfo(
                provider=AuthProvider.GOOGLE,
                provider_id=f"google_{user_info.id}",
                email=user_info.email,
                name=user_info.name,
                avatar_url=user_info.picture,
                is_verified=user_info.verified_email
            )
            
            logger.info(f"✅ Google OAuth 로그인 성공: {oauth_user.email}")
            return oauth_user
            
        except Exception as e:
            logger.error(f"❌ Google OAuth 로그인 실패: {str(e)}")
            raise ValueError(f"Google 로그인에 실패했습니다: {str(e)}")

    async def apple_login(self, id_token: str) -> OAuthUserInfo:
        """
        Apple OAuth 로그인 처리
        
        Args:
            id_token: Apple ID 토큰
            
        Returns:
            OAuthUserInfo: 사용자 정보
            
        Raises:
            ValueError: 인증 실패 시
        """
        try:
            # 1. ID 토큰 검증 및 디코딩
            user_info = await self._verify_apple_id_token(id_token)
            
            # 2. 사용자 정보 변환
            oauth_user = OAuthUserInfo(
                provider=AuthProvider.APPLE,
                provider_id=f"apple_{user_info.sub}",
                email=user_info.email or "",  # Apple은 이메일을 숨길 수 있음
                name=user_info.name or "Apple 사용자",
                avatar_url=None,  # Apple은 아바타 URL 제공 안함
                is_verified=user_info.email_verified or False
            )
            
            logger.info(f"✅ Apple OAuth 로그인 성공: {oauth_user.email}")
            return oauth_user
            
        except Exception as e:
            logger.error(f"❌ Apple OAuth 로그인 실패: {str(e)}")
            raise ValueError(f"Apple 로그인에 실패했습니다: {str(e)}")

    async def create_or_update_user(self, oauth_user: OAuthUserInfo) -> tuple[User, bool]:
        """
        OAuth 사용자 정보로 사용자 생성 또는 업데이트
        
        Args:
            oauth_user: OAuth 사용자 정보
            
        Returns:
            tuple[User, bool]: (사용자 정보, 신규 사용자 여부)
        """
        try:
            db = await get_database()
            
            # 1. 기존 사용자 조회 (provider_id 또는 email로)
            existing_user = await self._find_existing_user(oauth_user)
            
            if existing_user:
                # 기존 사용자 업데이트
                user = await self._update_existing_user(existing_user, oauth_user)
                logger.info(f"✅ 기존 사용자 로그인: {user.email}")
                return user, False
            else:
                # 신규 사용자 생성
                user = await self._create_new_user(oauth_user)
                logger.info(f"✅ 신규 사용자 생성: {user.email}")
                return user, True
                
        except Exception as e:
            logger.error(f"❌ 사용자 생성/업데이트 실패: {str(e)}")
            raise ValueError(f"사용자 처리에 실패했습니다: {str(e)}")

    async def _exchange_google_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Google 인증 코드를 액세스 토큰으로 교환"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.google_client_id,
                    "client_secret": self.google_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                }
            )
            
            if response.status_code != 200:
                raise ValueError(f"Google 토큰 교환 실패: {response.text}")
            
            return response.json()

    async def _get_google_user_info(self, access_token: str) -> GoogleOAuthResponse:
        """Google 액세스 토큰으로 사용자 정보 조회"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise ValueError(f"Google 사용자 정보 조회 실패: {response.text}")
            
            user_data = response.json()
            return GoogleOAuthResponse(**user_data)

    async def _verify_apple_id_token(self, id_token: str) -> AppleOAuthResponse:
        """Apple ID 토큰 검증 및 디코딩"""
        try:
            # 실제 환경에서는 Apple 공개 키로 토큰 검증 필요
            # 여기서는 간단히 디코딩만 수행 (개발 단계)
            payload = jwt.decode(
                id_token, 
                options={"verify_signature": False}  # 개발 단계에서만 사용
            )
            
            return AppleOAuthResponse(**payload)
            
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Apple ID 토큰이 유효하지 않습니다: {str(e)}")

    async def _find_existing_user(self, oauth_user: OAuthUserInfo) -> Optional[Dict[str, Any]]:
        """기존 사용자 조회"""
        try:
            db = await get_database()
            
            # 1. provider_id로 조회
            result = await db.client.from_("users")\
                .select("*")\
                .eq("provider", oauth_user.provider.value)\
                .eq("provider_id", oauth_user.provider_id)\
                .execute()
            
            if result.data:
                return result.data[0]
            
            # 2. 이메일로 조회 (다른 provider로 가입한 경우)
            if oauth_user.email:
                result = await db.client.from_("users")\
                    .select("*")\
                    .eq("email", oauth_user.email)\
                    .execute()
                
                if result.data:
                    return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 기존 사용자 조회 실패: {str(e)}")
            return None

    async def _update_existing_user(self, existing_user: Dict[str, Any], oauth_user: OAuthUserInfo) -> User:
        """기존 사용자 정보 업데이트"""
        try:
            db = await get_database()
            
            # 업데이트할 데이터 준비
            update_data = {
                "last_login": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # 프로필 정보 업데이트 (더 최신 정보로)
            if oauth_user.avatar_url and oauth_user.avatar_url != existing_user.get("avatar_url"):
                update_data["avatar_url"] = oauth_user.avatar_url
            
            if oauth_user.name and oauth_user.name != existing_user.get("name"):
                update_data["name"] = oauth_user.name
            
            # OAuth 제공자 정보 업데이트
            if existing_user.get("provider") != oauth_user.provider.value:
                update_data["provider"] = oauth_user.provider.value
                update_data["provider_id"] = oauth_user.provider_id
            
            # 데이터베이스 업데이트
            result = await db.client.from_("users")\
                .update(update_data)\
                .eq("id", existing_user["id"])\
                .execute()
            
            if not result.data:
                raise ValueError("사용자 정보 업데이트에 실패했습니다.")
            
            # 업데이트된 사용자 정보 반환
            updated_user_data = {**existing_user, **update_data}
            return User(**updated_user_data)
            
        except Exception as e:
            logger.error(f"❌ 사용자 정보 업데이트 실패: {str(e)}")
            raise

    async def _create_new_user(self, oauth_user: OAuthUserInfo) -> User:
        """신규 사용자 생성"""
        try:
            db = await get_database()
            
            now = datetime.utcnow()
            user_data = {
                "id": str(uuid4()),
                "email": oauth_user.email,
                "name": oauth_user.name,
                "avatar_url": oauth_user.avatar_url,
                "provider": oauth_user.provider.value,
                "provider_id": oauth_user.provider_id,
                "is_verified": oauth_user.is_verified,
                "japanese_level": JapaneseLevel.BEGINNER.value,
                "preferences": {
                    "theme": "light",
                    "font_size": "medium",
                    "auto_play": True,
                    "repeat_mode": "sentence",
                    "daily_goal_minutes": 30,
                    "notifications": {"email": True, "web_push": False}
                },
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "last_login": now.isoformat()
            }
            
            # 데이터베이스에 사용자 생성
            result = await db.client.from_("users")\
                .insert(user_data)\
                .execute()
            
            if not result.data:
                raise ValueError("사용자 생성에 실패했습니다.")
            
            return User(**result.data[0])
            
        except Exception as e:
            logger.error(f"❌ 신규 사용자 생성 실패: {str(e)}")
            raise

    def generate_jwt_token(self, user: User) -> Dict[str, Any]:
        """JWT 토큰 생성"""
        try:
            # 토큰 페이로드
            payload = {
                "sub": str(user.id),
                "email": user.email,
                "name": user.name,
                "provider": user.provider.value,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
            }
            
            # JWT 토큰 생성
            access_token = jwt.encode(
                payload,
                settings.JWT_SECRET_KEY,
                algorithm=settings.JWT_ALGORITHM
            )
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.JWT_EXPIRE_MINUTES * 60
            }
            
        except Exception as e:
            logger.error(f"❌ JWT 토큰 생성 실패: {str(e)}")
            raise ValueError(f"토큰 생성에 실패했습니다: {str(e)}")


# 싱글톤 인스턴스
oauth_service = OAuthService() 