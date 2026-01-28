"""
API dependencies for authentication, database sessions, etc.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status, Cookie, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_token, verify_token_type, generate_token_hash
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    TokenExpiredError,
    InvalidTokenError,
    SessionRevokedError,
)
from app.models.user import User, UserSession, UserRole


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
) -> Optional[User]:
    """
    Get current user from access token (optional).
    Returns None if no valid token is present.
    """
    if not access_token:
        return None

    payload = verify_token_type(access_token, "access")
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    result = await db.execute(
        select(User).where(User.id == int(user_id), User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if user and user.is_active and not user.is_blocked:
        return user
    return None


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
) -> User:
    """
    Get current user from access token (required).
    Raises authentication error if no valid token.
    """
    if not access_token:
        raise AuthenticationError("Access token required")

    payload = verify_token_type(access_token, "access")
    if not payload:
        raise InvalidTokenError("Invalid or expired access token")

    user_id = payload.get("sub")
    if not user_id:
        raise InvalidTokenError("Invalid token payload")

    result = await db.execute(
        select(User).where(User.id == int(user_id), User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError("User not found")

    if not user.is_active:
        raise AuthenticationError("User account is deactivated")

    if user.is_blocked:
        raise AuthenticationError(
            f"User account is blocked: {user.blocked_reason or 'No reason provided'}"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user (verified email)."""
    if not current_user.email_verified:
        raise AuthorizationError("Email verification required")
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current user with verified email."""
    if not current_user.email_verified:
        raise AuthorizationError("Please verify your email address")
    return current_user


class RoleChecker:
    """Dependency for checking user roles."""

    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in self.allowed_roles:
            raise AuthorizationError(
                f"Access denied. Required roles: {[r.value for r in self.allowed_roles]}"
            )
        return current_user


# Pre-defined role checkers
require_admin = RoleChecker([UserRole.ADMIN])
require_moderator = RoleChecker([UserRole.ADMIN, UserRole.MODERATOR])
require_dealer = RoleChecker([UserRole.ADMIN, UserRole.DEALER])


async def get_refresh_token_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
    refresh_token: Optional[str] = Cookie(None),
) -> tuple[User, UserSession]:
    """
    Validate refresh token and return user with session.
    Used for token refresh endpoint.
    """
    if not refresh_token:
        raise AuthenticationError("Refresh token required")

    payload = verify_token_type(refresh_token, "refresh")
    if not payload:
        raise TokenExpiredError("Refresh token expired or invalid")

    user_id = payload.get("sub")
    if not user_id:
        raise InvalidTokenError("Invalid token payload")

    # Get user
    result = await db.execute(
        select(User).where(User.id == int(user_id), User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError("User not found")

    if not user.is_active:
        raise AuthenticationError("User account is deactivated")

    if user.is_blocked:
        raise AuthenticationError("User account is blocked")

    # Verify session exists and is valid
    token_hash = generate_token_hash(refresh_token)
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == user.id,
            UserSession.refresh_token_hash == token_hash,
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise InvalidTokenError("Session not found")

    if not session.is_valid:
        if session.revoked:
            raise SessionRevokedError("Session has been revoked")
        raise TokenExpiredError("Session has expired")

    return user, session


def get_client_info(request: Request) -> dict:
    """Extract client information from request."""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "device_type": _detect_device_type(request.headers.get("user-agent", "")),
    }


def _detect_device_type(user_agent: str) -> str:
    """Detect device type from user agent."""
    user_agent_lower = user_agent.lower()
    if "mobile" in user_agent_lower or "android" in user_agent_lower:
        return "mobile"
    elif "tablet" in user_agent_lower or "ipad" in user_agent_lower:
        return "tablet"
    return "desktop"

