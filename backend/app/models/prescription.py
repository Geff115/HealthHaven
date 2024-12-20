#!/usr/bin/env python3
"""
Enhanced Prescription model
"""
from datetime import datetime, timedelta
from app.models.base import Base, SessionLocal
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.models.doctor import Doctor
from app.models.appointment import Appointment
import enum


class PrescriptionStatus(enum.Enum):
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    EXPIRED = "expired"


class Prescription(Base):
    __tablename__ = 'prescriptions'

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False)
    appointment_id = Column(Integer, ForeignKey('appointments.id'), nullable=False)
    medication_name = Column(String(80), nullable=False)
    dosage = Column(String(80), nullable=False)
    instructions = Column(String(255), nullable=False)
    status = Column(Enum(PrescriptionStatus), default=PrescriptionStatus.ACTIVE, nullable=False)
    expiry_date = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=30))  # Default to 30 days
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Defining relationships
    doctor = relationship('Doctor', back_populates='prescriptions')
    appointment = relationship('Appointment', back_populates='prescriptions')

    def __repr__(self):
        """
        String representation of the prescription
        """
        return (f'<Prescription: {self.medication_name} ({self.dosage}), '
                f'Status: {self.status.value}, Expires: {self.expiry_date.date()}, '
                f'Doctor: {self.doctor_id}>')

    @classmethod
    def create_prescription(cls, doctor_id, appointment_id, medication_name, dosage, instructions, duration_days=30):
        """
        Create and save a prescription.
        """
        if not medication_name or not dosage:
            raise ValueError("Medication name and dosage are required.")

        with SessionLocal() as session:
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

        with SessionLocal() as session:
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

        with SessionLocal() as session:
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
        with SessionLocal() as session:
            query = session.query(cls).filter(cls.doctor_id == doctor_id)
            if status:
                if status not in PrescriptionStatus.__members__:
                    raise ValueError("Invalid status filter.")
                query = query.filter(cls.status == PrescriptionStatus[status.upper()])
            return query.all()

    @classmethod
    def check_expired_prescriptions(cls):
        """
        Check and update expired prescriptions.
        """
        now = datetime.utcnow()
        with SessionLocal() as session:
            expired_prescriptions = session.query(cls).filter(
                cls.expiry_date < now,
                cls.status == PrescriptionStatus.ACTIVE
            ).all()
            for prescription in expired_prescriptions:
                prescription.status = PrescriptionStatus.EXPIRED
            session.commit()

        return expired_prescriptions