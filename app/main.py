"""
AVTO LAIF Backend - Main Application Entry Point
FastAPI application with WebSocket support for real-time chat.
"""

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.database import init_db, close_db, get_db
from app.core.redis import RedisClient
from app.core.exceptions import AppException
from app.api.v1 import api_router
from app.services.websocket import manager, authenticate_websocket, handle_websocket_message
from app.admin import create_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Manages startup and shutdown events.
    """
    # Startup
    print("Starting AVTO LAIF Backend...")
    
    # Initialize database
    await init_db()
    print("Database initialized")
    
    # Initialize Redis
    try:
        await RedisClient.get_client()
        print("Redis connected")
    except Exception as e:
        print(f"Redis connection failed (optional): {e}")
    
    yield
    
    # Shutdown
    print("Shutting down AVTO LAIF Backend...")
    await close_db()
    await RedisClient.close()
    print("Cleanup complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="AVTO LAIF - Car Marketplace API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS middleware (add first so it executes last)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware (required for admin authentication)
# Important: Add AFTER CORS so sessions work properly
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="avto_laif_session",
    max_age=14 * 24 * 60 * 60,  # 14 days
    same_site="lax",
    https_only=False,  # Set to True in production with HTTPS
)

# Admin customization middleware (inject CSS/JS into admin pages)
from app.middleware.admin_custom import AdminCustomMiddleware
app.add_middleware(AdminCustomMiddleware)

# Mount static files FIRST (before admin panel)
# Use absolute path to ensure static files are found
from pathlib import Path
import os

# Get the project root directory (where this file is located)
# Use resolve() to get absolute path
BASE_DIR = Path(__file__).resolve().parent.parent  # Go up from app/ to project root
STATIC_DIR = BASE_DIR / "app" / "static"

# Create static directory if it doesn't exist
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files with absolute path
app.mount("/static", StaticFiles(directory=str(STATIC_DIR.absolute())), name="static")

# Create uploads directory
upload_dir = STATIC_DIR / "uploads"
upload_dir.mkdir(parents=True, exist_ok=True)

# Initialize Admin Panel (after static files are mounted)
admin = create_admin(app)



# Exception handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": str(exc),
                "details": {"type": type(exc).__name__},
            },
        )
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": {},
        },
    )


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "app": settings.APP_NAME,
    }


# Test logo endpoint
@app.get("/test-logo")
async def test_logo():
    """Test if logo is accessible."""
    from fastapi.responses import FileResponse
    from pathlib import Path
    logo_path = Path("app/static/logo.png")
    if logo_path.exists():
        return FileResponse(logo_path)
    return {"error": "Logo not found"}


# Admin Dashboard endpoint
@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Serve the admin dashboard page."""
    dashboard_path = STATIC_DIR.parent / "templates" / "admin" / "dashboard.html"
    
    if dashboard_path.exists():
        with open(dashboard_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(
            content="<h1>Dashboard not found</h1>",
            status_code=404
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else "Disabled in production",
        "api": settings.API_V1_PREFIX,
    }


# WebSocket endpoint for chat
@app.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for real-time chat.
    
    Authentication:
    - Pass access token as query param: /ws/chat?token=<access_token>
    - Or use cookies (access_token cookie)
    
    Message Types (client -> server):
    - ping: Heartbeat
    - subscribe: Subscribe to a dialog { dialog_id }
    - unsubscribe: Unsubscribe from a dialog { dialog_id }
    - typing: Typing indicator { dialog_id, is_typing }
    - message: Send message { dialog_id, text }
    - mark_read: Mark messages as read { dialog_id, message_ids }
    
    Message Types (server -> client):
    - pong: Heartbeat response
    - subscribed: Subscription confirmed { dialog_id }
    - new_message: New message received { dialog_id, message }
    - message_sent: Message sent confirmation { message_id, dialog_id, created_at }
    - message_read: Message read notification { dialog_id, message_id, reader_id, read_at }
    - typing: Typing indicator { dialog_id, user_id, is_typing }
    - online_status: User online status { user_id, is_online }
    - error: Error message { message }
    """
    # Authenticate
    user = await authenticate_websocket(websocket, db)
    if not user:
        await websocket.close(code=4001, reason="Authentication required")
        return

    # Connect
    connection = await manager.connect(websocket, user.id, user.name)

    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "user_id": user.id,
            "user_name": user.name,
        })

        # Listen for messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                await handle_websocket_message(connection, message, db)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                })

    except WebSocketDisconnect:
        await manager.disconnect(connection)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await manager.disconnect(connection)


# WebSocket endpoint for online status
@app.websocket("/ws/status")
async def websocket_status(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for online status tracking.
    Simpler than chat - just maintains presence.
    """
    user = await authenticate_websocket(websocket, db)
    if not user:
        await websocket.close(code=4001, reason="Authentication required")
        return

    connection = await manager.connect(websocket, user.id, user.name)

    try:
        while True:
            # Just keep connection alive with pings
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await manager.disconnect(connection)
    except Exception:
        await manager.disconnect(connection)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
    )

