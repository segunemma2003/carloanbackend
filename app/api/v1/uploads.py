"""
File upload endpoints for admin panel.
Handles image uploads for brands, categories, banners, etc.
"""

import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import require_admin
from app.models.user import User

router = APIRouter()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("app/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    folder: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Upload an image file.
    Returns the URL to access the uploaded image.
    
    Args:
        file: Image file to upload
        folder: Optional folder name (e.g., 'brands', 'categories', 'banners')
        current_user: Current admin user
    
    Returns:
        JSON with image URL
    """
    # Validate file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )
    
    # Read file content
    content = await file.read()
    
    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix.lower() or ".jpg"
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    # Create folder path
    if folder:
        folder_path = UPLOAD_DIR / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        file_path = folder_path / unique_filename
        url_path = f"/static/uploads/{folder}/{unique_filename}"
    else:
        file_path = UPLOAD_DIR / unique_filename
        url_path = f"/static/uploads/{unique_filename}"
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Return URL
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "url": url_path,
            "filename": unique_filename,
            "original_filename": file.filename,
            "size": len(content),
            "content_type": file.content_type,
        }
    )

