#!/usr/bin/env python3
"""
Testing the Symptom model
"""
import pytest
from .conftest import db_session
from ..app.models.user import User
from ..app.models.appointment import Appointment, AppointmentStatus
from ..app.models.doctor import Doctor
from ..app.models.symptom import Symptom
from sqlalchemy.exc import IntegrityError
from datetime import date, time


def test_create_symptom(db_session):
    user = User(
        first_name="Lara",
        last_name="Croft",
        username="laracroft",
        dob="2002-07-14",
        password_hash=User.set_password("tombraider"),
        email="lara.croft@example.com",
        city="London",
        state="",
        country="UK"
    )
    db_session.add(user)
    db_session.commit()

    appointment = Appointment(
        doctor_id=1,  # Assuming a doctor with id=1 exists
        user_id=user.id,
        appointment_date=date.today(),
        appointment_time=time(10, 0),
        appointment_note="Adventure planning",
        status="SCHEDULED"
    )
    db_session.add(appointment)
    db_session.commit()

    symptom = Symptom(
        user_id=user.id,
        appointment_id=appointment.id,
        symptom_name="Back Pain",
        severity_level="moderate",
        description="Occasional lower back pain after expeditions."
    )
    db_session.add(symptom)
    db_session.commit()
    db_session.refresh(symptom)

    assert symptom.id is not None
    assert symptom.symptom_name == "Back Pain"
    assert symptom.severity_level == "moderate"
    assert symptom.user.username == "laracroft"

def test_duplicate_symptom(db_session):
    user = User(
        first_name="Nathan",
        last_name="Drake",
        username="nathandrake",
        dob="2003-14-24",
        password_hash=User.set_password("treasure"),
        email="nathan.drake@example.com",
        city="San Francisco",
        state="CA",
        country="USA"
    )
    db_session.add(user)
    db_session.commit()

    doctor_user = User(
        first_name="Doctor",
        last_name="Strange",
        username="doctorstrange",
        dob="1980-05-11",
        password_hash=User.set_password("magic"),
        email="doctor.strange@example.com",
        city="Kamar-Taj",
        state="Nepal",
        country="Nepal"
    )
    db_session.add(doctor_user)
    db_session.commit()

    doctor = Doctor(
        user_id=doctor_user.id,
        doctor_username=doctor_user.username,
        phone_number="123-456-7890",
        specialization="Sorcery",
        license_number="LIC001"
    )
    db_session.add(doctor)
    db_session.commit()
    
    appointment = Appointment(
        doctor_id=doctor.id,
        user_id=user.id,
        appointment_date=date.today(),
        appointment_time=time(18, 30),
        appointment_note="Treasure hunting strategy",
        status="SCHEDULED"
    )
    db_session.add(appointment)
    db_session.commit()

    print(f"Appointment ID: {appointment.id}")  # Debugging
    assert appointment.id is not None, "Appointment ID is None. Ensure appointment is committed to the database."
    
    symptom1 = Symptom.create_symptom(
        session=db_session,
        user_id=user.id,
        appointment_id=appointment.id,
        symptom_name="Headache",
        severity_level="mild",
        description="Light headache after sunrise navigation."
    )
    db_session.add(symptom1)
    db_session.commit()

    print(f"Symptom 1 ID: {symptom1.id}, State: {symptom1}")  # Debugging

    with pytest.raises(ValueError) as excinfo:
        Symptom.create_symptom(
            session=db_session,
            user_id=user.id,
            appointment_id=appointment.id,
            symptom_name="Headache",
            severity_level="severe",
            description="Severe headache during treasure map decoding."
        )
    assert "already exists for this user" in str(excinfo.value)

def test_symptom_severity_validation(db_session):
    user = User(
        first_name="Arthur",
        last_name="Morgan",
        username="arthurmorgan",
        dob="2006-10-12",
        password_hash=User.set_password("outlaws"),
        email="arthur.morgan@example.com",
        city="Ambarino",
        state="WY",
        country="USA"
    )
    db_session.add(user)
    db_session.commit()

    appointment = Appointment(
        doctor_id=1,  # Assuming a doctor with id=1 exists
        user_id=user.id,
        appointment_date=date.today(),
        appointment_time=time(16, 0),
        appointment_note="Gang management",
        status="SCHEDULED"
    )
    db_session.add(appointment)
    db_session.commit()

    with pytest.raises(ValueError) as excinfo:
        Symptom.create_symptom(
            user_id=user.id,
            appointment_id=appointment.id,
            symptom_name="Nausea",
            severity_level="extreme",  # Invalid severity level
            description="Feeling extremely nauseous after a heist."
        )
    assert "Invalid severity level" in str(excinfo.value)

def test_update_symptom(db_session):
    user = User(
        first_name="Bruce",
        last_name="Wayne",
        username="brucewayne",
        dob="2000-02-02",
        password_hash=User.set_password("batman"),
        email="bruce.wayne@example.com",
        city="Gotham",
        state="NY",
        country="USA"
    )
    db_session.add(user)
    db_session.commit()

    doctor_user = User(
        first_name="Joshua",
        last_name="Perkins",
        username="joshperkins",
        dob="1987-07-22",
        password_hash=User.set_password("fabulous"),
        email="joshuaperkins@example.com",
        city="Brooklyn",
        state="New York",
        country="USA"
    )
    db_session.add(doctor_user)
    db_session.commit()

    doctor = Doctor(
        user_id=doctor_user.id,
        doctor_username=doctor_user.username,
        phone_number="123-456-7890",
        specialization="Pediatrics",
        license_number="LIC004"
    )
    db_session.add(doctor)
    db_session.commit()

    appointment = Appointment(
        doctor_id=doctor.id,
        user_id=user.id,
        appointment_date=date.today(),
        appointment_time=time(18, 30),
        appointment_note="Vigilante training",
        status=AppointmentStatus.SCHEDULED
    )
    db_session.add(appointment)
    db_session.commit()

    # Ensuring the appointment is committed to the database
    saved_appointment = db_session.query(Appointment).filter_by(id=appointment.id).first()
    print(f"Saved appointment: {saved_appointment}")
    print(f"Appointments in DB: {db_session.query(Appointment).all()}")
    assert saved_appointment is not None, "Appointment was not found in the database."

    symptom = Symptom.create_symptom(
        session=db_session,
        user_id=user.id,
        appointment_id=appointment.id,
        symptom_name="Arm Pain",
        severity_level="mild",
        description="Minor pain after combat training."
    )

    db_session.add(symptom)
    db_session.commit()

    # Ensure the symptom exists
    saved_symptom = db_session.query(Symptom).filter_by(id=symptom.id).first()
    print(f"Saved symptom: {saved_symptom}")
    print(f"Symptoms in DB: {db_session.query(Symptom).all()}")
    assert symptom is not None, "Symptom was not saved to the database."

    # Update the symptom
    updated_symptom = Symptom.update_symptom(
        session=db_session,
        symptom_id=symptom.id,
        severity_level="moderate",
        description="Increased pain after extended training sessions."
    )
    db_session.refresh(updated_symptom)

    assert updated_symptom.severity_level == "moderate"
    assert updated_symptom.description == "Increased pain after extended training sessions."

    # Verify unchanged attributes
    assert updated_symptom.symptom_name == "Arm Pain"
    assert updated_symptom.user_id == user.id
    assert updated_symptom.appointment_id == appointment.id