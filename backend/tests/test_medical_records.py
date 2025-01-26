#!/usr/bin/env python3
"""
Testing the Medical records model
"""
import pytest
from .conftest import db_session
from ..app.models.user import User
from ..app.models.doctor import Doctor
from ..app.models.medical_record import MedicalRecord
from ..app.models.appointment import Appointment
from sqlalchemy.exc import IntegrityError
from datetime import date, time


def test_create_medical_record(db_session):
    user = User(
        first_name="Peter",
        last_name="Parker",
        username="peterparker",
        dob="2002-10-12",
        password_hash=User.set_password("spiderman"),
        email="peter.parker@example.com",
        city="New York",
        state="NY",
        country="USA"
    )
    doctor_user = User(
        first_name="Alfred",
        last_name="Pennyworth",
        username="alfredpennyworth",
        dob="2003-04-14",
        password_hash=User.set_password("butler"),
        email="alfred.pennyworth@example.com",
        city="London",
        state="",
        country="UK"
    )
    db_session.add_all([user, doctor_user])
    db_session.commit()

    doctor = Doctor(
        user_id=doctor_user.id,
        doctor_username=doctor_user.username,
        phone_number="000-111-2222",
        specialization="General Medicine",
        license_number="LIC121212"
    )
    db_session.add(doctor)
    db_session.commit()

    appointment = Appointment(
        doctor_id=doctor.id,
        user_id=user.id,
        appointment_date=date.today(),
        appointment_time=time(12, 0),
        appointment_note="Routine check-up",
        status="Completed"
    )
    db_session.add(appointment)
    db_session.commit()

    medical_record = MedicalRecord(
        user_id=user.id,
        doctor_id=doctor.id,
        record_date=date.today(),
        description="Routine annual physical examination.",
        diagnosis="Healthy",
        treatment_plan="Maintain current health regimen."
    )
    db_session.add(medical_record)
    db_session.commit()
    db_session.refresh(medical_record)

    assert medical_record.id is not None
    assert medical_record.user.first_name == "Peter"
    assert medical_record.doctor.specialization == "General Medicine"
    assert medical_record.diagnosis == "Healthy"
    assert medical_record.doctor.doctor_username == "alfredpennyworth"
    assert medical_record.user.username == "peterparker"

def test_medical_record_relationships(db_session):
    user = User(
        first_name="Clark",
        last_name="Kent",
        username="clarkkent",
        dob="1999-05-17",
        password_hash=User.set_password("superman"),
        email="clark.kent@example.com",
        city="Metropolis",
        state="NY",
        country="USA"
    )
    doctor_user = User(
        first_name="Lois",
        last_name="Lane",
        username="loislane",
        dob="1998-09-18",
        password_hash=User.set_password("journalist"),
        email="lois.lane@example.com",
        city="Metropolis",
        state="NY",
        country="USA"
    )
    db_session.add_all([user, doctor_user])
    db_session.commit()

    doctor = Doctor(
        user_id=doctor_user.id,
        doctor_username=doctor_user.username,
        phone_number="333-444-5555",
        specialization="Journalism",
        license_number="LIC131313"
    )
    db_session.add(doctor)
    db_session.commit()

    appointment = Appointment(
        doctor_id=doctor.id,
        user_id=user.id,
        appointment_date=date.today(),
        appointment_time=time(10, 30),
        appointment_note="Investigative reporting",
        status="Completed"
    )
    db_session.add(appointment)
    db_session.commit()

    medical_record = MedicalRecord(
        user_id=user.id,
        doctor_id=doctor.id,
        record_date=date.today(),
        description="Extensive interview techniques.",
        diagnosis="N/A",
        treatment_plan="Enhance investigative skills."
    )
    db_session.add(medical_record)
    db_session.commit()

    fetched_user = db_session.query(User).filter(User.id == user.id).first()
    fetched_doctor = db_session.query(Doctor).filter(Doctor.id == doctor.id).first()

    assert len(fetched_user.medical_records) == 1
    assert fetched_user.medical_records[0].description == "Extensive interview techniques."

    assert len(fetched_doctor.medical_records) == 1
    assert fetched_doctor.medical_records[0].user.username == "clarkkent"

    assert fetched_user.medical_records[0].doctor.specialization == "Journalism"
    assert fetched_doctor.medical_records[0].diagnosis == "N/A"

def test_search_medical_records(db_session):
    user = User(
        first_name="Tony",
        last_name="Stark",
        username="tonystark",
        dob="2004-09-27",
        password_hash=User.set_password("ironman"),
        email="tony.stark@example.com",
        city="Los Angeles",
        state="CA",
        country="USA"
    )
    doctor_user = User(
        first_name="Pepper",
        last_name="Potts",
        username="pepperpotts",
        dob="2003-06-14",
        password_hash=User.set_password("manager"),
        email="pepper.potts@example.com",
        city="Los Angeles",
        state="CA",
        country="USA"
    )
    db_session.add_all([user, doctor_user])
    db_session.commit()

    doctor = Doctor(
        user_id=doctor_user.id,
        doctor_username=doctor_user.username,
        phone_number="666-777-8888",
        specialization="Business Management",
        license_number="LIC141414"
    )
    db_session.add(doctor)
    db_session.commit()

    appointment1 = Appointment(
        doctor_id=doctor.id,
        user_id=user.id,
        appointment_date=date(2024, 8, 1),
        appointment_time=time(9, 0),
        appointment_note="Business strategy session",
        status="Completed"
    )
    appointment2 = Appointment(
        doctor_id=doctor.id,
        user_id=user.id,
        appointment_date=date(2024, 8, 15),
        appointment_time=time(14, 0),
        appointment_note="Product launch planning",
        status="Completed"
    )
    db_session.add_all([appointment1, appointment2])
    db_session.commit()

    medical_record1 = MedicalRecord(
        user_id=user.id,
        doctor_id=doctor.id,
        record_date=date(2024, 8, 1),
        description="Reviewed business strategy.",
        diagnosis="N/A",
        treatment_plan="Implement new market analysis tools."
    )
    medical_record2 = MedicalRecord(
        user_id=user.id,
        doctor_id=doctor.id,
        record_date=date(2024, 8, 15),
        description="Planned product launch.",
        diagnosis="N/A",
        treatment_plan="Execute marketing campaign."
    )
    db_session.add_all([medical_record1, medical_record2])
    db_session.commit()

    # Test case 1: Search by keyword in description
    records = MedicalRecord.search_records("marketing", db_session)
    assert len(records) == 1
    assert records[0].description == "Planned product launch."

    # Test case 2: Search by keyword in treatment_plan
    records = MedicalRecord.search_records("market", db_session)
    assert len(records) == 2
    descriptions = [record.description for record in records]
    assert "Reviewed business strategy." in descriptions
    assert "Planned product launch." in descriptions

    # Test case 3: Search with no matching record
    records = MedicalRecord.search_records("nonexistent", db_session)
    assert len(records) == 0

    # Test case 4: Case-insensitive search
    records = MedicalRecord.search_records("MARKETING", db_session)
    assert len(records) == 1
    assert records[0].description == "Planned product launch."