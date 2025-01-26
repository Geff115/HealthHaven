#!/usr/bin/env python3
"""
Appointment model
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from .base import Base
from .doctor import Doctor
from ..db.session import get_db_session
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import Session, relationship
from sqlalchemy import Date, Time, ForeignKey, or_, and_
from .tasks import send_reminder
from pytz import timezone, utc
from sqlalchemy.dialects.postgresql import ENUM
from enum import Enum as PyEnum
from sqlalchemy import UniqueConstraint
from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger(__name__)

class AppointmentStatus(PyEnum):
    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class Appointment(Base):
    __tablename__ = 'appointments'

    __table_args__ = (
        UniqueConstraint(
            'doctor_id',
            'appointment_date',
            'appointment_time',
            name='uq_appointment_time'
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id', ondelete='CASCADE'), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    appointment_date = Column(Date, index=True, nullable=False)
    appointment_time = Column(Time, nullable=False)
    appointment_note = Column(String(255), nullable=False)
    status = Column(
        ENUM(AppointmentStatus, name="appointment_status", create_type=True),
        default=AppointmentStatus.SCHEDULED,
        nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Defining relationships between Doctor, User, and Prescription
    user = relationship("User", back_populates='appointments')
    doctor = relationship("Doctor", back_populates='appointments')
    prescriptions = relationship("Prescription", back_populates='appointment')
    symptoms = relationship("Symptom", back_populates='appointments')

    searchable_columns = ["appointment_note"]


    def __repr__(self):
        """
        String representation of the appointment
        note.
        """
        return (f'<Appointment: {self.appointment_note}, Scheduled on {self.appointment_date} '
                f'at {self.appointment_time}, between User {self.user_id} and Doctor {self.doctor_id}>')


    @classmethod
    def validate_appointment(cls, doctor_id, user_id, appointment_date, appointment_time):
        """
        Validate that a doctor and user do not have overlapping appointments
        """
        with get_db_session() as session:
            # Check for conflicting doctor appointments
            doctor_conflict = session.query(cls).filter(
                cls.doctor_id == doctor_id,
                cls.appointment_date == appointment_date,
                cls.appointment_time == appointment_time,
                cls.status != AppointmentStatus.CANCELLED  # Ignore cancelled appointments
            ).first()

            if doctor_conflict:
                raise ValueError("The doctor is not available at this time slot. Please choose another time.")

            # Check for conflicting user appointments
            user_conflict = session.query(cls).filter(
                cls.user_id == user_id,
                cls.appointment_date == appointment_date,
                cls.appointment_time == appointment_time,
                cls.status != AppointmentStatus.CANCELLED  # Ignore cancelled appointments
            ).first()

            if user_conflict:
                raise ValueError("You already have an appointment scheduled at this time slot. Please choose another time.")
    
    @classmethod
    def create_appointment(cls, doctor_id, user_id, appointment_date, appointment_time, appointment_note, user_tz):
        """
        Create and save an appointment after validating,
        storing time in UTC
        """
        logger = logging.getLogger(__name__)
        logger.debug(f"Creating appointment with params: doctor_id={doctor_id}, user_id={user_id}, "
                     f"date={appointment_date}, time={appointment_time}, tz={user_tz}")

        # Validate the appointment for conflicts
        cls.validate_appointment(doctor_id, user_id, appointment_date, appointment_time)
        logger.debug("Appointment validation passed")

        # Ensuring the appointment is in a future time
        cls.validate_future_date(appointment_date, appointment_time)
        logger.debug("Future date validation passed")

        try:
            # convert the appointment time to UTC
            user_timezone = timezone(user_tz)
            local_dt = datetime.combine(appointment_date, appointment_time)
            local_dt_with_tz = user_timezone.localize(local_dt)  # Add timezone info
            utc_dt = local_dt_with_tz.astimezone(utc)
            logger.debug(f"Converted time to UTC: {utc_dt}")
        
            with get_db_session() as session:
                # Get doctor information first
                doctor = session.query(Doctor).join(Doctor.user).filter(Doctor.id == doctor_id).first()
                if not doctor:
                    raise ValueError("Doctor not found")
                logger.debug(f"Found doctor: {doctor.user.first_name} {doctor.user.last_name}")

                appointment = cls(
                    doctor_id=doctor_id,
                    user_id=user_id,
                    appointment_date=utc_dt.date(),
                    appointment_time=utc_dt.time(),
                    appointment_note=appointment_note,
                    status=AppointmentStatus.SCHEDULED
                )
                session.add(appointment)
                session.commit()
                logger.debug(f"Created appointment with ID: {appointment.id}")
            
                # scheduling the reminder task
                reminder_time = utc_dt - timedelta(hours=1)
                send_reminder.apply_async(args=[appointment.id], eta=reminder_time)
                logger.debug("Scheduled reminder task")

                # Prepare response data within the session
                response_data = {
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
                        "id": doctor.id,
                        "first_name": doctor.user.first_name,
                        "last_name": doctor.user.last_name,
                        "specialization": doctor.specialization
                    }
                }
                logger.debug("Prepared response data")
                return response_data
            
        except Exception as e:
            logger.error(f"Failed to create appointment: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to create appointment: {str(e)}")

    @classmethod
    def get_appointment(cls, appointment_id, user_tz):
        """
        Retrieve an appointment and convert time to user's local timezone.
        """
        user_timezone = timezone(user_tz)

        with get_db_session() as session:
            appointment = session.query(cls).filter(cls.id == appointment_id).first()
            if not appointment:
                raise ValueError("Appointment not found.")

            # Convert UTC to user's timezone
            utc_dt = datetime.combine(appointment.appointment_date, appointment.appointment_time).replace(tzinfo=utc)
            local_dt = utc_dt.astimezone(user_timezone)

            return {
                "id": appointment.id,
                "doctor_id": appointment.doctor_id,
                "user_id": appointment.user_id,
                "appointment_note": appointment.appointment_note,
                "appointment_date": local_dt.date(),
                "appointment_time": local_dt.time(),
                "created_at": appointment.created_at,
                "updated_at": appointment.updated_at
            }

    @classmethod
    def validate_future_date(cls, appointment_date, appointment_time):
        """
        Ensure appointment is scheduled for
        a future time
        """
        now = datetime.utcnow()
        appointment_datetime = datetime.combine(appointment_date, appointment_time)
        if appointment_datetime <= now:
            raise ValueError("Appointment must be scheduled for a future time.")

    @classmethod
    def update_status(cls, appointment_id, status):
        """
        Update the status of an appointment.
        """
        if status not in AppointmentStatus.__members__:
            raise ValueError("Invalid Appointment status.")

        with get_db_session() as session:
            appointment = session.query(cls).filter(cls.id == appointment_id).first()
            if not appointment:
                raise ValueError("Appointment not found.")
            appointment.status = AppointmentStatus[status.capitalize()]
            session.commit()
            session.refresh(appointment)

        return appointment

    @classmethod
    def get_appointment_by_date(cls, start_date, end_date, doctor_id=None, user_id=None, limit=100, offset=0):
        """
        Fetch appointments within a date range and optionally
        filter by doctor or user.
        """
        with get_db_session() as session:
            query = session.query(cls).filter(
                cls.appointment_date >= start_date,
                cls.appointment_date <= end_date
            )
            if doctor_id:
                query = query.filter(cls.doctor_id == doctor_id)
            if user_id:
                query = query.filter(cls.user_id == user_id)

            return query.limit(limit).offset(offset).all()
    
    @classmethod
    def search_appointments(cls, user_id: int, keyword: str, session: Optional[Session] = None):
        """
        Search appointments by keyword for a specific user.
        """
        session_provided = session is not None
        if not session_provided:
            session = SessionLocal()

        try:
            results = cls.search(
                keyword=keyword,
                *cls.searchable_columns,
                session=session
            )
            return [appointment for appointment in results if appointment.user_id == user_id]

        finally:
            if not session_provided:
                session.close()