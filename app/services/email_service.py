"""Safe, no-op-capable email service used by the app.

This service will not raise if SMTP is not configured. It lazy-imports
optional dependencies so the app can run without installing them.
"""
from typing import Optional
import asyncio

from app.core.config import settings


class EmailService:
    """Safe email service: no-op when SMTP not configured; lazy imports.

    Methods are async so they can be scheduled with `asyncio.create_task`.
    """

    def __init__(self) -> None:
        self.host = getattr(settings, "SMTP_HOST", None)
        self.port = getattr(settings, "SMTP_PORT", None)
        self.user = getattr(settings, "SMTP_USER", None)
        self.password = getattr(settings, "SMTP_PASSWORD", None)
        self.from_email = getattr(settings, "EMAIL_FROM", "noreply@example.com")
        self.enabled = bool(self.host and self.user and self.password)

    async def _send_via_smtp(self, to_email: str, subject: str, html_body: str) -> bool:
        try:
            # Lazy import to avoid introducing a hard dependency in dev
            import aiosmtplib
            from email.message import EmailMessage

            msg = EmailMessage()
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.set_content(html_body, subtype="html")

            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                start_tls=True,
            )
            return True
        except Exception as exc:  # pragma: no cover - defensive logging
            # Do not surface SMTP errors to callers; log and continue.
            print(f"[email_service] SMTP send failed: {exc}")
            return False

    async def send_verification_email(self, to_email: str, user_name: Optional[str], token: str) -> bool:
        subject = "AVTO LAIF — Подтвердите email"
        verify_url = f"{getattr(settings, 'FRONTEND_URL', '')}/verify-email?token={token}"
        html = f"<p>Здравствуйте, {user_name or to_email}.</p><p>Чтобы подтвердить email, перейдите по ссылке: <a href='{verify_url}'>подтвердить</a></p>"
        if not self.enabled:
            print(f"[email_service] SMTP not configured — skipping verification email to {to_email}")
            return True
        return await self._send_via_smtp(to_email, subject, html)

    async def send_password_reset_email(self, to_email: str, user_name: Optional[str], token: str) -> bool:
        subject = "AVTO LAIF — Сброс пароля"
        reset_url = f"{getattr(settings, 'FRONTEND_URL', '')}/reset-password?token={token}"
        html = f"<p>Здравствуйте, {user_name or to_email}.</p><p>Сбросить пароль: <a href='{reset_url}'>ссылка</a></p>"
        if not self.enabled:
            print(f"[email_service] SMTP not configured — skipping password reset email to {to_email}")
            return True
        return await self._send_via_smtp(to_email, subject, html)

    async def send_welcome_email(self, to_email: str, user_name: Optional[str]) -> bool:
        subject = "Добро пожаловать в AVTO LAIF"
        html = f"<p>Здравствуйте, {user_name or to_email}.</p><p>Спасибо за регистрацию на AVTO LAIF.</p>"
        if not self.enabled:
            print(f"[email_service] SMTP not configured — skipping welcome email to {to_email}")
            return True
        return await self._send_via_smtp(to_email, subject, html)


# Singleton instance for import
email_service = EmailService()
