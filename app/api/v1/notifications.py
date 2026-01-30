"""
Notification endpoints: list, get, mark as read, preferences.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.notification import Notification, NotificationPreference
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationMarkRead,
)
from app.schemas.common import PaginatedResponse, MessageOut


router = APIRouter()


@router.get("/", response_model=PaginatedResponse[NotificationResponse])
async def list_notifications(
    unread_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_archived == False,
    )
    if unread_only:
        query = query.where(Notification.is_read == False)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Notification.created_at.desc())
    result = await db.execute(query)
    notifications = result.scalars().all()

    items = [NotificationResponse.model_validate(n) for n in notifications]

    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id))
    notification = result.scalar_one_or_none()
    if not notification:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Notification not found")
    return NotificationResponse.model_validate(notification)


@router.post("/mark-read", response_model=MessageOut)
async def mark_read(
    data: NotificationMarkRead,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Notification).where(Notification.id.in_(data.message_ids), Notification.user_id == current_user.id))
    notifications = result.scalars().all()
    for n in notifications:
        n.mark_as_read()
    await db.commit()
    return MessageOut(message=f"Marked {len(notifications)} messages as read")


@router.delete("/{notification_id}", response_model=MessageOut)
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id))
    notification = result.scalar_one_or_none()
    if not notification:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Notification not found")
    notification.archive()
    await db.commit()
    return MessageOut(message="Notification deleted")


@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == current_user.id))
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = NotificationPreference(user_id=current_user.id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
    return NotificationPreferenceResponse.model_validate(prefs)


@router.patch("/preferences", response_model=NotificationPreferenceResponse)
async def update_preferences(
    update_data: NotificationPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == current_user.id))
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = NotificationPreference(user_id=current_user.id)
        db.add(prefs)
        await db.flush()
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(prefs, field, value)
    await db.commit()
    await db.refresh(prefs)
    return NotificationPreferenceResponse.model_validate(prefs)
"""Notification endpoints (list, get, mark read, preferences)."""
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.notification import Notification, NotificationPreference
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)
from app.schemas.common import MessageOut, PaginatedResponse


router = APIRouter()


@router.get("/", response_model=PaginatedResponse[NotificationResponse])
async def list_notifications(
    unread_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_archived == False,
    )
    if unread_only:
        query = query.where(Notification.is_read == False)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Notification.created_at.desc())

    result = await db.execute(query)
    notifications = result.scalars().all()

    items = [NotificationResponse.model_validate(n) for n in notifications]

    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(notification_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id))
    notification = result.scalar_one_or_none()
    if not notification:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Notification not found")
    return NotificationResponse.model_validate(notification)


@router.post("/read", response_model=MessageOut)
async def mark_read(payload: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    ids = payload.get("notification_ids", [])
    if not ids:
        return MessageOut(message="No notifications specified")

    result = await db.execute(select(Notification).where(Notification.id.in_(ids), Notification.user_id == current_user.id))
    notifications = result.scalars().all()
    for n in notifications:
        n.mark_as_read()
    await db.commit()
    return MessageOut(message=f"Marked {len(notifications)} notifications as read")


@router.delete("/{notification_id}", response_model=MessageOut)
async def delete_notification(notification_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id))
    notification = result.scalar_one_or_none()
    if not notification:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Notification not found")
    notification.archive()
    await db.commit()
    return MessageOut(message="Notification archived")


# Preferences
@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_preferences(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == current_user.id))
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = NotificationPreference(user_id=current_user.id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
    return NotificationPreferenceResponse.model_validate(prefs)


@router.patch("/preferences", response_model=NotificationPreferenceResponse)
async def update_preferences(update_data: NotificationPreferenceUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == current_user.id))
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = NotificationPreference(user_id=current_user.id)
        db.add(prefs)
        await db.flush()

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(prefs, field, value)

    await db.commit()
    await db.refresh(prefs)
    return NotificationPreferenceResponse.model_validate(prefs)
"""Notification endpoints for users."""
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.notification import Notification, NotificationPreference
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
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
    query = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_archived == False,
    )
    if unread_only:
        query = query.where(Notification.is_read == False)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Notification.created_at.desc())
    result = await db.execute(query)
    notifications = result.scalars().all()
    items = [NotificationResponse.model_validate(n) for n in notifications]

    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id)
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
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id)
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise NotFoundError("Notification not found", "notification", notification_id)
    notification.mark_as_read()
    await db.commit()
    return MessageOut(message="Notification marked as read")


@router.delete("/{notification_id}", response_model=MessageOut)
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id)
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise NotFoundError("Notification not found", "notification", notification_id)
    notification.archive()
    await db.commit()
    return MessageOut(message="Notification deleted")


# Preferences
@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_preferences(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == current_user.id))
    preferences = result.scalar_one_or_none()
    if not preferences:
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
    result = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == current_user.id))
    preferences = result.scalar_one_or_none()
    if not preferences:
        preferences = NotificationPreference(user_id=current_user.id)
        db.add(preferences)
        await db.flush()

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(preferences, field, value)

    await db.commit()
    await db.refresh(preferences)
    return NotificationPreferenceResponse.model_validate(preferences)
"""
Notification endpoints: list, get, mark read, delete, preferences.
"""
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.notification import Notification, NotificationPreference
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
    query = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_archived == False,
    )
    if unread_only:
        query = query.where(Notification.is_read == False)

    total_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Notification.created_at.desc())
    result = await db.execute(query)
    notifications = result.scalars().all()

    items = [NotificationResponse.model_validate(n) for n in notifications]

    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id)
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise NotFoundError("Notification not found", "notification", notification_id)
    return NotificationResponse.model_validate(notification)


@router.post("/mark-read", response_model=MessageOut)
async def mark_read(
    body: NotificationMarkRead,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not body.ids:
        return MessageOut(message="No ids provided")

    result = await db.execute(select(Notification).where(Notification.id.in_(body.ids), Notification.user_id == current_user.id))
    notifications = result.scalars().all()
    for n in notifications:
        n.mark_as_read()
    await db.commit()
    return MessageOut(message=f"Marked {len(notifications)} notifications as read")


@router.delete("/{notification_id}", response_model=MessageOut)
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id))
    notification = result.scalar_one_or_none()
    if not notification:
        raise NotFoundError("Notification not found", "notification", notification_id)
    notification.archive()
    await db.commit()
    return MessageOut(message="Notification deleted")


@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == current_user.id))
    preferences = result.scalar_one_or_none()
    if not preferences:
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
    result = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == current_user.id))
    preferences = result.scalar_one_or_none()
    if not preferences:
        preferences = NotificationPreference(user_id=current_user.id)
        db.add(preferences)
        await db.flush()

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(preferences, field, value)

    await db.commit()
    await db.refresh(preferences)
    return NotificationPreferenceResponse.model_validate(preferences)
"""Notification endpoints for AVTO LAIF."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.notification import Notification, NotificationPreference
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
    query = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_archived == False,
    )

    if unread_only:
        query = query.where(Notification.is_read == False)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Notification.created_at.desc())

    result = await db.execute(query)
    notifications = result.scalars().all()
    items = [NotificationResponse.model_validate(n) for n in notifications]

    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(notification_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id))
    notification = result.scalar_one_or_none()
    if not notification:
        raise NotFoundError("Notification not found")
    return NotificationResponse.model_validate(notification)


