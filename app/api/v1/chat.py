"""
Chat/Messaging endpoints.
REST API for dialogs and messages.
WebSocket is handled separately.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import NotFoundError, AuthorizationError, ValidationError
from app.models.chat import Dialog, Message
from app.models.ad import Ad, AdStatus
from app.models.user import User
from app.schemas.chat import (
    DialogResponse,
    DialogListResponse,
    DialogDetail,
    DialogCreate,
    MessageCreate,
    MessageResponse,
    ChatBlock,
)
from app.schemas.user import UserResponse
from app.schemas.common import PaginatedResponse, MessageOut
from app.api.deps import get_current_user


router = APIRouter()


async def get_or_create_dialog(
    db: AsyncSession,
    ad_id: int,
    buyer_id: int,
) -> Dialog:
    """Get existing dialog or create new one."""
    # Get ad to find seller
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.deleted_at.is_(None))
    )
    ad = result.scalar_one_or_none()

    if not ad:
        raise NotFoundError("Ad not found", "ad", ad_id)

    if ad.user_id == buyer_id:
        raise ValidationError("Cannot message your own ad")

    seller_id = ad.user_id

    # Check for existing dialog
    result = await db.execute(
        select(Dialog).where(
            Dialog.ad_id == ad_id,
            Dialog.seller_id == seller_id,
            Dialog.buyer_id == buyer_id,
        )
    )
    dialog = result.scalar_one_or_none()

    if not dialog:
        dialog = Dialog(
            ad_id=ad_id,
            seller_id=seller_id,
            buyer_id=buyer_id,
        )
        db.add(dialog)
        await db.flush()

    return dialog


# ============ Dialogs ============

@router.get("/dialogs", response_model=DialogListResponse)
async def list_dialogs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user's dialogs.
    """
    query = select(Dialog).where(
        or_(
            and_(Dialog.seller_id == current_user.id, Dialog.is_seller_deleted == False),
            and_(Dialog.buyer_id == current_user.id, Dialog.is_buyer_deleted == False),
        )
    ).options(
        selectinload(Dialog.ad),
        selectinload(Dialog.seller),
        selectinload(Dialog.buyer),
    ).order_by(Dialog.last_message_at.desc().nullsfirst())

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Count total unread
    from sqlalchemy import case
    unread_query = select(func.sum(
        case(
            (Dialog.seller_id == current_user.id, Dialog.seller_unread_count),
            else_=Dialog.buyer_unread_count,
        )
    )).where(
        or_(
            Dialog.seller_id == current_user.id,
            Dialog.buyer_id == current_user.id,
        )
    )
    unread_result = await db.execute(unread_query)
    unread_total = unread_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    dialogs = result.scalars().all()

    dialog_responses = []
    for dialog in dialogs:
        # Determine other user
        if current_user.id == dialog.seller_id:
            other_user = dialog.buyer
            unread_count = dialog.seller_unread_count
        else:
            other_user = dialog.seller
            unread_count = dialog.buyer_unread_count

        main_image = None
        if dialog.ad.images:
            main_image = dialog.ad.images[0].url if hasattr(dialog.ad, 'images') else None

        dialog_responses.append(DialogResponse(
            id=dialog.id,
            ad_id=dialog.ad_id,
            ad_title=dialog.ad.title,
            ad_main_image=main_image,
            ad_price=f"{dialog.ad.price} {dialog.ad.currency.value}",
            seller_id=dialog.seller_id,
            buyer_id=dialog.buyer_id,
            other_user=UserResponse.model_validate(other_user),
            last_message_text=dialog.last_message_text,
            last_message_at=dialog.last_message_at,
            unread_count=unread_count,
            is_blocked=dialog.is_blocked(),
            created_at=dialog.created_at,
        ))

    return DialogListResponse(
        dialogs=dialog_responses,
        total=total,
        unread_total=unread_total,
    )


