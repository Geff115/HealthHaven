#!/usr/bin/env python3
"""
User routes
"""
import os
import uuid
import shutil
from PIL import Image
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.exc import SQLAlchemyError
from ..auth.dependencies import get_current_active_user
from ..models.user import User
from ..db.session import get_db_session
from ..logging import security_logger
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator

router = APIRouter(prefix="/users", tags=["users"])


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: str
    last_name: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

    @validator('first_name', 'last_name')
    def validate_non_empty(cls, value):
        if not value.strip():
            raise ValueError("This field cannot be empty")
        return value


# Create upload directory if it doesn't exist
UPLOAD_DIR = Path("backend/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@router.get("/me")
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    security_logger.info(f"User profile accessed: {current_user.username}")
    with get_db_session() as session:
        return {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "city": current_user.city,
            "state": current_user.state,
            "country": current_user.country,
            "profile_picture": current_user.profile_picture
        }

@router.put("/me")
async def update_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update current user profile"""
    with get_db_session() as session:
        try:
            result = current_user.update_user(**user_data.dict(exclude_unset=True))
            security_logger.info(f"User profile updated: {current_user.username} - {user_data.dict(exclude_unset=True)}")
            return {"message": "Profile updated successfully", "updated_profile": result}
        except KeyError as e:
            security_logger.warning(f"Invalid field update attempt by user: {current_user.username} - {e}")
            raise HTTPException(status_code=400, detail=f"Invalid field: {e}")
        except SQLAlchemyError:
            security_logger.error(f"Database update failed for user: {current_user.username} - {e}")
            raise HTTPException(status_code=500, detail="Database update failed")

@router.post("/me/profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    """Upload user profile picture"""
    try:
        # Validate file type
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_location = UPLOAD_DIR / unique_filename

        # Save file
        with file_location.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Optimize image
        with Image.open(file_location) as img:
            # Resize if too large
            if img.height > 800 or img.width > 800:
                img.thumbnail((800, 800))
            # Save optimized image
            img.save(file_location, optimize=True, quality=85)

        # Update database
        with get_db_session() as session:
            # Delete old profile picture if exists
            if current_user.profile_picture:
                old_file = Path(current_user.profile_picture)
                if old_file.exists():
                    old_file.unlink()

            # Update user profile with new picture URL
            relative_path = f"/uploads/{unique_filename}"
            current_user.profile_picture = relative_path
            session.add(current_user)
            session.commit()

            security_logger.info(f"Profile picture updated for user: {current_user.username}")
            return {"message": "Profile picture updated successfully", "file_path": relative_path}

    except Exception as e:
        security_logger.error(f"Profile picture upload failed for user {current_user.username}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload profile picture")