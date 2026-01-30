"""
Payment and billing service.
Handles payment processing, tariff management, and invoice generation.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, List
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.billing import (
    Tariff,
    AdBoost,
    Payment,
    Invoice,
    PaymentStatus,
    PaymentProvider,
    FeatureType,
)
from app.models.ad import Ad
from app.core.config import settings


class PaymentService:
    """
    Service for payment processing and billing.
    Supports multiple payment providers.
    """

    async def get_active_tariffs(
        self,
        db: AsyncSession,
        feature_type: Optional[FeatureType] = None,
    ) -> List[Tariff]:
        """
        Get active tariffs for purchase.
        
        Args:
            db: Database session
            feature_type: Filter by feature type (optional)
        
        Returns:
            List of active tariffs
        """
        query = select(Tariff).where(Tariff.is_active == True)
        
        if feature_type:
            query = query.where(Tariff.feature_type == feature_type)
        
        query = query.order_by(Tariff.sort_order, Tariff.price)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_tariff(self, db: AsyncSession, tariff_id: int) -> Optional[Tariff]:
        """Get tariff by ID."""
        result = await db.execute(
            select(Tariff).where(Tariff.id == tariff_id)
        )
        return result.scalar_one_or_none()

    async def create_payment(
        self,
        db: AsyncSession,
        user_id: int,
        tariff_id: int,
        ad_id: int,
        provider: PaymentProvider,
    ) -> Payment:
        """
        Create a payment for ad boost.
        
        Args:
            db: Database session
            user_id: User making payment
            tariff_id: Tariff being purchased
            ad_id: Ad to boost
            provider: Payment provider
        
        Returns:
            Created Payment object
        """
        # Get tariff
        tariff = await self.get_tariff(db, tariff_id)
        if not tariff:
            raise ValueError("Tariff not found")
        
        # Create payment
        payment = Payment(
            user_id=user_id,
            amount=tariff.price,
            currency=tariff.currency,
            provider=provider,
            provider_transaction_id="",  # Will be set after provider confirmation
            description=f"Boost ad #{ad_id} with {tariff.name}",
            related_ad_id=ad_id,
            related_tariff_id=tariff_id,
        )
        
        db.add(payment)
        await db.flush()
        
        return payment

    async def create_payment_url(
        self,
        db: AsyncSession,
        payment: Payment,
    ) -> str:
        """
        Create payment URL for external payment provider.
        This is provider-specific implementation.
        
        Args:
            db: Database session
            payment: Payment object
        
        Returns:
            Payment URL to redirect user to
        """
        if payment.provider == PaymentProvider.STRIPE:
            return await self._create_stripe_payment_url(payment)
        elif payment.provider == PaymentProvider.YANDEX:
            return await self._create_yandex_payment_url(payment)
        elif payment.provider == PaymentProvider.SBERBANK:
            return await self._create_sberbank_payment_url(payment)
        else:
            raise ValueError(f"Unsupported payment provider: {payment.provider}")

    async def _create_stripe_payment_url(self, payment: Payment) -> str:
        """Create Stripe payment URL."""
        
        
        raise NotImplementedError("Stripe integration not yet implemented")

    async def _create_yandex_payment_url(self, payment: Payment) -> str:
        """Create Yandex.Kassa payment URL."""
        # This would use Yandex Kassa API
        # https://yandex.ru/dev/kassa/
        
        # Example:
        # from yookassa import Client, Payment as YKPayment
        # Client.agent = ("AVTO_LAIF/1.0")
        # Client.auth_token = settings.YANDEX_KASSA_TOKEN
        # payment_obj = YKPayment.create({
        #     "amount": {
        #         "value": str(payment.amount),
        #         "currency": payment.currency
        #     },
        #     "confirmation": {
        #         "type": "redirect",
        #         "return_url": f"{settings.FRONTEND_URL}/payment/success?payment_id={payment.id}"
        #     },
        #     "capture": True,
        #     "description": payment.description,
        #     "metadata": {"payment_id": payment.id}
        # })
        # payment.provider_transaction_id = payment_obj.id
        # payment.provider_payment_url = payment_obj.confirmation.confirmation_url
        # return payment_obj.confirmation.confirmation_url
        
        raise NotImplementedError("Yandex Kassa integration not yet implemented")

    async def _create_sberbank_payment_url(self, payment: Payment) -> str:
        """Create Sberbank payment URL."""
        # Similar implementation for Sberbank
        raise NotImplementedError("Sberbank integration not yet implemented")

    async def confirm_payment(
        self,
        db: AsyncSession,
        payment_id: int,
    ) -> bool:
        """
        Confirm payment is complete and apply boost.
        
        Args:
            db: Database session
            payment_id: Payment to confirm
        
        Returns:
            True if successful
        """
        result = await db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            return False
        
        # Mark as completed
        payment.mark_completed()
        
        # Create ad boost
        boost = AdBoost(
            ad_id=payment.related_ad_id,
            tariff_id=payment.related_tariff_id,
            payment_id=payment.id,
            amount=payment.amount,
            currency=payment.currency,
        )
        boost.activate()
        
        db.add(boost)
        
        # Update ad with boost flags
        if payment.related_ad_id:
            result = await db.execute(
                select(Ad).where(Ad.id == payment.related_ad_id)
            )
            ad = result.scalar_one_or_none()
            
            if ad and payment.related_tariff_id:
                tariff = await self.get_tariff(db, payment.related_tariff_id)
                if tariff:
                    if tariff.feature_type == FeatureType.FEATURED:
                        ad.is_featured = True
                        ad.featured_until = boost.expires_at
                    elif tariff.feature_type == FeatureType.TOP:
                        ad.is_top = True
                        ad.top_until = boost.expires_at
                    elif tariff.feature_type == FeatureType.URGENT:
                        ad.is_urgent = True
        
        await db.commit()
        return True

    async def refund_payment(
        self,
        db: AsyncSession,
        payment_id: int,
        reason: str,
    ) -> bool:
        """
        Refund a payment.
        
        Args:
            db: Database session
            payment_id: Payment to refund
            reason: Refund reason
        
        Returns:
            True if successful
        """
        result = await db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            return False
        
        # Call provider to refund
        # This would be provider-specific
        
        # Mark as refunded
        payment.refund(reason)
        
        # Deactivate related boost
        result = await db.execute(
            select(AdBoost).where(AdBoost.payment_id == payment_id)
        )
        boost = result.scalar_one_or_none()
        
        if boost:
            boost.refund(reason)
            
            # Remove boost from ad
            if boost.ad_id:
                result = await db.execute(
                    select(Ad).where(Ad.id == boost.ad_id)
                )
                ad = result.scalar_one_or_none()
                
                if ad:
                    tariff = await self.get_tariff(db, boost.tariff_id)
                    if tariff:
                        if tariff.feature_type == FeatureType.FEATURED:
                            ad.is_featured = False
                        elif tariff.feature_type == FeatureType.TOP:
                            ad.is_top = False
                        elif tariff.feature_type == FeatureType.URGENT:
                            ad.is_urgent = False
        
        await db.commit()
        return True

    async def get_user_payment_history(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = 50,
    ) -> List[Payment]:
        """Get user's payment history."""
        result = await db.execute(
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_active_boosts_for_ad(
        self,
        db: AsyncSession,
        ad_id: int,
    ) -> List[AdBoost]:
        """Get active boosts for an ad."""
        result = await db.execute(
            select(AdBoost).where(
                and_(
                    AdBoost.ad_id == ad_id,
                    AdBoost.is_active == True,
                    AdBoost.expires_at > datetime.now(timezone.utc),
                )
            )
        )
        return result.scalars().all()

    async def expire_old_boosts(self, db: AsyncSession) -> int:
        """
        Expire boosts that have passed their expiration date.
        Should be run periodically (e.g., via Celery).
        
        Returns:
            Number of boosts expired
        """
        now = datetime.now(timezone.utc)
        
        result = await db.execute(
            select(AdBoost).where(
                and_(
                    AdBoost.is_active == True,
                    AdBoost.expires_at <= now,
                )
            )
        )
        boosts = result.scalars().all()
        
        count = 0
        for boost in boosts:
            boost.deactivate()
            
            # Remove boost flags from ad
            result = await db.execute(
                select(Ad).where(Ad.id == boost.ad_id)
            )
            ad = result.scalar_one_or_none()
            
            if ad:
                tariff = await self.get_tariff(db, boost.tariff_id)
                if tariff:
                    if tariff.feature_type == FeatureType.FEATURED:
                        ad.is_featured = False
                    elif tariff.feature_type == FeatureType.TOP:
                        ad.is_top = False
                    elif tariff.feature_type == FeatureType.URGENT:
                        ad.is_urgent = False
            
            count += 1
        
        if count > 0:
            await db.commit()
        
        return count

    async def create_invoice(
        self,
        db: AsyncSession,
        payment_id: int,
        invoice_number: str,
    ) -> Optional[Invoice]:
        """
        Create invoice for payment.
        
        Args:
            db: Database session
            payment_id: Payment to invoice
            invoice_number: Invoice number
        
        Returns:
            Created Invoice object
        """
        result = await db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            return None
        
        invoice = Invoice(
            payment_id=payment_id,
            invoice_number=invoice_number,
            amount=payment.amount,
            currency=payment.currency,
            issued_at=datetime.now(timezone.utc),
            is_paid=(payment.status == PaymentStatus.COMPLETED),
            paid_at=payment.completed_at,
        )
        
        db.add(invoice)
        await db.commit()
        
        return invoice


# Global payment service instance
payment_service = PaymentService()