"""
알림 관리 API 엔드포인트

사용자의 학습 리마인더 알림 설정, 웹푸시 구독 관리, 알림 발송 등을 처리합니다.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.notification import (
    NotificationResponse,
    NotificationCreate,
    NotificationScheduleResponse,
    NotificationScheduleCreate,
    NotificationScheduleUpdate,
    NotificationSubscriptionResponse,
    NotificationSubscriptionCreate,
    NotificationStatus,
    NotificationType,
    NotificationChannel
)
from app.services.notification_service import NotificationService
from app.core.auth import get_current_user
from app.core.database import get_db

router = APIRouter()
notification_service = NotificationService()

# ===================
# 알림 발송 엔드포인트
# ===================

@router.post("/send", response_model=NotificationResponse)
async def send_notification(
    notification: NotificationCreate,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    즉시 알림 발송
    
    - **notification**: 발송할 알림 정보
    - **returns**: 생성된 알림 정보
    """
    try:
        # 권한 확인 (관리자 또는 본인)
        if current_user.role != "admin" and current_user.id != notification.user_id:
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # 백그라운드에서 알림 발송
        background_tasks.add_task(
            notification_service.send_notification,
            notification.user_id,
            notification.type,
            notification.title,
            notification.content,
            notification.channels,
            notification.scheduled_at,
            notification.metadata
        )
        
        # 즉시 알림 레코드 생성하여 반환
        created_notification = await notification_service.create_notification(
            user_id=notification.user_id,
            type=notification.type,
            title=notification.title,
            content=notification.content,
            channels=notification.channels,
            scheduled_at=notification.scheduled_at,
            metadata=notification.metadata
        )
        
        return created_notification
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")

@router.post("/send/reminder")
async def send_learning_reminder(
    user_id: str,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    학습 리마인더 알림 발송
    
    - **user_id**: 대상 사용자 ID
    - **returns**: 발송 성공 메시지
    """
    try:
        # 권한 확인
        if current_user.role != "admin" and current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # 백그라운드에서 학습 리마인더 발송
        background_tasks.add_task(
            notification_service.send_learning_reminder,
            user_id
        )
        
        return {"message": "Learning reminder scheduled successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send learning reminder: {str(e)}")

# ===================
# 알림 조회 엔드포인트
# ===================

@router.get("/", response_model=List[NotificationResponse])
async def get_user_notifications(
    limit: int = 20,
    offset: int = 0,
    status: Optional[NotificationStatus] = None,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    사용자의 알림 목록 조회
    
    - **limit**: 페이지 크기 (기본값: 20)
    - **offset**: 오프셋 (기본값: 0)
    - **status**: 알림 상태 필터 (선택사항)
    - **returns**: 알림 목록
    """
    try:
        notifications = await notification_service.get_user_notifications(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            status=status
        )
        return notifications
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notifications: {str(e)}")

@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    알림을 읽음으로 표시
    
    - **notification_id**: 알림 ID
    - **returns**: 성공 메시지
    """
    try:
        await notification_service.mark_as_read(notification_id, current_user.id)
        return {"message": "Notification marked as read"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark notification as read: {str(e)}")

# ===================
# 알림 스케줄 관리
# ===================

@router.get("/schedules", response_model=List[NotificationScheduleResponse])
async def get_notification_schedules(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    사용자의 알림 스케줄 목록 조회
    
    - **returns**: 알림 스케줄 목록
    """
    try:
        schedules = await notification_service.get_user_schedules(current_user.id)
        return schedules
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notification schedules: {str(e)}")

@router.post("/schedules", response_model=NotificationScheduleResponse)
async def create_notification_schedule(
    schedule: NotificationScheduleCreate,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    새로운 알림 스케줄 생성
    
    - **schedule**: 생성할 스케줄 정보
    - **returns**: 생성된 스케줄 정보
    """
    try:
        created_schedule = await notification_service.create_schedule(
            user_id=current_user.id,
            type=schedule.type,
            channels=schedule.channels,
            schedule_config=schedule.schedule_config,
            is_active=schedule.is_active,
            metadata=schedule.metadata
        )
        return created_schedule
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create notification schedule: {str(e)}")

@router.put("/schedules/{schedule_id}", response_model=NotificationScheduleResponse)
async def update_notification_schedule(
    schedule_id: str,
    schedule: NotificationScheduleUpdate,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    알림 스케줄 수정
    
    - **schedule_id**: 스케줄 ID
    - **schedule**: 수정할 스케줄 정보
    - **returns**: 수정된 스케줄 정보
    """
    try:
        updated_schedule = await notification_service.update_schedule(
            schedule_id=schedule_id,
            user_id=current_user.id,
            **schedule.model_dump(exclude_unset=True)
        )
        return updated_schedule
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update notification schedule: {str(e)}")

@router.delete("/schedules/{schedule_id}")
async def delete_notification_schedule(
    schedule_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    알림 스케줄 삭제
    
    - **schedule_id**: 스케줄 ID
    - **returns**: 성공 메시지
    """
    try:
        await notification_service.delete_schedule(schedule_id, current_user.id)
        return {"message": "Notification schedule deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete notification schedule: {str(e)}")

# ===================
# 웹푸시 구독 관리
# ===================

@router.get("/subscriptions", response_model=List[NotificationSubscriptionResponse])
async def get_push_subscriptions(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    사용자의 웹푸시 구독 목록 조회
    
    - **returns**: 웹푸시 구독 목록
    """
    try:
        subscriptions = await notification_service.get_user_subscriptions(current_user.id)
        return subscriptions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get push subscriptions: {str(e)}")

@router.post("/subscriptions", response_model=NotificationSubscriptionResponse)
async def create_push_subscription(
    subscription: NotificationSubscriptionCreate,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    새로운 웹푸시 구독 생성
    
    - **subscription**: 구독 정보
    - **returns**: 생성된 구독 정보
    """
    try:
        created_subscription = await notification_service.create_subscription(
            user_id=current_user.id,
            endpoint=subscription.endpoint,
            p256dh_key=subscription.p256dh_key,
            auth_key=subscription.auth_key,
            user_agent=subscription.user_agent
        )
        return created_subscription
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create push subscription: {str(e)}")

@router.delete("/subscriptions/{subscription_id}")
async def delete_push_subscription(
    subscription_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    웹푸시 구독 삭제
    
    - **subscription_id**: 구독 ID
    - **returns**: 성공 메시지
    """
    try:
        await notification_service.delete_subscription(subscription_id, current_user.id)
        return {"message": "Push subscription deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete push subscription: {str(e)}")

# ===================
# 관리자 전용 엔드포인트
# ===================

@router.post("/broadcast")
async def broadcast_notification(
    notification: NotificationCreate,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    전체 사용자에게 알림 브로드캐스트 (관리자 전용)
    
    - **notification**: 브로드캐스트할 알림 정보
    - **returns**: 성공 메시지
    """
    try:
        # 관리자 권한 확인
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin permission required")
        
        # 백그라운드에서 브로드캐스트 실행
        background_tasks.add_task(
            notification_service.broadcast_notification,
            notification.type,
            notification.title,
            notification.content,
            notification.channels,
            notification.metadata
        )
        
        return {"message": "Broadcast notification scheduled successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to broadcast notification: {str(e)}")

@router.get("/stats")
async def get_notification_stats(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    알림 통계 조회 (관리자 전용)
    
    - **returns**: 알림 발송 통계
    """
    try:
        # 관리자 권한 확인
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin permission required")
        
        stats = await notification_service.get_notification_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notification stats: {str(e)}") 