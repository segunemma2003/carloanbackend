"""Webhook endpoints for external providers (payments, partners).

This file provides a minimal, safe set of endpoints so the app can
receive webhooks without requiring external provider SDKs.
"""
from typing import Any
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """Simple health endpoint for webhook receiver."""
    return {"ok": True}


@router.post("/payments/{provider}")
async def payment_webhook(provider: str, request: Request) -> Any:
    """
    Generic payment webhook receiver.

    - Logs the incoming payload and returns 200.
    - Implement provider-specific signature verification later.
    """
    payload = await request.body()
    # Keep logging minimal to avoid leaking secrets in logs
    print(f"[webhook] payment received from {provider}: {len(payload)} bytes")

    # TODO: verify signatures for providers (Stripe, Yandex, etc.)

    return JSONResponse(status_code=status.HTTP_200_OK, content={"received": True})


@router.post("/generic")
async def generic_webhook(request: Request) -> Any:
    """Catch-all webhook receiver used for partners and simple callbacks."""
    data = await request.json()
    print(f"[webhook] generic payload keys: {list(data.keys()) if isinstance(data, dict) else 'non-json'}")
    return JSONResponse(status_code=status.HTTP_200_OK, content={"ok": True})
