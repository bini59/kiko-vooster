"""
웹푸시 서비스

브라우저 웹푸시 알림 발송 및 관리를 담당합니다.
Web Push Protocol을 사용하여 사용자 브라우저에 실시간 알림을 전송합니다.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import aiohttp
import asyncio
from urllib.parse import urlparse

from pywebpush import webpush, WebPushException
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

from app.core.config import settings
from app.models.notification import WebPushPayload

logger = logging.getLogger(__name__)


class WebPushService:
    """웹푸시 발송 서비스"""
    
    def __init__(self):
        """웹푸시 서비스 초기화"""
        # VAPID 키 설정 (환경변수에서 읽어옴)
        self.vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY', None)
        self.vapid_public_key = getattr(settings, 'VAPID_PUBLIC_KEY', None)
        self.vapid_claims = {
            "sub": getattr(settings, 'VAPID_CONTACT_EMAIL', 'mailto:admin@kiko.com')
        }
        
        # FCM 설정 (Google Firebase Cloud Messaging)
        self.fcm_server_key = getattr(settings, 'FCM_SERVER_KEY', None)
        
        # 웹푸시 기본 설정
        self.default_ttl = 86400  # 24시간 (초)
        self.max_retry_attempts = 3
        self.retry_delay = 1  # 재시도 지연 시간(초)
        
        # VAPID 키가 없으면 자동 생성
        if not self.vapid_private_key or not self.vapid_public_key:
            self._generate_vapid_keys()
    
    async def send_push(
        self,
        subscription: Dict[str, Any],
        title: str,
        message: str,
        action_url: Optional[str] = None,
        icon: Optional[str] = None,
        badge: Optional[str] = None,
        image: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        웹푸시 알림을 발송합니다.
        
        Args:
            subscription: 구독 정보 (endpoint, keys)
            title: 알림 제목
            message: 알림 내용
            action_url: 클릭 시 이동할 URL
            icon: 아이콘 URL
            badge: 배지 URL
            image: 이미지 URL
            data: 추가 데이터
            ttl: Time to Live (초)
            
        Returns:
            발송 성공 여부
        """
        try:
            # 페이로드 생성
            payload = WebPushPayload(
                title=title,
                body=message,
                icon=icon or "/icons/notification-icon.png",
                badge=badge or "/icons/badge-icon.png",
                image=image,
                url=action_url,
                tag="kiko_notification",
                timestamp=int(datetime.utcnow().timestamp()),
                data=data or {}
            )
            
            # 구독 정보 검증
            if not self._validate_subscription(subscription):
                logger.error("유효하지 않은 구독 정보")
                return False
            
            # 푸시 발송
            success = await self._send_web_push_notification(
                subscription, payload, ttl or self.default_ttl
            )
            
            if success:
                logger.info(f"웹푸시 발송 성공: {subscription.get('endpoint', 'unknown')}")
            else:
                logger.error(f"웹푸시 발송 실패: {subscription.get('endpoint', 'unknown')}")
            
            return success
            
        except Exception as e:
            logger.error(f"웹푸시 발송 에러: {e}")
            return False
    
    async def send_learning_reminder_push(
        self,
        subscription: Dict[str, Any],
        user_name: str,
        target_study_time: str = "지금",
        action_url: str = "/study"
    ) -> bool:
        """학습 리마인더 푸시 알림을 발송합니다."""
        try:
            return await self.send_push(
                subscription=subscription,
                title="일본어 학습 시간이에요! 🌸",
                message=f"{user_name}님, {target_study_time}에 학습하기로 하셨는데 아직 시작하지 않으셨네요. 지금 바로 시작해보세요!",
                action_url=action_url,
                data={
                    "type": "learning_reminder",
                    "user_name": user_name,
                    "target_study_time": target_study_time
                }
            )
            
        except Exception as e:
            logger.error(f"학습 리마인더 푸시 발송 실패: {e}")
            return False
    
    async def send_vocabulary_review_push(
        self,
        subscription: Dict[str, Any],
        user_name: str,
        review_words_count: int,
        action_url: str = "/vocabulary/review"
    ) -> bool:
        """단어 복습 리마인더 푸시 알림을 발송합니다."""
        try:
            return await self.send_push(
                subscription=subscription,
                title=f"복습할 단어 {review_words_count}개 📚",
                message=f"단어장에서 {review_words_count}개 단어가 복습을 기다리고 있어요. 지금 바로 복습해보세요!",
                action_url=action_url,
                data={
                    "type": "vocabulary_review",
                    "user_name": user_name,
                    "review_words_count": review_words_count
                }
            )
            
        except Exception as e:
            logger.error(f"단어 복습 푸시 발송 실패: {e}")
            return False
    
    async def send_streak_celebration_push(
        self,
        subscription: Dict[str, Any],
        user_name: str,
        streak_days: int,
        action_url: str = "/study"
    ) -> bool:
        """연속 학습 축하 푸시 알림을 발송합니다."""
        try:
            return await self.send_push(
                subscription=subscription,
                title=f"{streak_days}일 연속 학습 중! 🔥",
                message=f"{user_name}님이 {streak_days}일 연속으로 학습하고 계시네요! 오늘도 연속 기록을 이어가보세요.",
                action_url=action_url,
                data={
                    "type": "streak_reminder",
                    "user_name": user_name,
                    "streak_days": streak_days
                }
            )
            
        except Exception as e:
            logger.error(f"연속 학습 축하 푸시 발송 실패: {e}")
            return False
    
    async def send_bulk_push(
        self,
        subscriptions: List[Dict[str, Any]],
        title: str,
        message: str,
        action_url: Optional[str] = None,
        batch_size: int = 50
    ) -> Dict[str, int]:
        """
        여러 구독에 일괄 푸시 알림을 발송합니다.
        
        Args:
            subscriptions: 구독 정보 목록
            title: 알림 제목
            message: 알림 내용
            action_url: 클릭 시 이동할 URL
            batch_size: 배치 크기
            
        Returns:
            발송 결과 통계
        """
        results = {"success": 0, "failed": 0, "invalid": 0}
        
        # 배치 단위로 처리
        for i in range(0, len(subscriptions), batch_size):
            batch = subscriptions[i:i + batch_size]
            tasks = []
            
            for subscription in batch:
                if self._validate_subscription(subscription):
                    task = self.send_push(
                        subscription=subscription,
                        title=title,
                        message=message,
                        action_url=action_url
                    )
                    tasks.append(task)
                else:
                    results["invalid"] += 1
            
            # 병렬 처리
            if tasks:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        results["failed"] += 1
                        logger.error(f"배치 푸시 발송 에러: {result}")
                    elif result:
                        results["success"] += 1
                    else:
                        results["failed"] += 1
                
                # 배치 간 잠시 대기 (API 제한 회피)
                await asyncio.sleep(0.1)
        
        logger.info(f"일괄 푸시 발송 완료: {results}")
        return results
    
    # =============================================================================
    # 실제 웹푸시 발송 구현
    # =============================================================================
    
    async def _send_web_push_notification(
        self,
        subscription: Dict[str, Any],
        payload: WebPushPayload,
        ttl: int
    ) -> bool:
        """실제 웹푸시 알림을 발송합니다."""
        try:
            # 구독 정보 추출
            endpoint = subscription.get('endpoint')
            p256dh_key = subscription.get('p256dh_key') or subscription.get('keys', {}).get('p256dh')
            auth_key = subscription.get('auth_key') or subscription.get('keys', {}).get('auth')
            
            if not endpoint or not p256dh_key or not auth_key:
                logger.error("필수 구독 정보 누락")
                return False
            
            # 페이로드 JSON 변환
            payload_json = json.dumps(payload.dict(), ensure_ascii=False)
            
            # 재시도 로직과 함께 발송
            for attempt in range(self.max_retry_attempts):
                try:
                    # pywebpush 라이브러리 사용
                    response = webpush(
                        subscription_info={
                            "endpoint": endpoint,
                            "keys": {
                                "p256dh": p256dh_key,
                                "auth": auth_key
                            }
                        },
                        data=payload_json,
                        vapid_private_key=self.vapid_private_key,
                        vapid_claims=self.vapid_claims,
                        ttl=ttl,
                        timeout=10  # 10초 타임아웃
                    )
                    
                    # 성공 응답 확인
                    if 200 <= response.status_code < 300:
                        logger.info(f"웹푸시 발송 성공: {endpoint}")
                        return True
                    elif response.status_code == 410:
                        # 구독 만료
                        logger.warning(f"구독 만료: {endpoint}")
                        return False
                    elif response.status_code == 413:
                        # 페이로드 너무 큼
                        logger.error(f"페이로드 크기 초과: {endpoint}")
                        return False
                    else:
                        logger.warning(f"웹푸시 발송 실패 (재시도 {attempt + 1}): {response.status_code}")
                        
                except WebPushException as e:
                    if e.response and e.response.status_code == 410:
                        # 구독 만료는 재시도하지 않음
                        logger.warning(f"구독 만료: {endpoint}")
                        return False
                    else:
                        logger.warning(f"WebPush 에러 (재시도 {attempt + 1}): {e}")
                
                except Exception as e:
                    logger.warning(f"웹푸시 발송 에러 (재시도 {attempt + 1}): {e}")
                
                # 재시도 대기
                if attempt < self.max_retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # 지수 백오프
            
            logger.error(f"웹푸시 발송 최종 실패: {endpoint}")
            return False
            
        except Exception as e:
            logger.error(f"웹푸시 발송 처리 에러: {e}")
            return False
    
    # =============================================================================
    # FCM 지원 (Firebase Cloud Messaging)
    # =============================================================================
    
    async def _send_fcm_notification(
        self,
        subscription: Dict[str, Any],
        payload: WebPushPayload
    ) -> bool:
        """FCM을 통한 푸시 알림 발송 (Chrome 전용)"""
        try:
            if not self.fcm_server_key:
                logger.warning("FCM 서버 키가 설정되지 않음")
                return False
            
            # FCM 엔드포인트인지 확인
            endpoint = subscription.get('endpoint', '')
            if 'fcm.googleapis.com' not in endpoint:
                return False
            
            # FCM 토큰 추출
            fcm_token = endpoint.split('/')[-1]
            
            # FCM 메시지 구성
            fcm_payload = {
                "to": fcm_token,
                "notification": {
                    "title": payload.title,
                    "body": payload.body,
                    "icon": payload.icon,
                    "click_action": payload.url
                },
                "data": payload.data
            }
            
            # FCM API 호출
            headers = {
                "Authorization": f"key={self.fcm_server_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://fcm.googleapis.com/fcm/send",
                    json=fcm_payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('success', 0) > 0:
                            logger.info(f"FCM 발송 성공: {fcm_token}")
                            return True
                        else:
                            logger.error(f"FCM 발송 실패: {result}")
                            return False
                    else:
                        logger.error(f"FCM API 에러: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"FCM 발송 에러: {e}")
            return False
    
    # =============================================================================
    # VAPID 키 관리
    # =============================================================================
    
    def _generate_vapid_keys(self):
        """VAPID 키 쌍을 자동 생성합니다."""
        try:
            # ECDSA 키 쌍 생성
            private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
            public_key = private_key.public_key()
            
            # 개인키를 PEM 형식으로 변환
            private_pem = private_key.private_bytes(
                encoding=Encoding.PEM,
                format=PrivateFormat.PKCS8,
                encryption_algorithm=NoEncryption()
            )
            
            # 공개키를 PEM 형식으로 변환
            public_pem = public_key.public_bytes(
                encoding=Encoding.PEM,
                format=PrivateFormat.PKCS1
            )
            
            self.vapid_private_key = private_pem.decode('utf-8')
            self.vapid_public_key = public_pem.decode('utf-8')
            
            logger.info("VAPID 키 자동 생성 완료")
            logger.warning("프로덕션 환경에서는 환경변수로 고정된 VAPID 키를 사용하세요!")
            
        except Exception as e:
            logger.error(f"VAPID 키 생성 실패: {e}")
    
    def get_public_vapid_key(self) -> str:
        """클라이언트에서 사용할 공개 VAPID 키를 반환합니다."""
        return self.vapid_public_key or ""
    
    # =============================================================================
    # 유틸리티 메서드
    # =============================================================================
    
    def _validate_subscription(self, subscription: Dict[str, Any]) -> bool:
        """구독 정보의 유효성을 검증합니다."""
        try:
            endpoint = subscription.get('endpoint')
            if not endpoint or not endpoint.startswith('https://'):
                return False
            
            # keys 검증
            keys = subscription.get('keys', {})
            p256dh = keys.get('p256dh') or subscription.get('p256dh_key')
            auth = keys.get('auth') or subscription.get('auth_key')
            
            if not p256dh or not auth:
                return False
            
            # endpoint URL 검증
            parsed = urlparse(endpoint)
            if not parsed.netloc:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"구독 정보 검증 에러: {e}")
            return False
    
    def _get_browser_type(self, endpoint: str) -> str:
        """엔드포인트에서 브라우저 타입을 추출합니다."""
        if 'fcm.googleapis.com' in endpoint:
            return 'chrome'
        elif 'mozilla.com' in endpoint:
            return 'firefox'
        elif 'microsoft.com' in endpoint:
            return 'edge'
        elif 'apple.com' in endpoint:
            return 'safari'
        else:
            return 'unknown'
    
    async def test_push_subscription(self, subscription: Dict[str, Any]) -> bool:
        """구독 정보를 테스트합니다."""
        try:
            return await self.send_push(
                subscription=subscription,
                title="테스트 알림",
                message="푸시 알림 설정이 완료되었습니다! 🎉",
                data={"type": "test"}
            )
            
        except Exception as e:
            logger.error(f"푸시 구독 테스트 실패: {e}")
            return False
    
    def estimate_payload_size(self, payload: WebPushPayload) -> int:
        """페이로드 크기를 추정합니다."""
        try:
            payload_json = json.dumps(payload.dict(), ensure_ascii=False)
            return len(payload_json.encode('utf-8'))
            
        except Exception:
            return 0
    
    def is_payload_too_large(self, payload: WebPushPayload, max_size: int = 4096) -> bool:
        """페이로드가 너무 큰지 확인합니다."""
        return self.estimate_payload_size(payload) > max_size 