@router.post("/mark-read", response_model=MessageOut)
async def mark_read(data: NotificationMarkRead, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not data.message_ids:
        return MessageOut(message="No message ids provided")

    result = await db.execute(select(Notification).where(Notification.id.in_(data.message_ids), Notification.user_id == current_user.id))
    notifications = result.scalars().all()
    for n in notifications:
        n.mark_as_read()
    await db.commit()
    return MessageOut(message=f"Marked {len(notifications)} messages as read")


@router.delete("/{notification_id}", response_model=MessageOut)
async def delete_notification(notification_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id))
    notification = result.scalar_one_or_none()
    if not notification:
        raise NotFoundError("Notification not found")
    notification.archive()
    await db.commit()
    return MessageOut(message="Notification deleted")


# Preferences
@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_preferences(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == current_user.id))
    preferences = result.scalar_one_or_none()
    if not preferences:
        preferences = NotificationPreference(user_id=current_user.id)
        db.add(preferences)
        await db.commit()
        await db.refresh(preferences)
    return NotificationPreferenceResponse.model_validate(preferences)


@router.patch("/preferences", response_model=NotificationPreferenceResponse)
async def update_preferences(update_data: NotificationPreferenceUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == current_user.id))
    preferences = result.scalar_one_or_none()
    if not preferences:
        preferences = NotificationPreference(user_id=current_user.id)
        db.add(preferences)
        await db.flush()

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(preferences, field, value)

    await db.commit()
    await db.refresh(preferences)
    return NotificationPreferenceResponse.model_validate(preferences)
