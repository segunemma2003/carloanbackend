"""
Schemas for notifications and billing.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
import json

from pydantic import BaseModel, Field

from app.models.notification import NotificationType, NotificationChannel
from app.models.billing import PaymentStatus, PaymentProvider, FeatureType
from app.schemas.common import BaseSchema


# ============ Notification Schemas ============

class NotificationResponse(BaseSchema):
    """Notification response."""
    
    id: int
    user_id: int
    type: NotificationType
    title: str
    body: str
    data: Optional[str] = None
    related_user_id: Optional[int] = None
    related_ad_id: Optional[int] = None
    related_dialog_id: Optional[int] = None
    is_read: bool
    read_at: Optional[datetime] = None
    sent_via_in_app: bool
    sent_via_email: bool
    sent_via_sms: bool
    sent_via_push: bool
    email_status: Optional[str] = None
    sms_status: Optional[str] = None
    push_status: Optional[str] = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    """List of notifications with metadata."""
    
    notifications: List[NotificationResponse]
    total: int
    unread_count: int


class NotificationPreferenceResponse(BaseSchema):
    """User notification preferences."""
    
    id: int
    user_id: int
    
    # Notification types
    notify_new_message: bool
    notify_new_response: bool
    notify_ad_approved: bool
    notify_ad_rejected: bool
    notify_subscription_ending: bool
    notify_price_alert: bool
    notify_favorite_posted: bool
    notify_system_alerts: bool
    
    # Delivery channels
    email_enabled: bool
    sms_enabled: bool
    push_enabled: bool
    
    # Do not disturb
    quiet_hours_enabled: bool
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class NotificationPreferenceUpdate(BaseModel):
    """Update notification preferences."""
    
    # Notification types (optional)
    notify_new_message: Optional[bool] = None
    notify_new_response: Optional[bool] = None
    notify_ad_approved: Optional[bool] = None
    notify_ad_rejected: Optional[bool] = None
    notify_subscription_ending: Optional[bool] = None
    notify_price_alert: Optional[bool] = None
    notify_favorite_posted: Optional[bool] = None
    notify_system_alerts: Optional[bool] = None
    
    # Delivery channels (optional)
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    
    # Do not disturb (optional)
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class NotificationMarkRead(BaseModel):
    """Mark notification as read."""
    
    is_read: bool = True


# ============ Billing Schemas ============

class TariffResponse(BaseSchema):
    """Tariff response."""
    
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    feature_type: FeatureType
    price: Decimal
    currency: str
    duration_days: int
    max_ads: Optional[int] = None
    max_boosts_per_ad: Optional[int] = None
    sort_order: int
    is_active: bool
    is_featured: bool


class AdBoostResponse(BaseSchema):
    """Ad boost response."""
    
    id: int
    ad_id: int
    tariff_id: int
    amount: Decimal
    currency: str
    activated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    refund_reason: Optional[str] = None
    is_active: bool
    created_at: datetime


class PaymentResponse(BaseSchema):
    """Payment response."""
    
    id: int
    user_id: int
    amount: Decimal
    currency: str
    provider: PaymentProvider
    provider_transaction_id: str
    provider_payment_url: Optional[str] = None
    status: PaymentStatus
    description: Optional[str] = None
    related_ad_id: Optional[int] = None
    related_tariff_id: Optional[int] = None
    completed_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    refund_reason: Optional[str] = None
    created_at: datetime


class PaymentCreateRequest(BaseModel):
    """Request to create payment."""
    
    ad_id: int
    tariff_id: int
    provider: PaymentProvider = PaymentProvider.STRIPE


class PaymentConfirmRequest(BaseModel):
    """Request to confirm payment."""
    
    provider_transaction_id: Optional[str] = None


class InvoiceResponse(BaseSchema):
    """Invoice response."""
    
    id: int
    payment_id: int
    invoice_number: str
    amount: Decimal
    currency: str
    vat_percentage: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None
    issued_at: datetime
    due_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    is_paid: bool


# ============ Webhook Schemas ============

class StripeWebhookRequest(BaseModel):
    """Stripe webhook request."""
    
    id: str
    type: str
    data: dict


class YandexWebhookRequest(BaseModel):
    """Yandex.Kassa webhook request."""
    
    type: str
    event: dict


class SberbankWebhookRequest(BaseModel):
    """Sberbank webhook request."""
    
    orderNumber: str
    operation: str
    status: int
    amount: int


# ============ Billing Statistics ============

class BillingStatsResponse(BaseModel):
    """Billing statistics response."""
    
    total_revenue: Decimal
    currency: str
    total_payments: int
    completed_payments: int
    failed_payments: int
    total_refunds: int
    payment_methods: dict  # {provider: count}
    top_tariffs: List[dict]  # [{name, count, revenue}]
    daily_revenue: List[dict]  # [{date, amount}]