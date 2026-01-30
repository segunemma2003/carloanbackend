"""
Billing and tariff models for paid features.
Handles tariffs, ad boosts, and payments.
"""

import enum
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.ad import Ad


class FeatureType(str, enum.Enum):
    """Types of paid features."""
    FEATURED = "featured"  # Ad appears in featured section
    TOP = "top"            # Ad appears at top of search results
    URGENT = "urgent"      # Ad marked as urgent


class PaymentStatus(str, enum.Enum):
    """Payment status."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentProvider(str, enum.Enum):
    """Payment providers."""
    STRIPE = "stripe"
    YANDEX = "yandex"
    SBERBANK = "sberbank"
    PAYPAL = "paypal"


class Tariff(Base, TimestampMixin):
    """
    Tariff/pricing plan for features.
    
    Examples:
    - Featured for 7 days: 500 RUB
    - Top placement for 30 days: 1000 RUB
    - Bundle: Featured + Top for 30 days: 1500 RUB
    """

    __tablename__ = "tariffs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Feature type
    feature_type: Mapped[FeatureType] = mapped_column(
        Enum(FeatureType),
        nullable=False,
        index=True,
    )
    
    # Pricing
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    
    # Duration
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 7, 30, 90, 365
    
    # Limits (for package/bundle tariffs)
    max_ads: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )  # Max ads for bundle (None = unlimited)
    max_boosts_per_ad: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )  # Max boosts per ad (None = unlimited)
    
    # Management
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )  # Highlight in UI

    # Relationships
    boosts: Mapped[List["AdBoost"]] = relationship("AdBoost", back_populates="tariff")

    def __repr__(self) -> str:
        return f"<Tariff(id={self.id}, name={self.name}, price={self.price})>"

    @property
    def display_price(self) -> str:
        """Format price for display."""
        return f"{self.price} {self.currency}"

    @property
    def price_per_day(self) -> Decimal:
        """Calculate price per day."""
        return self.price / Decimal(self.duration_days)


class AdBoost(Base, TimestampMixin):
    """
    Purchase of a tariff for an ad.
    Represents a boost applied to an ad.
    """

    __tablename__ = "ad_boosts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Related entities
    ad_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tariff_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tariffs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    
    # Payment info
    payment_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Amount
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    
    # Duration
    activated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Refund
    refunded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    refund_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    ad: Mapped["Ad"] = relationship("Ad")
    tariff: Mapped["Tariff"] = relationship("Tariff", back_populates="boosts")
    payment: Mapped[Optional["Payment"]] = relationship("Payment")

    def __repr__(self) -> str:
        return f"<AdBoost(id={self.id}, ad_id={self.ad_id}, tariff_id={self.tariff_id})>"

    def activate(self) -> None:
        """Activate the boost."""
        self.is_active = True
        self.activated_at = datetime.now(timezone.utc)
        
        # Calculate expiration
        from datetime import timedelta
        self.expires_at = self.activated_at + timedelta(
            days=self.tariff.duration_days
        )

    def is_expired(self) -> bool:
        """Check if boost has expired."""
        if not self.is_active or not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def deactivate(self) -> None:
        """Deactivate the boost."""
        self.is_active = False

    def refund(self, reason: str) -> None:
        """Refund the boost."""
        self.refunded_at = datetime.now(timezone.utc)
        self.refund_reason = reason
        self.is_active = False


class Payment(Base, TimestampMixin):
    """
    Payment transaction.
    Tracks all payments for boosts, subscriptions, etc.
    """

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # User making payment
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Payment amount
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    
    # Payment provider
    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(PaymentProvider),
        nullable=False,
        index=True,
    )
    provider_transaction_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    provider_payment_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True,
    )
    
    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Related ad
    related_ad_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    related_tariff_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Completion
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Refund
    refunded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    refund_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Metadata (JSON)
    metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, user_id={self.user_id}, status={self.status})>"

    @property
    def display_amount(self) -> str:
        """Format amount for display."""
        return f"{self.amount} {self.currency}"

    def mark_completed(self) -> None:
        """Mark payment as completed."""
        self.status = PaymentStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)

    def mark_failed(self) -> None:
        """Mark payment as failed."""
        self.status = PaymentStatus.FAILED

    def refund(self, reason: str) -> None:
        """Mark payment as refunded."""
        self.status = PaymentStatus.REFUNDED
        self.refunded_at = datetime.now(timezone.utc)
        self.refund_reason = reason


class Invoice(Base, TimestampMixin):
    """
    Invoice for payments.
    Optional, for accounting/VAT purposes.
    """

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Related payment
    payment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    
    # Invoice number
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    
    # Invoice details
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    
    # VAT (if applicable)
    vat_percentage: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    vat_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    
    # Dates
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    due_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Status
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # File path (if stored)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, invoice_number={self.invoice_number})>"