#!/usr/bin/env python3
"""
Appointment model
"""
from datetime import datetime, timedelta
from app.models.base import Base, SessionLocal
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import Session, relationship
from sqlalchemy import Date, Time, ForeignKey
from app.models.user import User
from app.models.doctor import Doctor
from app.models.symptom import Symptom
from app.models.prescription import Prescription
from tasks import send_reminder
from pytz import timezone, utc
from enum import Enum as PyEnum


class AppointmentStatus(PyEnum):
    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class Appointment(Base):
    __tablename__ = 'appointments'

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(Time, nullable=False)
    appointment_note = Column(String(255), nullable=False)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Defining relationships between Doctor, User, and Prescription
    user = relationship('User', back_populates='appointments')
    doctor = relationship('Doctor', back_populates='appointments')
    prescription = relationship('Prescription', back_populates='appointments')
    symptoms = relationship('Symptom', back_populates='appointments')


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
        with SessionLocal() as session:
            # Check for overlapping appointments for the doctor
            doctor_conflict = session.query(cls).filter(
                cls.doctor_id == doctor_id,
                cls.appointment_date == appointment_date,
                cls.appointment_time == appointment_time
            ).first()

            if doctor_conflict:
                raise ValueError(f"Doctor {doctor_id} already has an appointment at this time.")

            # Check for overlapping appointments for the user
            user_conflict = session.query(cls).filter(
                cls.user_id == user_id,
                cls.appointment_date == appointment_date,
                cls.appointment_time == appointment_time
            ).first()

            if user_conflict:
                raise ValueError(f"User {user_id} already has an appointment at this time.")
    
    @classmethod
    def create_appointment(cls, doctor_id, user_id, appointment_date, appointment_time, appointment_note, user_tz):
        """
        Create and save an appointment after validating,
        storing time in UTC
        """
        # Validate the appointment for conflicts
        cls.validate_appointment(doctor_id, user_id, appointment_date, appointment_time)

        # Ensuring the appointment is in a future time
        cls.validate_future_date(appointment_date, appointment_time)

        # convert the appointment time to UTC
        user_timezone = timezone(user_tz)
        local_dt = datetime.combine(appointment_date, appointment_time)
        local_dt_with_tz = user_timezone.localize(local_dt)  # Add timezone info
        utc_dt = local_dt_with_tz.astimezone(utc)

        # Create and save the appointment
        with SessionLocal() as session:
            appointment = cls(
                doctor_id=doctor_id,
                user_id=user_id,
                appointment_date=utc_dt.date(),
                appointment_time=utc_dt.time(),
                appointment_note=appointment_note
            )
            session.add(appointment)
            session.commit()
            session.refresh(appointment)

            # scheduling the reminder task
            reminder_time = utc_dt - timedelta(hours=1)  # Send reminder 1 hour before
            send_reminder.apply_async(args=[appointment.id], eta=reminder_time)

        return appointment

    @classmethod
    def get_appointment(cls, appointment_id, user_tz):
        """
        Retrieve an appointment and convert time to user's local timezone.
        """
        user_timezone = timezone(user_tz)

        with SessionLocal() as session:
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

        with SessionLocal() as session:
            appointment = session.query(cls).filter(cls.id == appointment_id).first()
            if not appointment:
                raise ValueError("Appointment not found.")
            appointment.status = AppointmentStatus[status.capitalize()]
            session.commit()
            session.refresh(appointment)

        return appointment

    @classmethod
    def get_appointment_by_date(cls, start_date, end_date, doctor_id=None, user_id=None):
        """
        Fetch appointments within a date range and optionally
        filter by doctor or user.
        """
        with SessionLocal() as session:
            query = session.query(cls).filter(
                cls.appointment_date >= start_date,
                cls.appointment_date <= end_date
            )
            if doctor_id:
                query = query.filter(cls.doctor_id == doctor_id)
            if user_id:
                query = query.filter(cls.user_id == user_id)

            return query.all()