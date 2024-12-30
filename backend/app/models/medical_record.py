#!/usr/bin/env python3
"""
MedicalRecord model
"""
from datetime import datetime
from .base import Base
from ..db.session import get_db_session
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship


class MedicalRecord(Base):
    __tablename__ = 'medical_records'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors.id', ondelete='CASCADE'), index=True, nullable=False)
    record_date = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    description = Column(String(255), nullable=False)
    diagnosis = Column(String(255), nullable=True, index=True)  # Optional diagnosis
    treatment_plan = Column(String(255), nullable=True, index=True)  # Optional treatment plan
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates='medical_records')
    doctor = relationship("Doctor", back_populates='medical_records')


    def __repr__(self):
        """
        String representation of the medical record
        """
        return (f'<MedicalRecord: User: {self.user_id}, Doctor: {self.doctor_id}, '
                f'Diagnosis: {self.diagnosis}, Record Date: {self.record_date.date()}>')

    @classmethod
    def create_medical_record(cls, user_id, doctor_id, description, diagnosis=None, treatment_plan=None):
        """
        Create a new medical record.
        """
        if not description:
            raise ValueError("Description is required for a medical record.")

        with get_db_session() as session:
            record = cls(
                user_id=user_id,
                doctor_id=doctor_id,
                description=description,
                diagnosis=diagnosis,
                treatment_plan=treatment_plan
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    @classmethod
    def get_records_by_user(cls, user_id):
        """
        Retrieve all medical records for a specific user.
        """
        with get_db_session() as session:
            records = session.query(cls).filter(cls.user_id == user_id).all()
            return records

    @classmethod
    def get_records_by_doctor(cls, doctor_id):
        """
        Retrieve all medical records created by a specific doctor.
        """
        with get_db_session() as session:
            records = session.query(cls).filter(cls.doctor_id == doctor_id).all()
            return records

    @classmethod
    def search_records(cls, keyword, session=None):
        """
        Search medical records by a keyword in the diagnosis or treatment plan.
        """
        session = session or get_db_session()
        records = session.query(cls).filter(
            (cls.diagnosis.ilike(f"%{keyword}%")) |
            (cls.treatment_plan.ilike(f"%{keyword}%")) |
            (cls.description.ilike(f"%{keyword}%"))
        ).all()

        return records