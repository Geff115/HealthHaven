#!/usr/bin/env python3
"""Homepage routes"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from ..auth.dependencies import get_current_active_user
from ..models.user import User
from typing import Optional
import logging

router = APIRouter(prefix="/homepage", tags=["homepage"])
logger = logging.getLogger(__name__)


async def optional_active_user_dependency():
    """Dependency wrapper to make the current active user optional."""
    try:
        return await get_current_active_user()
    except Exception as e:
        logger.warning(f"Authentication failed: {e}")
        return None

@router.get("/homepage-data", response_class=JSONResponse)
async def get_homepage_data(current_user: Optional[User] = Depends(optional_active_user_dependency)):
    """Get homepage data - works for both authenticated and unauthenticated users"""
    base_data = {
        "services": ["Symptom diagnosis", "Appointment with Medical professionals", "Health information", "ML for medicine research"],
        "locations": ["Africa", "Europe", "America"],
        "specialties": ["Cardiology", "Neurology", "Orthopedics", "Pediatrics", "Dermatology", "Gynecology", "Opthalmology"]
    }

    if current_user:
        base_data.update({
            "user_info": {
                "name": f"{current_user.first_name} {current_user.last_name}",
                "location": f"{current_user.city}, {current_user.state}" if current_user.city and current_user.state else "Location not available",
            }
        })

    return base_data