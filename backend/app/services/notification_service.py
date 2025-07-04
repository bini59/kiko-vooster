"""
알림 서비스

알림 생성, 발송, 스케줄 관리, 구독 관리 등의 비즈니스 로직을 담당합니다.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import selectinload

from app.models.notification import (
    NotificationType, NotificationChannel, NotificationStatus,
    NotificationCreate, NotificationUpdate,
    NotificationScheduleCreate, NotificationScheduleUpdate,
    NotificationSubscriptionCreate, NotificationSubscriptionUpdate
)
from app.core.database import get_session
from app.services.email_service import EmailService
from app.services.web_push_service import WebPushService
from app.utils.template_engine import TemplateEngine

# 실제 데이터베이스 테이블 모델 (SQLAlchemy)들은 별도 파일에서 import
# from app.db.models.notification import Notification, NotificationSchedule, NotificationSubscription, NotificationTemplate

logger = logging.getLogger(__name__)


class NotificationService:
    """알림 서비스 클래스"""
    
    def __init__(self):
        """서비스 초기화"""
        self.email_service = EmailService()
        self.web_push_service = WebPushService()
        self.template_engine = TemplateEngine()
    
    # =============================================================================
    # 알림 생성 및 발송
    # =============================================================================
    
    async def create_notification(
        self,
        session: AsyncSession,
        notification_data: NotificationCreate
    ) -> UUID:
        """
        새로운 알림을 생성합니다.
        
        Args:
            session: 데이터베이스 세션
            notification_data: 알림 생성 데이터
            
        Returns:
            생성된 알림의 ID
        """
        try:
            logger.info("알림 생성 시작")
            # 알림 레코드 생성 (실제 DB 모델은 별도 구현 필요)
            notification = Notification(
                user_id=notification_data.user_id,
                type=notification_data.type,
                channel=notification_data.channel,
                title=notification_data.title,
                message=notification_data.message,
                action_url=notification_data.action_url,
                template_variables=notification_data.template_variables,
                metadata=notification_data.metadata,
                status=NotificationStatus.PENDING
            )
            
            session.add(notification)
            await session.commit()
            await session.refresh(notification)
            
            logger.info(f"알림 생성 완료: {notification.id}")
            return notification.id
            
        except Exception as e:
            await session.rollback()
            logger.error(f"알림 생성 실패: {e}")
            raise
    
    async def send_notification(
        self,
        session: AsyncSession,
        notification_id: UUID,
        immediate: bool = True
    ) -> bool:
        """
        알림을 발송합니다.
        
        Args:
            session: 데이터베이스 세션
            notification_id: 알림 ID
            immediate: 즉시 발송 여부
            
        Returns:
            발송 성공 여부
        """
        try:
            logger.info(f"알림 발송 시작: {notification_id}")
            # 알림 조회
            stmt = select(Notification).where(Notification.id == notification_id)
            result = await session.execute(stmt)
            notification = result.scalar_one_or_none()
            
            if not notification:
                logger.error(f"알림을 찾을 수 없음: {notification_id}")
                return False
            
            if notification.status != NotificationStatus.PENDING:
                logger.warning(f"이미 처리된 알림: {notification_id}, 상태: {notification.status}")
                return False
            
            # 채널별 발송 처리
            success = False
            error_message = None
            
            try:
                if notification.channel == NotificationChannel.EMAIL:
                    success = await self._send_email_notification(session, notification)
                elif notification.channel == NotificationChannel.WEB_PUSH:
                    success = await self._send_web_push_notification(session, notification)
                elif notification.channel == NotificationChannel.IN_APP:
                    success = await self._send_in_app_notification(session, notification)
                else:
                    error_message = f"지원하지 않는 채널: {notification.channel}"
                    
            except Exception as e:
                error_message = str(e)
                logger.error(f"알림 발송 실패: {notification_id}, 에러: {e}")
            
            # 상태 업데이트
            new_status = NotificationStatus.SENT if success else NotificationStatus.FAILED
            await self.update_notification_status(
                session, notification_id, new_status, error_message
            )
            
            return success
            
        except Exception as e:
            logger.error(f"알림 발송 처리 실패: {notification_id}, 에러: {e}")
            return False
    
    async def send_bulk_notifications(
        self,
        session: AsyncSession,
        notification_ids: List[UUID],
        batch_size: int = 10
    ) -> Dict[str, int]:
        """
        여러 알림을 일괄 발송합니다.
        
        Args:
            session: 데이터베이스 세션
            notification_ids: 알림 ID 목록
            batch_size: 배치 크기
            
        Returns:
            발송 결과 통계
        """
        results = {"success": 0, "failed": 0, "skipped": 0}
        
        # 배치 단위로 처리
        for i in range(0, len(notification_ids), batch_size):
            batch = notification_ids[i:i + batch_size]
            tasks = []
            
            for notification_id in batch:
                task = self.send_notification(session, notification_id)
                tasks.append(task)
            
            # 병렬 처리
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    results["failed"] += 1
                    logger.error(f"배치 발송 에러: {result}")
                elif result:
                    results["success"] += 1
                else:
                    results["failed"] += 1
            
            # 배치 간 잠시 대기 (API 제한 회피)
            await asyncio.sleep(0.1)
        
        logger.info(f"일괄 발송 완료: {results}")
        return results
    
    # =============================================================================
    # 채널별 발송 구현
    # =============================================================================
    
    async def _send_email_notification(
        self,
        session: AsyncSession,
        notification: "Notification"
    ) -> bool:
        """이메일 알림 발송"""
        try:
            # 사용자 정보 조회 (이메일 주소 필요)
            user = await self._get_user_info(session, notification.user_id)
            if not user or not user.email:
                logger.error(f"사용자 이메일 정보 없음: {notification.user_id}")
                return False
            
            # 템플릿 적용
            template_data = {
                "user_name": user.name,
                "user_email": user.email,
                **notification.template_variables
            }
            
            subject = await self.template_engine.render(
                notification.title, template_data
            )
            html_content = await self.template_engine.render(
                notification.message, template_data
            )
            
            # 이메일 발송
            success = await self.email_service.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                action_url=notification.action_url
            )
            
            if success:
                logger.info(f"이메일 발송 성공: {notification.id}")
            else:
                logger.error(f"이메일 발송 실패: {notification.id}")
            
            return success
            
        except Exception as e:
            logger.error(f"이메일 알림 발송 에러: {e}")
            return False
    
    async def _send_web_push_notification(
        self,
        session: AsyncSession,
        notification: "Notification"
    ) -> bool:
        """웹푸시 알림 발송"""
        try:
            # 사용자의 활성 구독 조회
            subscriptions = await self._get_active_subscriptions(
                session, notification.user_id, notification.type
            )
            
            if not subscriptions:
                logger.warning(f"활성 구독 없음: {notification.user_id}")
                return False
            
            # 템플릿 적용
            user = await self._get_user_info(session, notification.user_id)
            template_data = {
                "user_name": user.name if user else "사용자",
                **notification.template_variables
            }
            
            title = await self.template_engine.render(
                notification.title, template_data
            )
            message = await self.template_engine.render(
                notification.message, template_data
            )
            
            # 모든 구독에 발송
            success_count = 0
            for subscription in subscriptions:
                try:
                    result = await self.web_push_service.send_push(
                        subscription=subscription,
                        title=title,
                        message=message,
                        action_url=notification.action_url,
                        data=notification.metadata
                    )
                    
                    if result:
                        success_count += 1
                    else:
                        # 실패한 구독은 에러 카운트 증가
                        await self._increment_subscription_error(session, subscription.id)
                        
                except Exception as e:
                    logger.error(f"개별 푸시 발송 실패: {subscription.id}, 에러: {e}")
                    await self._increment_subscription_error(session, subscription.id)
            
            # 최소 하나라도 성공하면 성공으로 처리
            success = success_count > 0
            
            if success:
                logger.info(f"웹푸시 발송 성공: {notification.id}, 성공: {success_count}/{len(subscriptions)}")
            else:
                logger.error(f"웹푸시 발송 실패: {notification.id}, 모든 구독 실패")
            
            return success
            
        except Exception as e:
            logger.error(f"웹푸시 알림 발송 에러: {e}")
            return False
    
    async def _send_in_app_notification(
        self,
        session: AsyncSession,
        notification: "Notification"
    ) -> bool:
        """인앱 알림 처리 (WebSocket 또는 실시간 채널)"""
        try:
            # Supabase Realtime 또는 WebSocket을 통한 실시간 알림
            # 실제 구현은 WebSocket 관리자나 Supabase 클라이언트 필요
            
            payload = {
                "id": str(notification.id),
                "type": notification.type,
                "title": notification.title,
                "message": notification.message,
                "action_url": notification.action_url,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # WebSocket 채널에 브로드캐스트 (실제 구현 필요)
            # await websocket_manager.send_to_user(notification.user_id, payload)
            
            logger.info(f"인앱 알림 발송: {notification.id}")
            return True
            
        except Exception as e:
            logger.error(f"인앱 알림 발송 에러: {e}")
            return False
    
    # =============================================================================
    # 알림 스케줄 관리
    # =============================================================================
    
    async def create_notification_schedule(
        self,
        session: AsyncSession,
        user_id: UUID,
        schedule_data: NotificationScheduleCreate
    ) -> UUID:
        """알림 스케줄을 생성합니다."""
        try:
            # 기존 같은 유형의 스케줄이 있으면 비활성화
            await self._deactivate_existing_schedules(session, user_id, schedule_data.type)
            
            # 새 스케줄 생성
            schedule = NotificationSchedule(
                user_id=user_id,
                type=schedule_data.type,
                name=schedule_data.name,
                description=schedule_data.description,
                is_enabled=schedule_data.is_enabled,
                frequency=schedule_data.frequency,
                preferred_time=schedule_data.preferred_time,
                timezone=schedule_data.timezone,
                days_of_week=schedule_data.days_of_week,
                custom_interval_hours=schedule_data.custom_interval_hours,
                conditions=schedule_data.conditions
            )
            
            session.add(schedule)
            await session.commit()
            await session.refresh(schedule)
            
            logger.info(f"알림 스케줄 생성 완료: {schedule.id}")
            return schedule.id
            
        except Exception as e:
            await session.rollback()
            logger.error(f"알림 스케줄 생성 실패: {e}")
            raise
    
    async def update_notification_schedule(
        self,
        session: AsyncSession,
        schedule_id: UUID,
        schedule_data: NotificationScheduleUpdate
    ) -> bool:
        """알림 스케줄을 업데이트합니다."""
        try:
            stmt = (
                update(NotificationSchedule)
                .where(NotificationSchedule.id == schedule_id)
                .values(**schedule_data.dict(exclude_unset=True))
            )
            
            result = await session.execute(stmt)
            await session.commit()
            
            success = result.rowcount > 0
            if success:
                logger.info(f"알림 스케줄 업데이트 완료: {schedule_id}")
            else:
                logger.warning(f"알림 스케줄을 찾을 수 없음: {schedule_id}")
            
            return success
            
        except Exception as e:
            await session.rollback()
            logger.error(f"알림 스케줄 업데이트 실패: {e}")
            return False
    
    async def get_due_notifications(
        self,
        session: AsyncSession,
        limit: int = 100
    ) -> List["NotificationSchedule"]:
        """실행할 시간이 된 알림 스케줄들을 조회합니다."""
        try:
            current_time = datetime.utcnow()
            
            stmt = (
                select(NotificationSchedule)
                .where(
                    and_(
                        NotificationSchedule.is_enabled == True,
                        NotificationSchedule.next_execution <= current_time
                    )
                )
                .limit(limit)
            )
            
            result = await session.execute(stmt)
            schedules = result.scalars().all()
            
            logger.info(f"실행 대기 스케줄 조회: {len(schedules)}개")
            return list(schedules)
            
        except Exception as e:
            logger.error(f"스케줄 조회 실패: {e}")
            return []
    
    async def execute_scheduled_notification(
        self,
        session: AsyncSession,
        schedule: "NotificationSchedule"
    ) -> bool:
        """스케줄된 알림을 실행합니다."""
        try:
            # 실행 조건 확인
            if not await self._check_execution_conditions(session, schedule):
                logger.info(f"실행 조건 미충족, 건너뛰기: {schedule.id}")
                return False
            
            # 사용자 정보 조회
            user = await self._get_user_info(session, schedule.user_id)
            if not user:
                logger.error(f"사용자 정보 없음: {schedule.user_id}")
                return False
            
            # 템플릿 데이터 준비
            template_data = await self._prepare_template_data(session, user, schedule)
            
            # 알림 타입별 맞춤 알림 생성
            notifications = await self._create_scheduled_notifications(
                session, schedule, template_data
            )
            
            # 알림 발송
            success_count = 0
            for notification_id in notifications:
                if await self.send_notification(session, notification_id):
                    success_count += 1
            
            # 스케줄 실행 기록 업데이트
            await self._update_schedule_execution(session, schedule.id)
            
            success = success_count > 0
            logger.info(f"스케줄 실행 완료: {schedule.id}, 성공: {success_count}/{len(notifications)}")
            
            return success
            
        except Exception as e:
            logger.error(f"스케줄 실행 실패: {schedule.id}, 에러: {e}")
            return False
    
    # =============================================================================
    # 구독 관리
    # =============================================================================
    
    async def create_push_subscription(
        self,
        session: AsyncSession,
        user_id: UUID,
        subscription_data: NotificationSubscriptionCreate
    ) -> UUID:
        """웹푸시 구독을 생성합니다."""
        try:
            # 기존 같은 endpoint 구독이 있으면 업데이트
            existing = await self._get_subscription_by_endpoint(
                session, subscription_data.endpoint
            )
            
            if existing:
                # 기존 구독 업데이트
                stmt = (
                    update(NotificationSubscription)
                    .where(NotificationSubscription.id == existing.id)
                    .values(
                        user_id=user_id,
                        p256dh_key=subscription_data.p256dh_key,
                        auth_key=subscription_data.auth_key,
                        user_agent=subscription_data.user_agent,
                        browser_name=subscription_data.browser_name,
                        browser_version=subscription_data.browser_version,
                        device_type=subscription_data.device_type,
                        notification_types=subscription_data.notification_types,
                        is_active=True,
                        error_count=0,
                        last_used_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                )
                await session.execute(stmt)
                await session.commit()
                
                logger.info(f"기존 구독 업데이트: {existing.id}")
                return existing.id
            else:
                # 새 구독 생성
                subscription = NotificationSubscription(
                    user_id=user_id,
                    endpoint=subscription_data.endpoint,
                    p256dh_key=subscription_data.p256dh_key,
                    auth_key=subscription_data.auth_key,
                    user_agent=subscription_data.user_agent,
                    browser_name=subscription_data.browser_name,
                    browser_version=subscription_data.browser_version,
                    device_type=subscription_data.device_type,
                    notification_types=subscription_data.notification_types,
                    permission_granted_at=datetime.utcnow(),
                    last_used_at=datetime.utcnow()
                )
                
                session.add(subscription)
                await session.commit()
                await session.refresh(subscription)
                
                logger.info(f"새 구독 생성: {subscription.id}")
                return subscription.id
                
        except Exception as e:
            await session.rollback()
            logger.error(f"구독 생성 실패: {e}")
            raise
    
    # =============================================================================
    # 유틸리티 메서드
    # =============================================================================
    
    async def update_notification_status(
        self,
        session: AsyncSession,
        notification_id: UUID,
        status: NotificationStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """알림 상태를 업데이트합니다."""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            if status == NotificationStatus.SENT:
                update_data["sent_at"] = datetime.utcnow()
            elif status == NotificationStatus.DELIVERED:
                update_data["delivered_at"] = datetime.utcnow()
            elif status == NotificationStatus.OPENED:
                update_data["opened_at"] = datetime.utcnow()
            elif status == NotificationStatus.FAILED:
                update_data["failure_reason"] = error_message
                # 재시도 횟수 증가
                stmt = select(Notification.retry_count).where(Notification.id == notification_id)
                result = await session.execute(stmt)
                current_count = result.scalar() or 0
                update_data["retry_count"] = current_count + 1
            
            stmt = (
                update(Notification)
                .where(Notification.id == notification_id)
                .values(**update_data)
            )
            
            result = await session.execute(stmt)
            await session.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            await session.rollback()
            logger.error(f"알림 상태 업데이트 실패: {e}")
            return False
    
    async def get_notification_stats(
        self,
        session: AsyncSession,
        user_id: Optional[UUID] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """알림 통계를 조회합니다."""
        try:
            # 기간 설정
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # 기본 쿼리 조건
            where_conditions = [Notification.created_at >= since_date]
            if user_id:
                where_conditions.append(Notification.user_id == user_id)
            
            # 통계 쿼리들 (실제 구현은 SQLAlchemy 쿼리로 대체 필요)
            stats = {
                "total_sent": 0,
                "total_delivered": 0,
                "total_opened": 0,
                "delivery_rate": 0.0,
                "open_rate": 0.0,
                "last_30_days": {}
            }
            
            logger.info(f"알림 통계 조회 완료: {user_id}")
            return stats
            
        except Exception as e:
            logger.error(f"알림 통계 조회 실패: {e}")
            return {}
    
    # =============================================================================
    # 내부 도우미 메서드
    # =============================================================================
    
    async def _get_user_info(self, session: AsyncSession, user_id: UUID):
        """사용자 정보를 조회합니다. (실제 User 모델 연동 필요)"""
        # 실제 구현에서는 User 테이블에서 조회
        pass
    
    async def _get_active_subscriptions(
        self, session: AsyncSession, user_id: UUID, notification_type: str
    ):
        """사용자의 활성 구독 목록을 조회합니다."""
        # 실제 구현 필요
        pass
    
    async def _check_execution_conditions(
        self, session: AsyncSession, schedule: "NotificationSchedule"
    ) -> bool:
        """스케줄 실행 조건을 확인합니다."""
        # 조건별 검증 로직 구현 필요
        return True
    
    async def _prepare_template_data(
        self, session: AsyncSession, user, schedule
    ) -> Dict[str, Any]:
        """템플릿 데이터를 준비합니다."""
        # 사용자별 맞춤 데이터 준비
        return {
            "user_name": user.name,
            "user_email": user.email
        }
    
    async def _create_scheduled_notifications(
        self, session: AsyncSession, schedule, template_data: Dict[str, Any]
    ) -> List[UUID]:
        """스케줄에 따른 알림들을 생성합니다."""
        # 스케줄 타입별 알림 생성 로직
        return []
    
    async def _update_schedule_execution(
        self, session: AsyncSession, schedule_id: UUID
    ):
        """스케줄 실행 기록을 업데이트합니다."""
        # 다음 실행 시간 계산 및 업데이트
        pass 