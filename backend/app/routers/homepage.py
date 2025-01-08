#!/usr/bin/env python3
"""Homepage routes"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from ..models.user import User
from typing import Optional
import logging

router = APIRouter(prefix="/homepage", tags=["homepage"])
logger = logging.getLogger(__name__)


@router.get("/homepage-data", response_class=JSONResponse)
async def get_homepage_data():
    """Rendering data to the homepage"""
    base_data = {
        "services": ["Symptom diagnosis", "Appointment with Medical professionals", "Health information", "ML for medicine research"],
        "locations": ["Africa", "Europe", "America"],
        "specialties": ["Cardiology", "Neurology", "Orthopedics", "Pediatrics", "Dermatology", "Gynecology", "Opthalmology"]
    }

    return base_data