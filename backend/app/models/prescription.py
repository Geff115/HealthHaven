#!/usr/bin/env python3
"""
Enhanced Prescription model
"""
import logging
from datetime import datetime, timedelta
from .base import Base
from ..db.session import get_db_session
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.sql import func
from sqlalchemy import and_, or_
from enum import Enum as PyEnum
from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger(__name__)


class PrescriptionStatus(PyEnum):
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    EXPIRED = "expired"


class Prescription(Base):
    __tablename__ = 'prescriptions'

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id', ondelete='CASCADE'), index=True, nullable=False)
    appointment_id = Column(Integer, ForeignKey('appointments.id', ondelete='CASCADE'), index=True, nullable=False)
    medication_name = Column(String(80), nullable=False)
    dosage = Column(String(80), nullable=False)
    instructions = Column(String(255), nullable=False)
    status = Column(
        ENUM(PrescriptionStatus, name="prescription_status", create_type=True),
        default=PrescriptionStatus.ACTIVE,
        nullable=False
    )
    expiry_date = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=30))  # Default to 30 days
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Defining relationships
    doctor = relationship("Doctor", back_populates='prescriptions')
    appointment = relationship("Appointment", back_populates='prescriptions')

    searchable_columns = ["prescription_name", "dosage"]

    def __repr__(self):
        """
        String representation of the prescription
        """
        return (f'<Prescription: {self.medication_name} ({self.dosage}), '
                f'Status: {self.status.value}, Expires: {self.expiry_date.date()}, '
                f'Doctor: {self.doctor_id}>')

    @validates('status')
    def validate_status(self, key, value):
        """
        Validate the status to ensure it matches a valid PrescriptionStatus value.
        """
        if value not in list(PrescriptionStatus):
            raise ValueError(f"Invalid status: {value}. Must be one of {list(PrescriptionStatus.__members__.values())}.")
        return value

    @classmethod
    def create_prescription(cls, doctor_id, appointment_id, medication_name, dosage, instructions, duration_days=30):
        """
        Create and save a prescription.
        """
        if not medication_name or not dosage:
            raise ValueError("Medication name and dosage are required.")

        with get_db_session() as session:
            prescription = cls(
                doctor_id=doctor_id,
                appointment_id=appointment_id,
                medication_name=medication_name,
                dosage=dosage,
                instructions=instructions,
                expiry_date=datetime.utcnow() + timedelta(days=duration_days)
            )
            session.add(prescription)
            session.commit()
            session.refresh(prescription)

        return prescription
    
    @classmethod
    def get_prescription_by_medication_name(cls, medicine, doctor_id):
        """
        Search for a certain medication name prescribed by a doctor
        """
        if not medicine:
            raise ValueError("Please specify a medicine name.")

        with get_db_session() as session:
            prescribed_drug = session.query(cls).filter(
                cls.medication_name == medicine,
                cls.doctor_id == doctor_id
            ).all()

            if not prescribed_drug:
                raise ValueError("The medicine entered hasn't been prescribed by this doctor.")

        return prescribed_drug

    @classmethod
    def update_status(cls, prescription_id, status):
        """
        Update the status of a prescription.
        """
        if status not in PrescriptionStatus.__members__:
            raise ValueError("Invalid prescription status.")

        with get_db_session() as session:
            prescription = session.query(cls).filter(cls.id == prescription_id).first()
            if not prescription:
                raise ValueError("Prescription not found.")
            prescription.status = PrescriptionStatus[status.capitalize()]
            session.commit()
            session.refresh(prescription)

        return prescription

    @classmethod
    def get_prescription_by_doctor_and_status(cls, doctor_id, status=None):
        """
        Retrieve prescriptions by doctor, optionally filtering by status.
        """
        with get_db_session() as session:
            query = session.query(cls).filter(cls.doctor_id == doctor_id)
            if status:
                if status not in PrescriptionStatus.__members__:
                    raise ValueError("Invalid status filter.")
                query = query.filter(cls.status == PrescriptionStatus[status.upper()])
            return query.all()
    
    @classmethod
    def check_expired_prescriptions(cls, session=None):
        from datetime import datetime
        from pytz import timezone

        db_timezone = timezone("Africa/Lagos")

        # Use the provided session or create a new one
        internal_session = False
        if session is None:
            session = get_db_session()
            internal_session = True

        try:
            # Current time
            now = datetime.now(db_timezone).replace(microsecond=0)

            # Check if the database is SQLite
            if session.bind.dialect.name == "sqlite":
                expired_prescriptions = session.query(cls).filter(
                    cls.expiry_date < now,
                    cls.status == PrescriptionStatus.ACTIVE
                ).all()
            else:
                expired_prescriptions = session.query(cls).filter(
                    func.timezone("Africa/Lagos", cls.expiry_date) < now,
                    cls.status == PrescriptionStatus.ACTIVE
                ).all()

            for prescription in expired_prescriptions:
                prescription.status = PrescriptionStatus.EXPIRED

            session.commit()

            for prescription in expired_prescriptions:
                session.refresh(prescription)

            return expired_prescriptions

        finally:
            if internal_session:
                session.close()
    
    @classmethod
    def search_prescriptions(cls, user_id: int, keyword: str, session: Optional[Session] = None):
        """
        Search prescriptions by keyword for a specific user.
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
            return [prescription for prescription in results if prescription.user_id == user_id]

        finally:
            if not session_provided:
                session.close()
