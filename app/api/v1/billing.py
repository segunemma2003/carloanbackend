"""
Billing and tariff API endpoints.
Handles tariffs, payments, and boosts.
"""

from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError, ConflictError
from app.models.billing import (
    Tariff,
    AdBoost,
    Payment,
    PaymentStatus,
    PaymentProvider,
    FeatureType,
)
from app.models.ad import Ad, AdStatus
from app.models.user import User
from app.schemas.billing import (
    TariffResponse,
    PaymentResponse,
    AdBoostResponse,
    PaymentCreateRequest,
    PaymentConfirmRequest,
)
from app.schemas.common import PaginatedResponse, MessageOut
from app.api.deps import get_current_user, require_admin
from app.services.payment_service import payment_service


router = APIRouter()


# ============ Tariffs ============

@router.get("/tariffs", response_model=list[TariffResponse])
async def list_tariffs(
    feature_type: Optional[FeatureType] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get available tariffs.
    
    Args:
        feature_type: Filter by feature type (featured, top, urgent)
    """
    tariffs = await payment_service.get_active_tariffs(db, feature_type)
    return [TariffResponse.model_validate(t) for t in tariffs]


@router.get("/tariffs/{tariff_id}", response_model=TariffResponse)
async def get_tariff(
    tariff_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get tariff details."""
    tariff = await payment_service.get_tariff(db, tariff_id)
    
    if not tariff:
        raise NotFoundError("Tariff not found", "tariff", tariff_id)
    
    return TariffResponse.model_validate(tariff)


@router.post("/tariffs", response_model=TariffResponse, status_code=status.HTTP_201_CREATED)
async def create_tariff(
    tariff_data: dict,  # Use specific schema in production
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Create new tariff (admin only).
    """
    # Check slug uniqueness
    result = await db.execute(
        select(Tariff).where(Tariff.slug == tariff_data["slug"])
    )
    if result.scalar_one_or_none():
        raise ConflictError("Tariff with this slug already exists")
    
    tariff = Tariff(**tariff_data)
    db.add(tariff)
    await db.commit()
    await db.refresh(tariff)
    
    return TariffResponse.model_validate(tariff)


# ============ Payments ============

@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    request: PaymentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create payment for ad boost.
    
    Returns payment object with payment URL for redirect.
    """
    # Check ad exists and user owns it
    result = await db.execute(
        select(Ad).where(
            Ad.id == request.ad_id,
            Ad.user_id == current_user.id,
            Ad.deleted_at.is_(None),
        )
    )
    ad = result.scalar_one_or_none()
    
    if not ad:
        raise NotFoundError("Ad not found", "ad", request.ad_id)
    
    # Create payment
    payment = await payment_service.create_payment(
        db=db,
        user_id=current_user.id,
        tariff_id=request.tariff_id,
        ad_id=request.ad_id,
        provider=request.provider,
    )
    
    # Get payment URL from provider
    try:
        payment_url = await payment_service.create_payment_url(db, payment)
        payment.provider_payment_url = payment_url
        await db.commit()
    except NotImplementedError:
        # Provider not yet implemented, return test URL
        payment.provider_payment_url = (
            f"{settings.FRONTEND_URL}/payment/simulate?"
            f"payment_id={payment.id}"
        )
        await db.commit()
    
    return PaymentResponse.model_validate(payment)


@router.get("/payments", response_model=PaginatedResponse[PaymentResponse])
async def list_user_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current user's payment history.
    """
    query = select(Payment).where(
        Payment.user_id == current_user.id
    ).order_by(Payment.created_at.desc())
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Paginate
    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    payments = result.scalars().all()
    
    items = [PaymentResponse.model_validate(p) for p in payments]
    
    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get payment details."""
    result = await db.execute(
        select(Payment).where(
            Payment.id == payment_id,
            Payment.user_id == current_user.id,
        )
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise NotFoundError("Payment not found", "payment", payment_id)
    
    return PaymentResponse.model_validate(payment)


@router.post("/payments/{payment_id}/confirm", response_model=PaymentResponse)
async def confirm_payment(
    payment_id: int,
    request: PaymentConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Confirm payment completion.
    
    This would typically be called via webhook from payment provider.
    For testing, can be called manually with provider_transaction_id.
    """
    result = await db.execute(
        select(Payment).where(
            Payment.id == payment_id,
            Payment.user_id == current_user.id,
        )
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise NotFoundError("Payment not found", "payment", payment_id)
    
    # Update provider transaction ID if provided
    if request.provider_transaction_id:
        payment.provider_transaction_id = request.provider_transaction_id
    
    # Confirm payment
    success = await payment_service.confirm_payment(db, payment_id)
    
    if not success:
        raise ValidationError("Failed to confirm payment")
    
    await db.refresh(payment)
    return PaymentResponse.model_validate(payment)


@router.post("/payments/{payment_id}/refund", response_model=MessageOut)
async def refund_payment(
    payment_id: int,
    reason: str = Query(..., min_length=5),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Refund a payment.
    Can be done by user within 7 days or by admin anytime.
    """
    result = await db.execute(
        select(Payment).where(
            Payment.id == payment_id,
            Payment.user_id == current_user.id,
        )
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise NotFoundError("Payment not found", "payment", payment_id)
    
    if payment.status != PaymentStatus.COMPLETED:
        raise ValidationError("Can only refund completed payments")
    
    # Check age (allow refund within 7 days)
    from datetime import timedelta, datetime, timezone
    age = datetime.now(timezone.utc) - payment.completed_at
    if age > timedelta(days=7):
        raise ValidationError("Refund period has expired (7 days)")
    
    # Process refund
    success = await payment_service.refund_payment(db, payment_id, reason)
    
    if not success:
        raise ValidationError("Failed to refund payment")
    
    return MessageOut(message="Payment refunded successfully")


# ============ Ad Boosts ============

@router.get("/ads/{ad_id}/boosts", response_model=list[AdBoostResponse])
async def get_ad_boosts(
    ad_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get active boosts for an ad.
    Only ad owner can see.
    """
    # Check ad exists and user owns it
    result = await db.execute(
        select(Ad).where(
            Ad.id == ad_id,
            Ad.deleted_at.is_(None),
        )
    )
    ad = result.scalar_one_or_none()
    
    if not ad:
        raise NotFoundError("Ad not found", "ad", ad_id)
    
    if ad.user_id != current_user.id and not current_user.is_admin:
        raise ValidationError("Can only view boosts for your own ads")
    
    boosts = await payment_service.get_active_boosts_for_ad(db, ad_id)
    
    return [AdBoostResponse.model_validate(b) for b in boosts]


# ============ Admin Endpoints ============

@router.get("/admin/payments", response_model=PaginatedResponse[PaymentResponse])
async def list_all_payments(
    status: Optional[PaymentStatus] = None,
    provider: Optional[PaymentProvider] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    List all payments (admin only).
    """
    query = select(Payment)
    
    if status:
        query = query.where(Payment.status == status)
    if provider:
        query = query.where(Payment.provider == provider)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Paginate
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Payment.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    payments = result.scalars().all()
    
    items = [PaymentResponse.model_validate(p) for p in payments]
    
    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/admin/expire-boosts", response_model=MessageOut)
async def expire_old_boosts(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Manually trigger boost expiration check.
    Should be called periodically via scheduler.
    """
    count = await payment_service.expire_old_boosts(db)
    
    return MessageOut(message=f"Expired {count} old boosts")


# ============ Testing Endpoint ============

@router.post("/payments/{payment_id}/confirm-test", response_model=PaymentResponse)
async def confirm_payment_test(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    TEST ENDPOINT: Simulate payment confirmation.
    
    WARNING: Only use in development!
    In production, payments should be confirmed via provider webhooks.
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test endpoint disabled in production",
        )
    
    result = await db.execute(
        select(Payment).where(
            Payment.id == payment_id,
            Payment.user_id == current_user.id,
        )
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise NotFoundError("Payment not found", "payment", payment_id)
    
    # Confirm payment
    success = await payment_service.confirm_payment(db, payment_id)
    
    if not success:
        raise ValidationError("Failed to confirm payment")
    
    await db.refresh(payment)
    return PaymentResponse.model_validate(payment)