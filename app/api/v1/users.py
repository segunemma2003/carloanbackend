"""
User management endpoints.
Profile, sessions, and account management.
"""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import hash_password, verify_password, generate_token_hash
from app.core.exceptions import (
    AuthenticationError,
    NotFoundError,
    ValidationError,
    ConflictError,
)
from app.models.user import User, UserSession, UserRole
from app.models.ad import Ad, AdStatus
from app.schemas.user import (
    UserProfileResponse,
    UserUpdate,
    PasswordChange,
    SessionResponse,
    SessionListResponse,
    UserPublicProfile,
)
from app.schemas.common import MessageOut
from app.api.deps import get_current_user, require_admin


router = APIRouter()


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Get current user's profile.
    """
    return UserProfileResponse.model_validate(current_user)


@router.patch("/me", response_model=UserProfileResponse)
async def update_current_user_profile(
    update_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update current user's profile.
    """
    update_dict = update_data.model_dump(exclude_unset=True)

    # Check phone uniqueness if updating
    if "phone" in update_dict and update_dict["phone"]:
        result = await db.execute(
            select(User).where(
                User.phone == update_dict["phone"],
                User.id != current_user.id,
                User.deleted_at.is_(None),
            )
        )
        if result.scalar_one_or_none():
            raise ConflictError("Phone number already in use")

    for field, value in update_dict.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)

    return UserProfileResponse.model_validate(current_user)


@router.post("/me/change-password", response_model=MessageOut)
async def change_password(
    password_data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Change current user's password.
    """
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise AuthenticationError("Current password is incorrect")

    current_user.password_hash = hash_password(password_data.new_password)
    await db.commit()

    return MessageOut(message="Password changed successfully")


@router.get("/me/sessions", response_model=SessionListResponse)
async def get_user_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get list of active sessions for current user.
    """
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == current_user.id,
            UserSession.revoked == False,
            UserSession.expires_at > datetime.now(timezone.utc),
        ).order_by(UserSession.last_used_at.desc())
    )
    sessions = result.scalars().all()

    return SessionListResponse(
        sessions=[SessionResponse.model_validate(s) for s in sessions],
        total=len(sessions),
    )


@router.delete("/me/sessions/{session_id}", response_model=MessageOut)
async def revoke_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Revoke a specific session.
    """
    result = await db.execute(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise NotFoundError("Session not found", "session", session_id)

    session.revoke()
    await db.commit()

    return MessageOut(message="Session revoked successfully")


@router.delete("/me", response_model=MessageOut)
async def delete_account(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft delete current user's account.
    """
    current_user.soft_delete()
    current_user.is_active = False

    # Revoke all sessions
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == current_user.id,
            UserSession.revoked == False,
        )
    )
    sessions = result.scalars().all()
    for session in sessions:
        session.revoke()

    await db.commit()

    return MessageOut(message="Account deleted successfully")


@router.get("/{user_id}", response_model=UserPublicProfile)
async def get_user_public_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get public profile of a user.
    """
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User not found", "user", user_id)

    # Count active ads
    result = await db.execute(
        select(func.count(Ad.id)).where(
            Ad.user_id == user_id,
            Ad.status == AdStatus.ACTIVE,
            Ad.deleted_at.is_(None),
        )
    )
    ads_count = result.scalar() or 0

    return UserPublicProfile(
        id=user.id,
        name=user.name,
        avatar_url=user.avatar_url,
        account_type=user.account_type,
        is_dealer=user.role == UserRole.DEALER,
        company_name=user.company_name if user.role == UserRole.DEALER else None,
        company_logo_url=user.company_logo_url if user.role == UserRole.DEALER else None,
        company_description=user.company_description if user.role == UserRole.DEALER else None,
        ads_count=ads_count,
        member_since=user.created_at,
        last_seen_at=user.last_seen_at,
    )


# Admin endpoints

@router.get("/", response_model=List[UserProfileResponse])
async def list_users(
    skip: int = 0,
    limit: int = 20,
    role: UserRole = None,
    is_blocked: bool = None,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    List all users (admin only).
    """
    query = select(User).where(User.deleted_at.is_(None))

    if role:
        query = query.where(User.role == role)
    if is_blocked is not None:
        query = query.where(User.is_blocked == is_blocked)

    query = query.offset(skip).limit(limit).order_by(User.created_at.desc())

    result = await db.execute(query)
    users = result.scalars().all()

    return [UserProfileResponse.model_validate(u) for u in users]


@router.post("/{user_id}/block", response_model=MessageOut)
async def block_user(
    user_id: int,
    reason: str = None,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Block a user (admin only).
    """
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User not found", "user", user_id)

    if user.role == UserRole.ADMIN:
        raise ValidationError("Cannot block admin users")

    user.is_blocked = True
    user.blocked_reason = reason
    user.blocked_at = datetime.now(timezone.utc)

    # Revoke all sessions
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.revoked == False,
        )
    )
    sessions = result.scalars().all()
    for session in sessions:
        session.revoke()

    await db.commit()

    return MessageOut(message=f"User {user_id} blocked successfully")


@router.post("/{user_id}/unblock", response_model=MessageOut)
async def unblock_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Unblock a user (admin only).
    """
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User not found", "user", user_id)

    user.is_blocked = False
    user.blocked_reason = None
    user.blocked_at = None

    await db.commit()

    return MessageOut(message=f"User {user_id} unblocked successfully")


@router.patch("/{user_id}/role", response_model=UserProfileResponse)
async def update_user_role(
    user_id: int,
    new_role: UserRole,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Update user role (admin only).
    """
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User not found", "user", user_id)

    if user.id == admin_user.id:
        raise ValidationError("Cannot change own role")

    user.role = new_role
    await db.commit()
    await db.refresh(user)

    return UserProfileResponse.model_validate(user)

