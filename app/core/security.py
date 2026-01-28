"""
Security utilities for password hashing and JWT token management.
Implements rotating refresh tokens with session tracking.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Any

import jwt
import bcrypt

from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def hash_password(password: str) -> str:
    """Hash a password for storage."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def generate_token_hash(token: str) -> str:
    """Generate a hash of a token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_random_token(length: int = 64) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def create_access_token(
    subject: str | int,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict] = None,
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: The subject (usually user_id) to encode in the token
        expires_delta: Custom expiration time
        additional_claims: Additional claims to include in the token
    
    Returns:
        Encoded JWT token string
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }

    if additional_claims:
        to_encode.update(additional_claims)

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(
    subject: str | int,
    expires_delta: Optional[timedelta] = None,
) -> Tuple[str, str, datetime]:
    """
    Create a JWT refresh token.
    
    Returns:
        Tuple of (token, token_hash, expiration_datetime)
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    # Generate a unique token ID for this refresh token
    token_id = generate_random_token(32)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
        "jti": token_id,  # JWT ID for tracking
    }

    token = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    token_hash = generate_token_hash(token)

    return token, token_hash, expire


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.
    
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_token_type(token: str, expected_type: str) -> Optional[dict]:
    """
    Verify a token and check its type.
    
    Args:
        token: The JWT token to verify
        expected_type: Expected token type ('access' or 'refresh')
    
    Returns:
        Decoded payload if valid and correct type, None otherwise
    """
    payload = decode_token(token)
    if payload and payload.get("type") == expected_type:
        return payload
    return None


def create_verification_token(email: str, expires_hours: int = 24) -> str:
    """Create a token for email verification."""
    expire = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    to_encode = {
        "sub": email,
        "exp": expire,
        "type": "email_verification",
    }
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_password_reset_token(email: str, expires_hours: int = 1) -> str:
    """Create a token for password reset."""
    expire = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    to_encode = {
        "sub": email,
        "exp": expire,
        "type": "password_reset",
    }
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def verify_email_token(token: str) -> Optional[str]:
    """Verify email verification token and return email."""
    payload = verify_token_type(token, "email_verification")
    if payload:
        return payload.get("sub")
    return None


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify password reset token and return email."""
    payload = verify_token_type(token, "password_reset")
    if payload:
        return payload.get("sub")
    return None


def generate_sms_code(length: int = 6) -> str:
    """Generate a numeric SMS verification code."""
    return "".join([str(secrets.randbelow(10)) for _ in range(length)])

