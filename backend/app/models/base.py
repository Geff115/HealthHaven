#!/usr/bin/env python3
"""
Initializing the SQLAlchemy declarative base for
the models, and setting up the async engine and
sessionmaker for database connections
"""
from config import database_url
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.models.user import User
from app.models.doctor import Doctor
from app.models.symptom import Symptom
from app.models.appointment import Appointment
from app.models.prescription import Prescription
from app.models.medical_record import MedicalRecord


# Setting up SQLAlchemy dclarative base
Base = declarative_base()

# Setting up the engine
engine = create_engine(database_url, echo=True)

# Setting up a synchronous session
SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)
