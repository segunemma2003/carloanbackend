"""Safe SMS service for verification codes.

This module stores verification codes in-memory by default so the app can
run without Twilio credentials. If Twilio credentials exist, it will attempt
to send messages but won't raise on failure.
"""
from datetime import datetime, timedelta
import random
from typing import Dict, Tuple

from app.core.config import settings
from app.core.redis import RedisClient


# In-memory store: phone -> (code, expires_at)
_SMS_STORE: Dict[str, Tuple[str, datetime]] = {}


class SmsService:
    """SMS service that is safe to use without external provider."""

    def __init__(self) -> None:
        self.enabled = bool(
            getattr(settings, "TWILIO_ACCOUNT_SID", None)
            and getattr(settings, "TWILIO_AUTH_TOKEN", None)
            and getattr(settings, "TWILIO_PHONE_NUMBER", None)
        )

    async def send_verification_code(self, phone: str, length: int = 6, ttl_seconds: int = 300) -> str:
        code = "".join(str(random.randint(0, 9)) for _ in range(length))
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        # Try to persist in Redis if available for cross-process safety
        try:
            client = await RedisClient.get_client()
            await client.setex(f"sms:{phone}", ttl_seconds, code)
        except Exception:
            _SMS_STORE[phone] = (code, expires_at)

        if not self.enabled:
            print(f"[sms_service] Twilio not configured — generated code for {phone}: {code}")
            return code

        try:
            # Lazy import Twilio to avoid hard dependency
            from twilio.rest import Client

            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(body=f"Your verification code: {code}", from_=settings.TWILIO_PHONE_NUMBER, to=phone)
            return code
        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"[sms_service] Twilio send failed: {exc} — code stored locally for {phone}")
            return code

    async def verify_code(self, phone: str, code: str) -> bool:
        # Try Redis first
        try:
            client = await RedisClient.get_client()
            stored = await client.get(f"sms:{phone}")
            if not stored:
                return False
            if stored == code:
                await client.delete(f"sms:{phone}")
                return True
            return False
        except Exception:
            entry = _SMS_STORE.get(phone)
            if not entry:
                return False
            stored_code, expires_at = entry
            if datetime.utcnow() > expires_at:
                del _SMS_STORE[phone]
                return False
            if stored_code == code:
                del _SMS_STORE[phone]
                return True
            return False


sms_service = SmsService()
