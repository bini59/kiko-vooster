"""
알림 스케줄링 서비스

주기적인 학습 리마인더 발송, 알림 스케줄 처리 등을 담당합니다.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.services.notification_service import NotificationService
from app.core.database import get_database
from app.models.notification import NotificationType, NotificationChannel

logger = logging.getLogger(__name__)

class SchedulerService:
    """알림 스케줄링 서비스"""
    
    def __init__(self):
        # APScheduler 설정
        self.jobstores = {
            'default': MemoryJobStore()
        }
        self.executors = {
            'default': AsyncIOExecutor(),
        }
        self.job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=self.jobstores,
            executors=self.executors,
            job_defaults=self.job_defaults,
            timezone='Asia/Seoul'
        )
        
        self.notification_service = NotificationService()
        self.is_running = False
    
    async def start(self):
        """스케줄러 시작"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("🕐 알림 스케줄러 시작됨")
            
            # 기본 스케줄 작업 등록
            await self._register_default_jobs()
    
    async def stop(self):
        """스케줄러 중지"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("🛑 알림 스케줄러 중지됨")
    
    async def _register_default_jobs(self):
        """기본 스케줄 작업 등록"""
        try:
            # 1. 일일 학습 리마인더 (매일 오후 7시)
            self.scheduler.add_job(
                func=self._send_daily_learning_reminders,
                trigger=CronTrigger(hour=19, minute=0),  # 19:00
                id='daily_learning_reminder',
                name='일일 학습 리마인더',
                replace_existing=True
            )
            
            # 2. 단어 복습 리마인더 (매주 화, 목, 토 오후 3시)
            self.scheduler.add_job(
                func=self._send_vocabulary_review_reminders,
                trigger=CronTrigger(day_of_week='tue,thu,sat', hour=15, minute=0),
                id='vocabulary_review_reminder',
                name='단어 복습 리마인더',
                replace_existing=True
            )
            
            # 3. 연속 학습 축하 (매일 오후 8시)
            self.scheduler.add_job(
                func=self._send_streak_congratulations,
                trigger=CronTrigger(hour=20, minute=0),  # 20:00
                id='streak_congratulations',
                name='연속 학습 축하',
                replace_existing=True
            )
            
            # 4. 사용자 정의 스케줄 확인 (매 10분마다)
            self.scheduler.add_job(
                func=self._process_custom_schedules,
                trigger=IntervalTrigger(minutes=10),
                id='process_custom_schedules',
                name='사용자 정의 스케줄 처리',
                replace_existing=True
            )
            
            # 5. 알림 상태 정리 (매일 새벽 2시)
            self.scheduler.add_job(
                func=self._cleanup_old_notifications,
                trigger=CronTrigger(hour=2, minute=0),  # 02:00
                id='cleanup_notifications',
                name='오래된 알림 정리',
                replace_existing=True
            )
            
            logger.info("✅ 기본 스케줄 작업 등록 완료")
            
        except Exception as e:
            logger.error(f"❌ 기본 스케줄 작업 등록 실패: {str(e)}")
    
    async def _send_daily_learning_reminders(self):
        """일일 학습 리마인더 발송"""
        logger.info("📚 일일 학습 리마인더 발송 시작")
        
        try:
            db = await get_database()
            
            # 활성 학습 리마인더 스케줄을 가진 사용자 조회
            query = """
                SELECT DISTINCT ns.user_id 
                FROM notification_schedules ns
                WHERE ns.type = 'learning_reminder'
                  AND ns.is_active = true
                  AND ns.schedule_config->>'daily_enabled' = 'true'
            """
            
            result = db.client.rpc('execute_sql', {'query': query}).execute()
            user_ids = [row['user_id'] for row in result.data]
            
            logger.info(f"🎯 {len(user_ids)}명의 사용자에게 일일 학습 리마인더 발송")
            
            # 각 사용자에게 리마인더 발송
            for user_id in user_ids:
                try:
                    await self.notification_service.send_learning_reminder(user_id)
                    logger.debug(f"✅ 사용자 {user_id}에게 일일 리마인더 발송 완료")
                except Exception as e:
                    logger.error(f"❌ 사용자 {user_id} 일일 리마인더 발송 실패: {str(e)}")
            
            logger.info("✅ 일일 학습 리마인더 발송 완료")
            
        except Exception as e:
            logger.error(f"❌ 일일 학습 리마인더 발송 실패: {str(e)}")
    
    async def _send_vocabulary_review_reminders(self):
        """단어 복습 리마인더 발송"""
        logger.info("📖 단어 복습 리마인더 발송 시작")
        
        try:
            db = await get_database()
            
            # 단어장에 단어가 있고 복습 리마인더 활성화된 사용자 조회
            query = """
                SELECT DISTINCT u.id as user_id, COUNT(uw.id) as word_count
                FROM users u
                JOIN user_words uw ON u.id = uw.user_id
                JOIN notification_schedules ns ON u.id = ns.user_id
                WHERE ns.type = 'vocabulary_review'
                  AND ns.is_active = true
                  AND uw.mastery_level < 5
                GROUP BY u.id
                HAVING COUNT(uw.id) >= 5
            """
            
            result = db.client.rpc('execute_sql', {'query': query}).execute()
            users = result.data
            
            logger.info(f"🎯 {len(users)}명의 사용자에게 단어 복습 리마인더 발송")
            
            # 각 사용자에게 복습 리마인더 발송
            for user in users:
                try:
                    await self.notification_service.send_vocabulary_review_reminder(
                        user['user_id'],
                        user['word_count']
                    )
                    logger.debug(f"✅ 사용자 {user['user_id']}에게 복습 리마인더 발송 완료")
                except Exception as e:
                    logger.error(f"❌ 사용자 {user['user_id']} 복습 리마인더 발송 실패: {str(e)}")
            
            logger.info("✅ 단어 복습 리마인더 발송 완료")
            
        except Exception as e:
            logger.error(f"❌ 단어 복습 리마인더 발송 실패: {str(e)}")
    
    async def _send_streak_congratulations(self):
        """연속 학습 축하 알림 발송"""
        logger.info("🔥 연속 학습 축하 알림 발송 시작")
        
        try:
            db = await get_database()
            
            # 7일, 30일, 100일 연속 학습 달성 사용자 조회
            today = datetime.now(timezone.utc).date()
            
            query = """
                SELECT user_id, 
                       COUNT(DISTINCT DATE(session_start)) as streak_days
                FROM learning_sessions
                WHERE session_start >= DATE('now', '-100 days')
                  AND session_duration >= 300  -- 5분 이상 학습
                GROUP BY user_id
                HAVING streak_days IN (7, 30, 100)
            """
            
            result = db.client.rpc('execute_sql', {'query': query}).execute()
            streak_users = result.data
            
            logger.info(f"🎯 {len(streak_users)}명의 사용자에게 연속 학습 축하 발송")
            
            # 각 사용자에게 축하 알림 발송
            for user in streak_users:
                try:
                    await self.notification_service.send_streak_congratulation(
                        user['user_id'],
                        user['streak_days']
                    )
                    logger.debug(f"✅ 사용자 {user['user_id']}에게 {user['streak_days']}일 연속 축하 발송 완료")
                except Exception as e:
                    logger.error(f"❌ 사용자 {user['user_id']} 연속 학습 축하 발송 실패: {str(e)}")
            
            logger.info("✅ 연속 학습 축하 알림 발송 완료")
            
        except Exception as e:
            logger.error(f"❌ 연속 학습 축하 알림 발송 실패: {str(e)}")
    
    async def _process_custom_schedules(self):
        """사용자 정의 스케줄 처리"""
        logger.debug("⚙️ 사용자 정의 스케줄 처리 시작")
        
        try:
            db = await get_database()
            current_time = datetime.now(timezone.utc)
            
            # 발송 시간이 된 사용자 정의 스케줄 조회
            query = """
                SELECT ns.id, ns.user_id, ns.type, ns.schedule_config, ns.metadata
                FROM notification_schedules ns
                WHERE ns.is_active = true
                  AND ns.next_execution <= %s
                  AND ns.type = 'custom'
            """
            
            result = db.client.rpc('execute_sql', {
                'query': query,
                'params': [current_time.isoformat()]
            }).execute()
            
            schedules = result.data
            
            if schedules:
                logger.info(f"🎯 {len(schedules)}개의 사용자 정의 스케줄 처리")
                
                for schedule in schedules:
                    try:
                        await self._execute_custom_schedule(schedule)
                        logger.debug(f"✅ 스케줄 {schedule['id']} 실행 완료")
                    except Exception as e:
                        logger.error(f"❌ 스케줄 {schedule['id']} 실행 실패: {str(e)}")
            
            logger.debug("✅ 사용자 정의 스케줄 처리 완료")
            
        except Exception as e:
            logger.error(f"❌ 사용자 정의 스케줄 처리 실패: {str(e)}")
    
    async def _execute_custom_schedule(self, schedule: Dict[str, Any]):
        """개별 사용자 정의 스케줄 실행"""
        try:
            config = schedule['schedule_config']
            metadata = schedule.get('metadata', {})
            
            # 알림 타입별 처리
            notification_type = config.get('notification_type', 'learning_reminder')
            
            if notification_type == 'learning_reminder':
                await self.notification_service.send_learning_reminder(schedule['user_id'])
            elif notification_type == 'vocabulary_review':
                await self.notification_service.send_vocabulary_review_reminder(schedule['user_id'])
            elif notification_type == 'custom':
                # 사용자 정의 메시지
                title = config.get('title', '학습 리마인더')
                content = config.get('content', '학습을 시작해보세요!')
                channels = config.get('channels', [NotificationChannel.WEB_PUSH])
                
                await self.notification_service.send_notification(
                    user_id=schedule['user_id'],
                    type=NotificationType.LEARNING_REMINDER,
                    title=title,
                    content=content,
                    channels=channels,
                    metadata=metadata
                )
            
            # 다음 실행 시간 계산 및 업데이트
            await self._update_next_execution(schedule['id'], config)
            
        except Exception as e:
            logger.error(f"사용자 정의 스케줄 실행 실패: {str(e)}")
            raise
    
    async def _update_next_execution(self, schedule_id: str, config: Dict[str, Any]):
        """다음 실행 시간 업데이트"""
        try:
            # 반복 주기에 따른 다음 실행 시간 계산
            current_time = datetime.now(timezone.utc)
            repeat_type = config.get('repeat_type', 'none')
            
            if repeat_type == 'daily':
                next_execution = current_time + timedelta(days=1)
            elif repeat_type == 'weekly':
                next_execution = current_time + timedelta(weeks=1)
            elif repeat_type == 'monthly':
                next_execution = current_time + timedelta(days=30)
            else:
                # 일회성 스케줄인 경우 비활성화
                db = await get_database()
                db.client.from_('notification_schedules').update({
                    'is_active': False,
                    'updated_at': current_time.isoformat()
                }).eq('id', schedule_id).execute()
                return
            
            # 다음 실행 시간 업데이트
            db = await get_database()
            db.client.from_('notification_schedules').update({
                'next_execution': next_execution.isoformat(),
                'last_executed': current_time.isoformat(),
                'updated_at': current_time.isoformat()
            }).eq('id', schedule_id).execute()
            
        except Exception as e:
            logger.error(f"다음 실행 시간 업데이트 실패: {str(e)}")
    
    async def _cleanup_old_notifications(self):
        """오래된 알림 정리"""
        logger.info("🧹 오래된 알림 정리 시작")
        
        try:
            db = await get_database()
            
            # 30일 이전의 읽은 알림 삭제
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            
            delete_result = db.client.from_('notifications').delete().filter(
                'created_at', 'lt', cutoff_date.isoformat()
            ).filter(
                'status', 'eq', 'delivered'
            ).filter(
                'read_at', 'is_not', None
            ).execute()
            
            deleted_count = len(delete_result.data) if delete_result.data else 0
            logger.info(f"✅ {deleted_count}개의 오래된 알림 정리 완료")
            
        except Exception as e:
            logger.error(f"❌ 오래된 알림 정리 실패: {str(e)}")
    
    def add_user_schedule(self, user_id: str, schedule_config: Dict[str, Any], schedule_id: str):
        """사용자별 개별 스케줄 추가"""
        try:
            if not self.is_running:
                logger.warning("스케줄러가 실행 중이 아닙니다.")
                return
            
            # 크론 표현식 파싱
            cron_expression = schedule_config.get('cron_expression')
            if cron_expression:
                # 크론 표현식으로 스케줄 등록
                self.scheduler.add_job(
                    func=self._execute_user_schedule,
                    trigger=CronTrigger.from_crontab(cron_expression),
                    id=f"user_schedule_{schedule_id}",
                    name=f"사용자 {user_id} 개별 스케줄",
                    args=[user_id, schedule_config],
                    replace_existing=True
                )
                logger.info(f"✅ 사용자 {user_id} 개별 스케줄 등록: {cron_expression}")
            
        except Exception as e:
            logger.error(f"❌ 사용자 개별 스케줄 등록 실패: {str(e)}")
    
    def remove_user_schedule(self, schedule_id: str):
        """사용자별 개별 스케줄 제거"""
        try:
            job_id = f"user_schedule_{schedule_id}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"✅ 스케줄 {schedule_id} 제거 완료")
        except Exception as e:
            logger.error(f"❌ 스케줄 제거 실패: {str(e)}")
    
    async def _execute_user_schedule(self, user_id: str, schedule_config: Dict[str, Any]):
        """사용자별 개별 스케줄 실행"""
        try:
            notification_type = schedule_config.get('type', 'learning_reminder')
            
            if notification_type == 'learning_reminder':
                await self.notification_service.send_learning_reminder(user_id)
            elif notification_type == 'vocabulary_review':
                await self.notification_service.send_vocabulary_review_reminder(user_id)
            
            logger.debug(f"✅ 사용자 {user_id} 개별 스케줄 실행 완료")
            
        except Exception as e:
            logger.error(f"❌ 사용자 {user_id} 개별 스케줄 실행 실패: {str(e)}")

# 글로벌 스케줄러 인스턴스
_scheduler_service: Optional[SchedulerService] = None

def get_scheduler_service() -> SchedulerService:
    """스케줄러 서비스 인스턴스 반환"""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service

def set_scheduler_service(scheduler_service: SchedulerService):
    """스케줄러 서비스 인스턴스 설정"""
    global _scheduler_service
    _scheduler_service = scheduler_service 