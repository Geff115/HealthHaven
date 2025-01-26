#!/usr/bin/env python3
"""
Doctor-specifc route
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from datetime import date, time, datetime, timedelta
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, validator
from ..auth.dependencies import get_current_active_user
from ..models.appointment import Appointment, AppointmentStatus
from ..models.user import User, UserRole
from ..models.doctor import Doctor, DoctorStatus
from ..db.session import get_db_session

router = APIRouter(prefix="/doctors", tags=["doctors"])

logger = logging.getLogger(__name__)

class DoctorCreate(BaseModel):
    phone_number: str
    specialization: str
    license_number: str

    @validator('phone_number')
    def validate_phone(cls, v):
        if not v.isdigit():
            raise ValueError("Phone number must contain only digits")
        if len(v) < 10 or len(v) > 11:
            raise ValueError("Phone number must be between 10 and 11 digits long")
        return v

    @validator('license_number')
    def validate_license(cls, v):
        if not v.isalnum():
            raise ValueError("License number must be alphanumeric")
        if len(v) < 6 or len(v) > 20:
            raise ValueError("License number must be between 6 and 20 characters long")
        return v


class DoctorResponse(BaseModel):
    id: int
    user_id: int
    phone_number: str
    specialization: str
    license_number: str
    status: DoctorStatus
    created_at: datetime

@router.post("/register", response_model=DoctorResponse)
async def register_doctor(
    doctor_data: DoctorCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Register an existing user as a doctor"""
    try:
        with get_db_session() as session:
            # Check if user already has a doctor registration
            existing_doctor = session.query(Doctor).filter(
                Doctor.user_id == current_user.id
            ).first()

            if existing_doctor:
                logger.warning(f"User {current_user.username} attempted duplicate doctor registration")
                raise HTTPException(
                    status_code=400,
                    detail="Doctor registration already exists"
                )

            # Create doctor entry
            doctor = Doctor(
                user_id=current_user.id,
                phone_number=doctor_data.phone_number,
                specialization=doctor_data.specialization,
                license_number=doctor_data.license_number,
                status=DoctorStatus.PENDING
            )

            # Get the user from the current session
            user = session.query(User).filter(User.id == current_user.id).first()
            # Update user role to DOCTOR_PENDING
            user.role = UserRole.DOCTOR_PENDING

            session.add(doctor)
            session.add(user)  # Adding the updated user to the session
            session.commit()
            session.refresh(doctor)

            logger.info(f"New doctor registration | User: {current_user.username}")
            return doctor
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Failed to register doctor: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to register doctor"
        )

@router.get("/me", response_model=DoctorResponse)
async def get_doctor_profile(current_user: User = Depends(get_current_active_user)):
    """Get current doctor's profile"""
    try:
        with get_db_session() as session:
            doctor = session.query(Doctor).filter(
                Doctor.user_id == current_user.id
            ).first()
            
            if not doctor:
                raise HTTPException(
                    status_code=404,
                    detail="Doctor profile not found"
                )
            
            return doctor
    except Exception as e:
        security_logger.error(f"Error fetching doctor profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch doctor profile"
        )

@router.get("/specializations")
async def get_specializations():
    """Get list of available specializations"""
    specializations = [
        "General Practice",
        "Cardiology",
        "Pediatrics",
        "Orthopedics",
        "Dermatology",
        "Gynecology",
        "Neurology",
        "Oncology",
        "Psychology",
        "Opthalmology",
        "Dentistry",
        "Sexology"
    ]
    return {"specializations": specializations}