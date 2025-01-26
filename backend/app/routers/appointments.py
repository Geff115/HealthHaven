#!/usr/bin/env python3
import logging
import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import date, time, datetime, timedelta
from typing import List, Optional
from ..auth.dependencies import get_current_active_user
from ..models.appointment import Appointment, AppointmentStatus
from ..models.user import User
from ..models.doctor import Doctor, DoctorStatus
from ..db.session import get_db_session
from ..logging import security_logger
from .appointment_schemas import (
    AppointmentCreate, 
    AppointmentResponse, 
    AppointmentUpdate,
    AppointmentList,
    DoctorInfo
)

router = APIRouter(prefix="/api/v1/appointments", tags=["appointments"])

# List doctors endpoint - needs to be before the /{appointment_id} route
# List doctors endpoint
@router.get("/doctors", tags=["doctors"])
async def list_doctors(
    current_user: User = Depends(get_current_active_user)
):
    """List all approved doctors"""
    try:
        with get_db_session() as session:
            doctors = (
                session.query(Doctor)
                .join(Doctor.user)
                .filter(Doctor.status == DoctorStatus.APPROVED)
                .all()
            )
            
            return [
                {
                    "id": doctor.id,
                    "first_name": doctor.user.first_name,
                    "last_name": doctor.user.last_name,
                    "specialization": doctor.specialization
                } for doctor in doctors
            ]
    except Exception as e:
        security_logger.error(f"Failed to fetch doctors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch doctors"
        )

# List appointments endpoint
@router.get("/list")
async def list_appointments(
    current_user: User = Depends(get_current_active_user),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[str] = None
):
    """List user's appointments within a date range"""
    try:
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=30)

        with get_db_session() as session:
            # Base query with joins
            query = (
                session.query(Appointment)
                .join(Appointment.doctor)
                .join(Doctor.user)
                .filter(
                    Appointment.user_id == current_user.id,
                    Appointment.appointment_date >= start_date,
                    Appointment.appointment_date <= end_date
                )
            )
            
            if status:
                query = query.filter(Appointment.status == AppointmentStatus[status.upper()])
            
            # Get total count
            total = query.count()
            
            # Get paginated results
            appointments = query.order_by(
                Appointment.appointment_date.asc(),
                Appointment.appointment_time.asc()
            ).offset(offset).limit(limit).all()

            return {
                "items": [
                    {
                        "id": appt.id,
                        "doctor_id": appt.doctor_id,
                        "user_id": appt.user_id,
                        "appointment_date": appt.appointment_date,
                        "appointment_time": appt.appointment_time,
                        "appointment_note": appt.appointment_note,
                        "status": appt.status.value,
                        "created_at": appt.created_at,
                        "updated_at": appt.updated_at,
                        "doctor": {
                            "id": appt.doctor.id,
                            "first_name": appt.doctor.user.first_name,
                            "last_name": appt.doctor.user.last_name,
                            "specialization": appt.doctor.specialization
                        }
                    } for appt in appointments
                ],
                "total": total,
                "page": (offset // limit) + 1,
                "size": limit
            }
    except Exception as e:
        security_logger.error(f"Failed to fetch appointments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch appointments")

# Create appointment endpoint
@router.post("", response_model=AppointmentResponse)  # No trailing slash
@router.post("/", response_model=AppointmentResponse)
async def create_appointment(
    appointment_data: AppointmentCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new appointment"""
    try:
        # Create appointment - this now returns a dictionary with all needed data
        appointment_data = Appointment.create_appointment(
            doctor_id=appointment_data.doctor_id,
            user_id=current_user.id,
            appointment_date=appointment_data.appointment_date,
            appointment_time=appointment_data.appointment_time,
            appointment_note=appointment_data.appointment_note,
            user_tz=appointment_data.user_timezone
        )
            
        security_logger.info(
            f"Appointment created: User {current_user.id} with Doctor {appointment_data['doctor_id']}"
        )

        return appointment_data
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        security_logger.error(f"Appointment creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create appointment")

# Get single appointment endpoint
@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get appointment details"""
    try:
        with get_db_session() as session:
            # Query appointment with doctor info in a single query
            appointment = (
                session.query(Appointment)
                .join(Appointment.doctor)
                .join(Doctor.user)
                .filter(Appointment.id == appointment_id)
                .first()
            )
            
            if not appointment:
                raise HTTPException(status_code=404, detail="Appointment not found")
            
            if appointment.user_id != current_user.id:
                security_logger.warning(
                    f"Unauthorized appointment access attempt: User {current_user.id} tried to access appointment {appointment_id}"
                )
                raise HTTPException(status_code=403, detail="Not authorized to view this appointment")
            
            # Return data in the same format as create_appointment
            return {
                "id": appointment.id,
                "doctor_id": appointment.doctor_id,
                "user_id": appointment.user_id,
                "appointment_date": appointment.appointment_date,
                "appointment_time": appointment.appointment_time,
                "appointment_note": appointment.appointment_note,
                "status": appointment.status.value,
                "created_at": appointment.created_at,
                "updated_at": appointment.updated_at,
                "doctor": {
                    "id": appointment.doctor.id,
                    "first_name": appointment.doctor.user.first_name,
                    "last_name": appointment.doctor.user.last_name,
                    "specialization": appointment.doctor.specialization
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        security_logger.error(f"Failed to fetch appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch appointment")

# Update appointment endpoint
@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment_status(
    appointment_id: int,
    update_data: AppointmentUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update appointment status"""
    try:
        with get_db_session() as session:
            appointment = session.query(Appointment).filter(
                Appointment.id == appointment_id
            ).first()
            
            if not appointment:
                raise HTTPException(status_code=404, detail="Appointment not found")
            
            if appointment.user_id != current_user.id:
                security_logger.warning(
                    f"Unauthorized appointment update attempt: User {current_user.id} tried to update appointment {appointment_id}"
                )
                raise HTTPException(status_code=403, detail="Not authorized to update this appointment")

            appointment.status = AppointmentStatus[update_data.status.upper()]
            session.commit()
            session.refresh(appointment)
            
            security_logger.info(
                f"Appointment {appointment_id} status updated to {update_data.status} by user {current_user.id}"
            )
            
            return AppointmentResponse.from_orm(appointment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        security_logger.error(f"Failed to update appointment status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update appointment status")

# Delete/Cancel appointment endpoint
@router.delete("/{appointment_id}", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Cancel an appointment"""
    try:
        with get_db_session() as session:
            appointment = session.query(Appointment).filter(
                Appointment.id == appointment_id
            ).first()
            
            if not appointment:
                raise HTTPException(status_code=404, detail="Appointment not found")
                
            if appointment.user_id != current_user.id:
                security_logger.warning(
                    f"Unauthorized appointment cancellation attempt: User {current_user.id} tried to cancel appointment {appointment_id}"
                )
                raise HTTPException(status_code=403, detail="Not authorized to cancel this appointment")
                
            if appointment.status != AppointmentStatus.SCHEDULED:
                raise HTTPException(status_code=400, detail="Can only cancel scheduled appointments")

            appointment.status = AppointmentStatus.CANCELLED
            session.commit()
            session.refresh(appointment)
            
            security_logger.info(f"Appointment {appointment_id} cancelled by user {current_user.id}")
            
            return AppointmentResponse.from_orm(appointment)
    except HTTPException:
        raise
    except Exception as e:
        security_logger.error(f"Failed to cancel appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel appointment")