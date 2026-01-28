"""
Authentication endpoints.
Handles registration, login, logout, token refresh, and password reset.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    generate_token_hash,
    create_verification_token,
    create_password_reset_token,
    verify_email_token,
    verify_password_reset_token,
    generate_sms_code,
)
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.models.user import User, UserSession, EmailVerification, PasswordReset
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserProfileResponse,
    TokenResponse,
    RefreshTokenResponse,
    PasswordReset as PasswordResetSchema,
    PasswordResetConfirm,
    EmailVerify,
)
from app.schemas.common import MessageOut
from app.api.deps import get_current_user, get_refresh_token_session, get_client_info


router = APIRouter()


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set authentication cookies."""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        domain=settings.COOKIE_DOMAIN,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        domain=settings.COOKIE_DOMAIN,
        path="/api/v1/auth",  # Only send refresh token to auth endpoints
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear authentication cookies."""
    response.delete_cookie(key="access_token", domain=settings.COOKIE_DOMAIN)
    response.delete_cookie(
        key="refresh_token",
        domain=settings.COOKIE_DOMAIN,
        path="/api/v1/auth",
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user.
    
    - Creates user account
    - Sends email verification
    - Returns tokens and sets cookies
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email, User.deleted_at.is_(None))
    )
    if result.scalar_one_or_none():
        raise ConflictError("Email already registered")

    # Check if phone already exists
    if user_data.phone:
        result = await db.execute(
            select(User).where(User.phone == user_data.phone, User.deleted_at.is_(None))
        )
        if result.scalar_one_or_none():
            raise ConflictError("Phone number already registered")

    # Create user
    user = User(
        email=user_data.email,
        phone=user_data.phone,
        password_hash=hash_password(user_data.password),
        name=user_data.name,
        account_type=user_data.account_type,
    )
    db.add(user)
    await db.flush()

    # Create tokens
    access_token = create_access_token(user.id)
    refresh_token, token_hash, expires_at = create_refresh_token(user.id)

    # Create session
    client_info = get_client_info(request)
    session = UserSession(
        user_id=user.id,
        refresh_token_hash=token_hash,
        user_agent=client_info["user_agent"],
        ip_address=client_info["ip_address"],
        device_type=client_info["device_type"],
        expires_at=expires_at,
    )
    db.add(session)

    # Create email verification token
    verification_token = create_verification_token(user.email)
    email_verification = EmailVerification(
        user_id=user.id,
        token=verification_token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(email_verification)

    await db.commit()
    await db.refresh(user)

    # TODO: Send verification email asynchronously
    # await send_verification_email(user.email, verification_token)

    # Set cookies
    set_auth_cookies(response, access_token, refresh_token)

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserProfileResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Login with email/phone and password.
    
    - Validates credentials
    - Creates new session
    - Returns tokens and sets cookies
    """
    # Find user by email or phone
    result = await db.execute(
        select(User).where(
            or_(
                User.email == credentials.email_or_phone,
                User.phone == credentials.email_or_phone,
            ),
            User.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise AuthenticationError("Invalid email/phone or password")

    if not user.is_active:
        raise AuthenticationError("Account is deactivated")

    if user.is_blocked:
        raise AuthenticationError(f"Account is blocked: {user.blocked_reason or ''}")

    # Create tokens
    access_token = create_access_token(user.id)
    refresh_token, token_hash, expires_at = create_refresh_token(user.id)

    # Create session
    client_info = get_client_info(request)
    session = UserSession(
        user_id=user.id,
        refresh_token_hash=token_hash,
        user_agent=client_info["user_agent"],
        ip_address=client_info["ip_address"],
        device_type=client_info["device_type"],
        expires_at=expires_at,
    )
    db.add(session)

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(user)

    # Set cookies
    set_auth_cookies(response, access_token, refresh_token)

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserProfileResponse.model_validate(user),
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_tokens(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user_session: tuple = Depends(get_refresh_token_session),
):
    """
    Refresh access token using refresh token.
    
    Implements rotating refresh tokens:
    - Old refresh token is revoked
    - New refresh token is issued
    """
    user, old_session = user_session

    # Revoke old session (rotating refresh tokens)
    old_session.revoke()

    # Create new tokens
    access_token = create_access_token(user.id)
    refresh_token, token_hash, expires_at = create_refresh_token(user.id)

    # Create new session
    client_info = get_client_info(request)
    new_session = UserSession(
        user_id=user.id,
        refresh_token_hash=token_hash,
        user_agent=client_info["user_agent"],
        ip_address=client_info["ip_address"],
        device_type=client_info["device_type"],
        expires_at=expires_at,
    )
    db.add(new_session)

    await db.commit()

    # Set new cookies
    set_auth_cookies(response, access_token, refresh_token)

    return RefreshTokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", response_model=MessageOut)
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    user_session: tuple = Depends(get_refresh_token_session),
):
    """
    Logout current session.
    
    - Revokes current session
    - Clears cookies
    """
    user, session = user_session

    session.revoke()
    await db.commit()

    clear_auth_cookies(response)

    return MessageOut(message="Logged out successfully")


@router.post("/logout-all", response_model=MessageOut)
async def logout_all(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Logout all sessions for current user.
    """
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

    clear_auth_cookies(response)

    return MessageOut(message=f"Logged out from {len(sessions)} sessions")


@router.post("/verify-email", response_model=MessageOut)
async def verify_email(
    data: EmailVerify,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify email address using token.
    """
    email = verify_email_token(data.token)
    if not email:
        raise ValidationError("Invalid or expired verification token")

    result = await db.execute(
        select(User).where(User.email == email, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User not found")

    if user.email_verified:
        return MessageOut(message="Email already verified")

    user.email_verified = True

    # Mark verification as used
    result = await db.execute(
        select(EmailVerification).where(
            EmailVerification.user_id == user.id,
            EmailVerification.token == data.token,
        )
    )
    verification = result.scalar_one_or_none()
    if verification:
        verification.used = True

    await db.commit()

    return MessageOut(message="Email verified successfully")


@router.post("/resend-verification", response_model=MessageOut)
async def resend_verification(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Resend email verification.
    """
    if current_user.email_verified:
        return MessageOut(message="Email already verified")

    # Create new verification token
    verification_token = create_verification_token(current_user.email)
    email_verification = EmailVerification(
        user_id=current_user.id,
        token=verification_token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(email_verification)
    await db.commit()

    # TODO: Send verification email asynchronously
    # await send_verification_email(current_user.email, verification_token)

    return MessageOut(message="Verification email sent")


@router.post("/password-reset", response_model=MessageOut)
async def request_password_reset(
    data: PasswordResetSchema,
    db: AsyncSession = Depends(get_db),
):
    """
    Request password reset email.
    """
    result = await db.execute(
        select(User).where(User.email == data.email, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    # Always return success to prevent email enumeration
    if not user:
        return MessageOut(message="If the email exists, a reset link has been sent")

    # Create reset token
    reset_token = create_password_reset_token(user.email)
    password_reset = PasswordReset(
        user_id=user.id,
        token=reset_token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(password_reset)
    await db.commit()

    # TODO: Send password reset email asynchronously
    # await send_password_reset_email(user.email, reset_token)

    return MessageOut(message="If the email exists, a reset link has been sent")


@router.post("/password-reset/confirm", response_model=MessageOut)
async def confirm_password_reset(
    data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    """
    Confirm password reset with token.
    """
    email = verify_password_reset_token(data.token)
    if not email:
        raise ValidationError("Invalid or expired reset token")

    result = await db.execute(
        select(User).where(User.email == email, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User not found")

    # Update password
    user.password_hash = hash_password(data.new_password)

    # Mark reset token as used
    result = await db.execute(
        select(PasswordReset).where(
            PasswordReset.user_id == user.id,
            PasswordReset.token == data.token,
        )
    )
    reset = result.scalar_one_or_none()
    if reset:
        reset.used = True

    # Revoke all sessions for security
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == user.id,
            UserSession.revoked == False,
        )
    )
    sessions = result.scalars().all()
    for session in sessions:
        session.revoke()

    await db.commit()

    return MessageOut(message="Password reset successfully")