@router.post("/dialogs", response_model=DialogResponse, status_code=status.HTTP_201_CREATED)
async def create_dialog(
    data: DialogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start a new dialog about an ad.
    """
    dialog = await get_or_create_dialog(db, data.ad_id, current_user.id)

    # Load relations
    await db.refresh(dialog, ["ad", "seller", "buyer"])

    # Send initial message if provided
    if data.initial_message:
        message = Message(
            dialog_id=dialog.id,
            sender_id=current_user.id,
            text=data.initial_message,
        )
        db.add(message)
        await db.flush()

        # Update dialog
        dialog.last_message_id = message.id
        dialog.last_message_at = message.created_at
        dialog.last_message_text = message.text[:255] if message.text else None
        dialog.increment_unread_count(dialog.seller_id)

    await db.commit()
    await db.refresh(dialog)

    # Determine other user
    other_user = dialog.seller if current_user.id == dialog.buyer_id else dialog.buyer
    unread_count = dialog.get_unread_count(current_user.id)

    return DialogResponse(
        id=dialog.id,
        ad_id=dialog.ad_id,
        ad_title=dialog.ad.title,
        ad_main_image=None,
        ad_price=f"{dialog.ad.price} {dialog.ad.currency.value}",
        seller_id=dialog.seller_id,
        buyer_id=dialog.buyer_id,
        other_user=UserResponse.model_validate(other_user),
        last_message_text=dialog.last_message_text,
        last_message_at=dialog.last_message_at,
        unread_count=unread_count,
        is_blocked=dialog.is_blocked(),
        created_at=dialog.created_at,
    )


@router.get("/dialogs/{dialog_id}", response_model=DialogDetail)
async def get_dialog(
    dialog_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get dialog with messages.
    """
    result = await db.execute(
        select(Dialog).options(
            selectinload(Dialog.ad),
            selectinload(Dialog.seller),
            selectinload(Dialog.buyer),
            selectinload(Dialog.messages).selectinload(Message.sender),
        ).where(Dialog.id == dialog_id)
    )
    dialog = result.scalar_one_or_none()

    if not dialog:
        raise NotFoundError("Dialog not found", "dialog", dialog_id)

    if not dialog.is_participant(current_user.id):
        raise AuthorizationError("Access denied")

    # Check if deleted for this user
    if current_user.id == dialog.seller_id and dialog.is_seller_deleted:
        raise NotFoundError("Dialog not found", "dialog", dialog_id)
    if current_user.id == dialog.buyer_id and dialog.is_buyer_deleted:
        raise NotFoundError("Dialog not found", "dialog", dialog_id)

    # Mark messages as read
    dialog.reset_unread_count(current_user.id)
    for message in dialog.messages:
        if message.sender_id != current_user.id and not message.is_read:
            message.mark_as_read()

    await db.commit()

    # Determine other user
    other_user = dialog.seller if current_user.id == dialog.buyer_id else dialog.buyer

    messages = [
        MessageResponse(
            id=m.id,
            dialog_id=m.dialog_id,
            sender_id=m.sender_id,
            sender=UserResponse.model_validate(m.sender),
            text=m.text,
            attachments=None,
            is_read=m.is_read,
            read_at=m.read_at,
            is_delivered=m.is_delivered,
            delivered_at=m.delivered_at,
            is_system=m.is_system,
            system_type=m.system_type,
            created_at=m.created_at,
        )
        for m in dialog.messages
        if not (
            (m.is_deleted_by_sender and m.sender_id == current_user.id) or
            (m.is_deleted_by_recipient and m.sender_id != current_user.id)
        )
    ]

    return DialogDetail(
        id=dialog.id,
        ad_id=dialog.ad_id,
        ad_title=dialog.ad.title,
        ad_main_image=None,
        ad_price=f"{dialog.ad.price} {dialog.ad.currency.value}",
        seller_id=dialog.seller_id,
        buyer_id=dialog.buyer_id,
        other_user=UserResponse.model_validate(other_user),
        last_message_text=dialog.last_message_text,
        last_message_at=dialog.last_message_at,
        unread_count=0,
        is_blocked=dialog.is_blocked(),
        created_at=dialog.created_at,
        messages=messages,
    )


@router.delete("/dialogs/{dialog_id}", response_model=MessageOut)
async def delete_dialog(
    dialog_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete dialog (soft delete for current user only).
    """
    result = await db.execute(
        select(Dialog).where(Dialog.id == dialog_id)
    )
    dialog = result.scalar_one_or_none()

    if not dialog:
        raise NotFoundError("Dialog not found", "dialog", dialog_id)

    if not dialog.is_participant(current_user.id):
        raise AuthorizationError("Access denied")

    if current_user.id == dialog.seller_id:
        dialog.is_seller_deleted = True
    else:
        dialog.is_buyer_deleted = True

    await db.commit()

    return MessageOut(message="Dialog deleted successfully")


# ============ Messages ============

@router.post("/dialogs/{dialog_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    dialog_id: int,
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a message in a dialog.
    """
    result = await db.execute(
        select(Dialog).where(Dialog.id == dialog_id)
    )
    dialog = result.scalar_one_or_none()

    if not dialog:
        raise NotFoundError("Dialog not found", "dialog", dialog_id)

    if not dialog.is_participant(current_user.id):
        raise AuthorizationError("Access denied")

    if dialog.is_blocked():
        raise ValidationError("Cannot send messages in blocked dialog")

    # Create message
    message = Message(
        dialog_id=dialog_id,
        sender_id=current_user.id,
        text=message_data.text,
        attachments=str(message_data.attachments) if message_data.attachments else None,
    )
    db.add(message)
    await db.flush()

    # Update dialog
    dialog.last_message_id = message.id
    dialog.last_message_at = message.created_at
    dialog.last_message_text = message.text[:255] if message.text else "[Attachment]"

    # Increment unread for other user
    other_user_id = dialog.get_other_user_id(current_user.id)
    dialog.increment_unread_count(other_user_id)

    # Restore dialog if deleted
    if current_user.id == dialog.seller_id:
        dialog.is_seller_deleted = False
    else:
        dialog.is_buyer_deleted = False

    await db.commit()
    await db.refresh(message, ["sender"])

    return MessageResponse(
        id=message.id,
        dialog_id=message.dialog_id,
        sender_id=message.sender_id,
        sender=UserResponse.model_validate(message.sender),
        text=message.text,
        attachments=None,
        is_read=message.is_read,
        read_at=message.read_at,
        is_delivered=message.is_delivered,
        delivered_at=message.delivered_at,
        is_system=message.is_system,
        system_type=message.system_type,
        created_at=message.created_at,
    )


@router.get("/dialogs/{dialog_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    dialog_id: int,
    before_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get messages in a dialog with pagination.
    """
    result = await db.execute(
        select(Dialog).where(Dialog.id == dialog_id)
    )
    dialog = result.scalar_one_or_none()

    if not dialog:
        raise NotFoundError("Dialog not found", "dialog", dialog_id)

    if not dialog.is_participant(current_user.id):
        raise AuthorizationError("Access denied")

    query = select(Message).options(
        selectinload(Message.sender)
    ).where(Message.dialog_id == dialog_id)

    if before_id:
        query = query.where(Message.id < before_id)

    query = query.order_by(Message.id.desc()).limit(limit)

    result = await db.execute(query)
    messages = result.scalars().all()

    # Mark as read
    for message in messages:
        if message.sender_id != current_user.id and not message.is_read:
            message.mark_as_read()

    dialog.reset_unread_count(current_user.id)
    await db.commit()

    return [
        MessageResponse(
            id=m.id,
            dialog_id=m.dialog_id,
            sender_id=m.sender_id,
            sender=UserResponse.model_validate(m.sender),
            text=m.text,
            attachments=None,
            is_read=m.is_read,
            read_at=m.read_at,
            is_delivered=m.is_delivered,
            delivered_at=m.delivered_at,
            is_system=m.is_system,
            system_type=m.system_type,
            created_at=m.created_at,
        )
        for m in reversed(messages)
    ]


@router.post("/dialogs/{dialog_id}/read", response_model=MessageOut)
async def mark_dialog_read(
    dialog_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark all messages in dialog as read.
    """
    result = await db.execute(
        select(Dialog).where(Dialog.id == dialog_id)
    )
    dialog = result.scalar_one_or_none()

    if not dialog:
        raise NotFoundError("Dialog not found", "dialog", dialog_id)

    if not dialog.is_participant(current_user.id):
        raise AuthorizationError("Access denied")

    # Reset unread count
    dialog.reset_unread_count(current_user.id)

    # Mark all unread messages as read
    result = await db.execute(
        select(Message).where(
            Message.dialog_id == dialog_id,
            Message.sender_id != current_user.id,
            Message.is_read == False,
        )
    )
    messages = result.scalars().all()

    for message in messages:
        message.mark_as_read()

    await db.commit()

    return MessageOut(message=f"Marked {len(messages)} messages as read")


# ============ Blocking ============

@router.post("/dialogs/{dialog_id}/block", response_model=MessageOut)
async def block_user_in_dialog(
    dialog_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Block user in a dialog.
    """
    result = await db.execute(
        select(Dialog).where(Dialog.id == dialog_id)
    )
    dialog = result.scalar_one_or_none()

    if not dialog:
        raise NotFoundError("Dialog not found", "dialog", dialog_id)

    if not dialog.is_participant(current_user.id):
        raise AuthorizationError("Access denied")

    if current_user.id == dialog.seller_id:
        dialog.seller_blocked_buyer = True
    else:
        dialog.buyer_blocked_seller = True

    await db.commit()

    return MessageOut(message="User blocked successfully")


@router.post("/dialogs/{dialog_id}/unblock", response_model=MessageOut)
async def unblock_user_in_dialog(
    dialog_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Unblock user in a dialog.
    """
    result = await db.execute(
        select(Dialog).where(Dialog.id == dialog_id)
    )
    dialog = result.scalar_one_or_none()

    if not dialog:
        raise NotFoundError("Dialog not found", "dialog", dialog_id)

    if not dialog.is_participant(current_user.id):
        raise AuthorizationError("Access denied")

    if current_user.id == dialog.seller_id:
        dialog.seller_blocked_buyer = False
    else:
        dialog.buyer_blocked_seller = False

    await db.commit()

    return MessageOut(message="User unblocked successfully")


# ============ Unread Count ============

@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get total unread message count.
    """
    from sqlalchemy import case
    result = await db.execute(
        select(func.sum(
            case(
                (Dialog.seller_id == current_user.id, Dialog.seller_unread_count),
                else_=Dialog.buyer_unread_count,
            )
        )).where(
            or_(
                and_(Dialog.seller_id == current_user.id, Dialog.is_seller_deleted == False),
                and_(Dialog.buyer_id == current_user.id, Dialog.is_buyer_deleted == False),
            )
        )
    )
    count = result.scalar() or 0

    return {"unread_count": count}

