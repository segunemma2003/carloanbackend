"""
Notification service: create notifications and optionally send email/SMS.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.notification import Notification, NotificationPreference, NotificationType
from app.services.email_service import email_service
from app.services.sms_service import sms_service


class NotificationService:
    async def create_notification(
        self,
        db: AsyncSession,
        user_id: int,
        notification_type: NotificationType,
        title: Optional[str] = None,
        body: Optional[str] = None,
        data: Optional[dict] = None,
        send_channel: Optional[list[str]] = None,
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            body=body,
            data=data,
        )
        db.add(notif)
        await db.flush()

        # Load preferences
        result = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == user_id))
        prefs = result.scalar_one_or_none()

        # Dispatch via channels respecting preferences
        if prefs is None:
            # default: send email
            prefs_email = True
            prefs_sms = False
        else:
            prefs_email = prefs.email
            prefs_sms = prefs.sms

        # Fire-and-forget sends (do not await heavy IO here)
        if send_channel is None or "email" in send_channel:
            if prefs_email:
                try:
                    # schedule email
                    import asyncio

                    asyncio.create_task(
                        email_service.send_welcome_email(to_email=await self._get_user_email(db, user_id), user_name=None)
                    )
                except Exception:
                    pass

        if send_channel is None or "sms" in send_channel:
            if prefs_sms:
                try:
                    import asyncio

                    # we don't have the phone here; in real impl pass phone
                    # asyncio.create_task(sms_service.send_verification_code(phone))
                except Exception:
                    pass

        await db.commit()
        await db.refresh(notif)
        return notif

    async def _get_user_email(self, db: AsyncSession, user_id: int) -> Optional[str]:
        from app.models.user import User

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return getattr(user, "email", None) if user else None


notification_service = NotificationService()
"""Notification service: create notifications and dispatch according to preferences."""
from typing import Optional
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.notification import Notification, NotificationPreference, NotificationType
from app.models.user import User
from app.services.email_service import email_service
from app.services.sms_service import sms_service


class NotificationService:
    async def create_notification(
        self,
        db: AsyncSession,
        user_id: int,
        type: NotificationType,
        title: Optional[str] = None,
        body: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> Notification:
        payload = None
        if data is not None:
            payload = json.dumps(data)

        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            data=payload,
        )
        db.add(notification)
        await db.flush()

        # Fetch preferences
        pref_result = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == user_id))
        prefs = pref_result.scalar_one_or_none()

        # Fetch user contact info
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        # Dispatch email/sms based on preferences
        if prefs and user:
            if type == NotificationType.NEW_MESSAGE and prefs.email_new_message and user.email:
                # Fire-and-forget
                try:
                    import asyncio

                    asyncio.create_task(email_service.send_welcome_email(user.email, user.name))
                except Exception:
                    pass
            if type == NotificationType.NEW_MESSAGE and prefs.sms_new_message and user.phone:
                try:
                    import asyncio

                    asyncio.create_task(sms_service.send_verification_code(user.phone))
                except Exception:
                    pass

        return notification


notification_service = NotificationService()
"""Notification creation service.

Creates Notification DB rows and dispatches email/SMS according to user preferences.
This service is intentionally small and safe if email/SMS providers aren't configured.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.notification import Notification, NotificationPreference, NotificationType
from app.services.email_service import email_service
from app.services.sms_service import sms_service
from app.models.user import User
from app.core.database import get_db


