#!/usr/bin/env python3
"""
Testing the Doctor model
"""
import pytest
from .conftest import db_session
from ..app.models.user import User
from ..app.models.doctor import Doctor
from sqlalchemy.exc import IntegrityError


def test_create_doctor(db_session):
    user = User(
        first_name="Emily",
        last_name="Clark",
        username="emilyclark",
        dob="2000-07-14",
        password_hash=User.set_password("password123"),
        email="emily.clark@example.com",
        city="Boston",
        state="MA",
        country="USA"
    )
    db_session.add(user)
    db_session.commit()

    doctor = Doctor(
        user_id=user.id,
        doctor_username=user.username,
        phone_number="123-456-7890",
        specialization="Cardiology",
        license_number="LIC123456"
    )
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(doctor)

    assert doctor.id is not None
    assert doctor.specialization == "Cardiology"
    assert doctor.user.username == "emilyclark"

def test_unique_license_number(db_session):
    user1 = User(
        first_name="Frank",
        last_name="Sinatra",
        username="franksinatra",
        dob="2001-10-12",
        password_hash=User.set_password("swing"),
        email="frank.sinatra@example.com",
        city="New York",
        state="NY",
        country="USA"
    )
    user2 = User(
        first_name="Frankie",
        last_name="Valli",
        username="frankievalli",
        dob="2002-02-02",
        password_hash=User.set_password("valli"),
        email="frankie.valli@example.com",
        city="Philadelphia",
        state="PA",
        country="USA"
    )
    db_session.add_all([user1, user2])
    db_session.commit()

    doctor1 = Doctor(
        user_id=user1.id,
        doctor_username=user1.username,
        phone_number="987-654-3210",
        specialization="Neurology",
        license_number="LIC654321"
    )
    doctor2 = Doctor(
        user_id=user2.id,
        doctor_username=user2.username,
        phone_number="654-321-0987",
        specialization="Pediatrics",
        license_number="LIC654321"  # Duplicate license number
    )
    
    db_session.add(doctor1)
    db_session.commit()

    db_session.add(doctor2)
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_doctor_relationship_with_user(db_session):
    user = User(
        first_name="Grace",
        last_name="Hopper",
        username="gracehopper",
        dob="2003-04-17",
        password_hash=User.set_password("cobol"),
        email="grace.hopper@example.com",
        city="Arlington",
        state="VA",
        country="USA"
    )
    db_session.add(user)
    db_session.commit()

    doctor = Doctor(
        user_id=user.id,
        doctor_username=user.username,
        phone_number="555-555-5555",
        specialization="Computer Science",
        license_number="LIC999999"
    )
    db_session.add(doctor)
    db_session.commit()

    fetched_doctor = db_session.query(Doctor).filter(Doctor.user_id == user.id).first()
    assert fetched_doctor.user.email == "grace.hopper@example.com"