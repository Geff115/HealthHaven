#!/usr/bin/env python3
"""
Enhanced Symptom model
"""
from datetime import datetime
from app.models.base import Base, SessionLocal
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.models.user import User
from app.models.appointment import Appointment


class Symptom(Base):
    __tablename__ = 'symptoms'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    appointment_id = Column(Integer, ForeignKey('appointments.id'), nullable=False)
    symptom_name = Column(String(80), nullable=False)
    severity_level = Column(Enum("mild", "moderate", "severe", name="severity_level"), nullable=False)
    description = Column(String(255), nullable=True)  # Optional field
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='symptoms')
    appointment = relationship('Appointment', back_populates='symptoms')

    def __repr__(self):
        """
        String representation of the symptom
        """
        return (f'<Symptom: {self.symptom_name} (Severity: {self.severity_level}), '
                f'User: {self.user_id}, Appointment: {self.appointment_id}>')

    @classmethod
    def create_symptom(cls, user_id, appointment_id, symptom_name, severity_level, description=None):
        """
        Create a symptom for a user.
        """
        if not symptom_name:
            raise ValueError("Symptom name must be specified.")
        if severity_level not in ["mild", "moderate", "severe"]:
            raise ValueError("Invalid severity level. Choose from 'mild', 'moderate', or 'severe'.")

        with SessionLocal() as session:
            existing_symptom = session.query(cls).filter(
                cls.user_id == user_id,
                cls.symptom_name == symptom_name
            ).first()
            if existing_symptom:
                raise ValueError("This symptom already exists for this user.")

            symptom = cls(
                user_id=user_id,
                appointment_id=appointment_id,
                symptom_name=symptom_name,
                severity_level=severity_level,
                description=description
            )
            session.add(symptom)
            session.commit()
            session.refresh(symptom)
            return symptom

    @classmethod
    def get_symptom_by_name(cls, symptom_name):
        """
        Fetch symptoms by name.
        """
        if not symptom_name:
            raise ValueError("Symptom name must be specified.")
        if not isinstance(symptom_name, str):
            raise TypeError("Symptom name must be a string.")

        with SessionLocal() as session:
            symptoms = session.query(cls).filter(cls.symptom_name == symptom_name).all()
            if not symptoms:
                return f"No symptoms found with the name: {symptom_name}"

            return symptoms

    @classmethod
    def get_symptoms_by_severity(cls, severity_level):
        """
        Fetch symptoms by severity level.
        """
        if severity_level not in ["mild", "moderate", "severe"]:
            raise ValueError("Invalid severity level. Choose from 'mild', 'moderate', or 'severe'.")

        with SessionLocal() as session:
            symptoms = session.query(cls).filter(cls.severity_level == severity_level).all()
            return symptoms

    @classmethod
    def update_symptom(cls, symptom_id, **kwargs):
        """
        Update a symptom's details.
        """
        with SessionLocal() as session:
            symptom = session.query(cls).filter(cls.id == symptom_id).first()
            if not symptom:
                raise ValueError("Symptom not found.")

            for key, value in kwargs.items():
                if hasattr(symptom, key) and key != "id":
                    setattr(symptom, key, value)

            session.commit()
            session.refresh(symptom)
            return symptom