class NotificationService:
    async def create_notification(
        self,
        db: AsyncSession,
        user_id: int,
        notification_type: NotificationType,
        title: Optional[str] = None,
        body: Optional[str] = None,
        meta: Optional[str] = None,
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            body=body,
            meta=meta,
        )
        db.add(notif)
        await db.commit()
        await db.refresh(notif)

        # Attempt to send via email/sms based on preferences
        # Fetch preferences (best-effort)
        try:
            result = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == user_id))
            prefs = result.scalar_one_or_none()
        except Exception:
            prefs = None

        # Fetch user contact
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
        except Exception:
            user = None

        # Fire-and-forget notifications
        if user and prefs:
            if prefs.email_new_message and user.email:
                try:
                    import asyncio

                    asyncio.create_task(email_service.send_welcome_email(to_email=user.email, user_name=user.name))
                except Exception:
                    pass
            if prefs.sms_new_message and user.phone:
                try:
                    import asyncio

                    asyncio.create_task(sms_service.send_verification_code(user.phone))
                except Exception:
                    pass

        return notif


notification_service = NotificationService()
"""
Notification API endpoints.
"""

from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.models.notification import (
    Notification,
    NotificationPreference,
    NotificationType,
)
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationMarkRead,
)
from app.schemas.common import PaginatedResponse, MessageOut
from app.api.deps import get_current_user


router = APIRouter()


@router.get("/", response_model=PaginatedResponse[NotificationResponse])
async def list_notifications(
    unread_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user's notifications with pagination.
    """
    query = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_archived == False,
    )
    
    if unread_only:
        query = query.where(Notification.is_read == False)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(
        Notification.created_at.desc()
    )
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    items = [NotificationResponse.model_validate(n) for n in notifications]
    
    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get notification by ID.
    """
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise NotFoundError("Notification not found", "notification", notification_id)
    
    return NotificationResponse.model_validate(notification)


@router.post("/{notification_id}/read", response_model=MessageOut)
async def mark_notification_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark notification as read.
    """
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise NotFoundError("Notification not found", "notification", notification_id)
    
    notification.mark_as_read()
    await db.commit()
    
    return MessageOut(message="Notification marked as read")


@router.post("/read-all", response_model=MessageOut)
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark all notifications as read.
    """
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
            Notification.is_archived == False,
        )
    )
    notifications = result.scalars().all()
    
    for notification in notifications:
        notification.mark_as_read()
    
    await db.commit()
    
    return MessageOut(message=f"Marked {len(notifications)} notifications as read")


@router.delete("/{notification_id}", response_model=MessageOut)
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Archive (soft delete) a notification.
    """
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise NotFoundError("Notification not found", "notification", notification_id)
    
    notification.archive()
    await db.commit()
    
    return MessageOut(message="Notification deleted")


@router.delete("", response_model=MessageOut)
async def clear_old_notifications(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Archive (delete) old read notifications.
    """
    from datetime import timedelta
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read == True,
            Notification.created_at < cutoff_date,
            Notification.is_archived == False,
        )
    )
    notifications = result.scalars().all()
    
    for notification in notifications:
        notification.archive()
    
    await db.commit()
    
    return MessageOut(
        message=f"Archived {len(notifications)} old notifications"
    )


@router.get("/count/unread", response_model=dict)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get count of unread notifications.
    """
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
            Notification.is_archived == False,
        )
    )
    count = result.scalar() or 0
    
    return {"unread_count": count}


# ============ Notification Preferences ============

@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user's notification preferences.
    """
    result = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == current_user.id
        )
    )
    preferences = result.scalar_one_or_none()
    
    if not preferences:
        # Create default preferences
        preferences = NotificationPreference(user_id=current_user.id)
        db.add(preferences)
        await db.commit()
        await db.refresh(preferences)
    
    return NotificationPreferenceResponse.model_validate(preferences)


@router.patch("/preferences", response_model=NotificationPreferenceResponse)
async def update_preferences(
    update_data: NotificationPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update notification preferences.
    """
    result = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == current_user.id
        )
    )
    preferences = result.scalar_one_or_none()
    
    if not preferences:
        preferences = NotificationPreference(user_id=current_user.id)
        db.add(preferences)
        await db.flush()
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(preferences, field, value)
    
    await db.commit()
    await db.refresh(preferences)
    
    return NotificationPreferenceResponse.model_validate(preferences)