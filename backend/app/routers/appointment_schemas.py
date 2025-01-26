#!/usr/bin/env python3
from pydantic import BaseModel, Field, validator
from datetime import date, time, datetime
from typing import List, Optional

class DoctorInfo(BaseModel):
    id: int
    first_name: str
    last_name: str
    specialization: str

    class Config:
        form_attributes = True  # Updated from orm_mode = True

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
    doctor: DoctorInfo

    class Config:
        form_attributes = True
        
    @validator('status')
    def validate_status(cls, v):
        if isinstance(v, str):
            return v
        return v.value  # Convert enum to string if it's an enum

class AppointmentUpdate(BaseModel):
    status: str = Field(..., description="New status for the appointment")

    @validator('status')
    def validate_status(cls, v):
        if v not in ["SCHEDULED", "COMPLETED", "CANCELLED"]:
            raise ValueError(f"Invalid status. Must be one of: SCHEDULED, COMPLETED, CANCELLED")
        return v

class AppointmentList(BaseModel):
    items: List[AppointmentResponse]
    total: int
    page: int
    size: int

    class Config:
        form_attributes = True