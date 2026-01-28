"""
User-related schemas for authentication and profile management.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, field_validator
import phonenumbers

from app.models.user import UserRole, AccountType
from app.schemas.common import BaseSchema, TimestampSchema


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=2, max_length=100)
    account_type: AccountType = AccountType.INDIVIDUAL
    accept_terms: bool = Field(..., description="User must accept terms and conditions")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            parsed = phonenumbers.parse(v, "RU")
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid phone number")
            return phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164,
            )
        except phonenumbers.NumberParseException:
            raise ValueError("Invalid phone number format")

    @field_validator("accept_terms")
    @classmethod
    def must_accept_terms(cls, v: bool) -> bool:
        if not v:
            raise ValueError("You must accept the terms and conditions")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""

    email_or_phone: str = Field(..., description="Email or phone number")
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    city_id: Optional[int] = None
    
    # Company info (for dealers)
    company_name: Optional[str] = None
    company_description: Optional[str] = None
    company_logo_url: Optional[str] = None
    company_address: Optional[str] = None
    company_website: Optional[str] = None
    
    # Notification settings
    notify_email: Optional[bool] = None
    notify_sms: Optional[bool] = None
    notify_push: Optional[bool] = None


class PasswordChange(BaseModel):
    """Schema for password change."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordReset(BaseModel):
    """Schema for password reset request."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for confirming password reset."""

    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class EmailVerify(BaseModel):
    """Schema for email verification."""

    token: str


class PhoneVerify(BaseModel):
    """Schema for phone verification."""

    phone: str
    code: str = Field(..., min_length=4, max_length=8)


class PhoneVerifyRequest(BaseModel):
    """Schema for requesting phone verification."""

    phone: str


class UserResponse(BaseSchema):
    """Schema for user response in public contexts."""

    id: int
    name: str
    avatar_url: Optional[str] = None
    role: UserRole
    account_type: AccountType
    is_active: bool
    email_verified: bool
    phone_verified: bool
    last_seen_at: Optional[datetime] = None
    
    # Company info (for dealers)
    company_name: Optional[str] = None
    company_logo_url: Optional[str] = None

    created_at: datetime


class UserProfileResponse(BaseSchema):
    """Schema for user's own profile (includes private info)."""

    id: int
    email: str
    phone: Optional[str] = None
    name: str
    avatar_url: Optional[str] = None
    role: UserRole
    account_type: AccountType
    is_active: bool
    is_blocked: bool
    email_verified: bool
    phone_verified: bool
    two_factor_enabled: bool
    city_id: Optional[int] = None
    
    # Company info
    company_name: Optional[str] = None
    company_description: Optional[str] = None
    company_logo_url: Optional[str] = None
    company_address: Optional[str] = None
    company_website: Optional[str] = None
    
    # Notification settings
    notify_email: bool
    notify_sms: bool
    notify_push: bool
    
    # Statistics
    last_login_at: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until expiration
    user: UserProfileResponse


class RefreshTokenResponse(BaseModel):
    """Schema for refresh token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class SessionResponse(BaseSchema):
    """Schema for user session info."""

    id: int
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    device_type: Optional[str] = None
    last_used_at: datetime
    created_at: datetime
    is_current: bool = False


class SessionListResponse(BaseModel):
    """Schema for list of user sessions."""

    sessions: List[SessionResponse]
    total: int


class UserPublicProfile(BaseSchema):
    """Public profile for other users to view."""

    id: int
    name: str
    avatar_url: Optional[str] = None
    account_type: AccountType
    is_dealer: bool
    
    # Company info (only for dealers)
    company_name: Optional[str] = None
    company_logo_url: Optional[str] = None
    company_description: Optional[str] = None
    
    # Stats
    ads_count: int = 0
    member_since: datetime
    last_seen_at: Optional[datetime] = None

