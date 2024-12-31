#!/usr/bin/env python3
"""
User routes
"""
from fastapi import APIRouter, Depends
from ..auth.dependencies import get_current_active_user
from ..models.user import User
from typing import Optional
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/users", tags=["users"])


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

@router.get("/me")
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "city": current_user.city,
        "state": current_user.state,
        "country": current_user.country
    }

@router.put("/me")
async def update_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update current user profile"""
    try:
        result = current_user.update_user(**user_data.dict(exclude_unset=True))
        return result
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))