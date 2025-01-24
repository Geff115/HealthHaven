#!/usr/bin/env python3
"""
Appointment routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import date, time, datetime, timedelta
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, validator
from ..auth.dependencies import get_current_active_user
from ..models.appointment import Appointment, AppointmentStatus
from ..models.user import User
from ..models.doctor import Doctor
from ..db.session import get_db_session
from ..logging import security_logger


router = APIRouter(prefix="/api/v1", tags=["appointments"])

class AppointmentCreate(BaseModel):
    doctor_id: int = Field(..., description="ID of the doctor")
    appointment_date: date = Field(..., description="Date of appointment")
    appointment_time: time = Field(..., description="Time of appointment")
    appointment_note: str = Field(..., max_length=255, description="Notes for the appointment")
    user_timezone: str = Field(..., description="User's timezone (e.g., 'America/New_York')")

    @validator('appointment_note')
    def validate_note(cls, v):
        if not v.strip():
            raise ValueError("Appointment note cannot be empty")
        return v.strip()

class AppointmentResponse(BaseModel):
    id: int
    doctor_id: int
    user_id: int
    appointment_date: date
    appointment_time: time
    appointment_note: str
    status: str
    created_at: datetime
    updated_at: datetime

class AppointmentUpdate(BaseModel):
    status: str = Field(..., description="New status for the appointment")

    @validator('status')
    def validate_status(cls, v):
        if v not in AppointmentStatus.__members__:
            raise ValueError(f"Invalid status. Must be one of: {list(AppointmentStatus.__members__.keys())}")
        return v

@router.post("/", response_model=AppointmentResponse)
async def create_appointment(
    appointment_data: AppointmentCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new appointment"""
    try:
        # Verify doctor exists
        with get_db_session() as session:
            doctor = session.query(Doctor).filter(Doctor.id == appointment_data.doctor_id).first()
            if not doctor:
                raise HTTPException(status_code=404, detail="Doctor not found")

        appointment = Appointment.create_appointment(
            doctor_id=appointment_data.doctor_id,
            user_id=current_user.id,
            appointment_date=appointment_data.appointment_date,
            appointment_time=appointment_data.appointment_time,
            appointment_note=appointment_data.appointment_note,
            user_tz=appointment_data.user_timezone
        )
        
        security_logger.info(
            f"Appointment created: User {current_user.id} with Doctor {appointment_data.doctor_id}"
        )
        
        return appointment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        security_logger.error(f"Appointment creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create appointment")


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    user_timezone: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get appointment details"""
    try:
        appointment = Appointment.get_appointment(appointment_id, user_timezone)
        
        # Verify user has access to this appointment
        if appointment["user_id"] != current_user.id:
            security_logger.warning(
                f"Unauthorized appointment access attempt: User {current_user.id} tried to access appointment {appointment_id}"
            )
            raise HTTPException(status_code=403, detail="Not authorized to view this appointment")
            
        return appointment
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/", response_model=List[AppointmentResponse])
async def list_appointments(
    start_date: date = None,
    end_date: date = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user)
):
    """List user's appointments within a date range"""
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = start_date + timedelta(days=30)

    try:
        appointments = Appointment.get_appointment_by_date(
            start_date=start_date,
            end_date=end_date,
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        
        if status:
            appointments = [apt for apt in appointments if apt.status.value == status]
            
        return appointments
    except Exception as e:
        security_logger.error(f"Failed to fetch appointments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch appointments")

@router.put("/{appointment_id}")
async def update_appointment_status(
    appointment_id: int,
    update_data: AppointmentUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update appointment status"""
    try:
        # First fetch the appointment to verify ownership
        with get_db_session() as session:
            appointment = session.query(Appointment).filter(Appointment.id == appointment_id).first()
            if not appointment:
                raise HTTPException(status_code=404, detail="Appointment not found")
            
            if appointment.user_id != current_user.id:
                security_logger.warning(
                    f"Unauthorized appointment update attempt: User {current_user.id} tried to update appointment {appointment_id}"
                )
                raise HTTPException(status_code=403, detail="Not authorized to update this appointment")

        updated_appointment = Appointment.update_status(appointment_id, update_data.status)
        security_logger.info(
            f"Appointment {appointment_id} status updated to {update_data.status} by user {current_user.id}"
        )
        
        return {"message": "Appointment status updated successfully", "appointment": updated_appointment}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        security_logger.error(f"Failed to update appointment status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update appointment status")

@router.delete("/{appointment_id}")
async def cancel_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Cancel an appointment"""
    try:
        # First verify ownership
        with get_db_session() as session:
            appointment = session.query(Appointment).filter(Appointment.id == appointment_id).first()
            if not appointment:
                raise HTTPException(status_code=404, detail="Appointment not found")
                
            if appointment.user_id != current_user.id:
                security_logger.warning(
                    f"Unauthorized appointment cancellation attempt: User {current_user.id} tried to cancel appointment {appointment_id}"
                )
                raise HTTPException(status_code=403, detail="Not authorized to cancel this appointment")
                
            # Only allow cancellation of scheduled appointments
            if appointment.status != AppointmentStatus.SCHEDULED:
                raise HTTPException(status_code=400, detail="Can only cancel scheduled appointments")

        updated_appointment = Appointment.update_status(appointment_id, "CANCELLED")
        security_logger.info(f"Appointment {appointment_id} cancelled by user {current_user.id}")
        
        return {"message": "Appointment cancelled successfully", "appointment": updated_appointment}
    except Exception as e:
        security_logger.error(f"Failed to cancel appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel appointment")