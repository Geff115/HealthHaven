#!/usr/bin/env python3
"""
Testing the Appointment model
"""
import pytest
from .conftest import db_session
from ..app.models.user import User
from ..app.models.doctor import Doctor
from ..app.models.appointment import Appointment, AppointmentStatus
from sqlalchemy.exc import IntegrityError
from datetime import date, time


def test_create_appointment(db_session):
    user = User(
        first_name="Henry",
        last_name="Ford",
        username="henryford",
        dob="2001-09-20",
        password_hash=User.set_password("modelT"),
        email="henry.ford@example.com",
        city="Detroit",
        state="MI",
        country="USA"
    )
    doctor_user = User(
        first_name="Isaac",
        last_name="Newton",
        username="isaacnewton",
        dob="2002-01-14",
        password_hash=User.set_password("gravity"),
        email="isaac.newton@example.com",
        city="Cambridge",
        state="MA",
        country="USA"
    )
    db_session.add_all([user, doctor_user])
    db_session.commit()

    doctor = Doctor(
        user_id=doctor_user.id,
        doctor_username=doctor_user.username,
        phone_number="111-222-3333",
        specialization="Physics",
        license_number="LIC777777"
    )
    db_session.add(doctor)
    db_session.commit()

    appointment = Appointment(
        doctor_id=doctor.id,
        user_id=user.id,
        appointment_date=date.today(),
        appointment_time=time(14, 30),
        appointment_note="Discuss research collaboration",
        status=AppointmentStatus.SCHEDULED
    )
    db_session.add(appointment)
    db_session.commit()
    db_session.refresh(appointment)

    assert appointment.id is not None
    assert appointment.status == AppointmentStatus.SCHEDULED
    assert appointment.doctor.specialization == "Physics"
    assert appointment.user.email == "henry.ford@example.com"
    assert appointment.doctor.doctor_username == "isaacnewton"
    db_session.rollback()

def test_overlapping_appointment_doctor(db_session):
    user1 = User(
        first_name="Jane",
        last_name="Austen",
        username="janeausten",
        dob="1999-04-27",
        password_hash=User.set_password("pride"),
        email="jane.austen@example.com",
        city="Bath",
        state="Somerset",
        country="UK"
    )
    user2 = User(
        first_name="Mark",
        last_name="Twain",
        username="marktwain",
        dob="1998-09-13",
        password_hash=User.set_password("huck"),
        email="mark.twain@example.com",
        city="Hartford",
        state="CT",
        country="USA"
    )
    db_session.add_all([user1, user2])
    db_session.commit()

    doctor_user = User(
        first_name="Albert",
        last_name="Einstein",
        username="alberteinstein",
        dob="2003-06-15",
        password_hash=User.set_password("relativity"),
        email="albert.einstein@example.com",
        city="Princeton",
        state="NJ",
        country="USA"
    )
    db_session.add(doctor_user)
    db_session.commit()

    doctor = Doctor(
        user_id=doctor_user.id,
        doctor_username=doctor_user.username,
        phone_number="444-555-6666",
        specialization="Theoretical Physics",
        license_number="LIC888888"
    )
    db_session.add(doctor)
    db_session.commit()

    appointment1 = Appointment(
        doctor_id=doctor.id,
        user_id=user1.id,
        appointment_date=date(2024, 5, 20),
        appointment_time=time(10, 0),
        appointment_note="Discuss quantum mechanics",
        status=AppointmentStatus.SCHEDULED
    )
    db_session.add(appointment1)
    db_session.commit()

    appointment2 = Appointment(
        doctor_id=doctor.id,
        user_id=user2.id,
        appointment_date=date(2024, 5, 20),
        appointment_time=time(10, 0),  # Same time as appointment1
        appointment_note="Discuss general relativity",
        status=AppointmentStatus.SCHEDULED
    )
    db_session.add(appointment2)
    with pytest.raises(IntegrityError):
        db_session.add(appointment2)
        db_session.commit()
        db_session.rollback()


def test_appointment_relationships(db_session):
    user = User(
        first_name="Laura",
        last_name="Ingalls",
        username="lauraingalls",
        dob="2004-07-08",
        password_hash=User.set_password("littlehouse"),
        email="laura.ingalls@example.com",
        city="Milwaukee",
        state="WI",
        country="USA"
    )
    db_session.add(user)
    db_session.commit()

    doctor_user = User(
        first_name="Thomas",
        last_name="Edison",
        username="thomasedison",
        dob="2003-09-19",
        password_hash=User.set_password("lightbulb"),
        email="thomas.edison@example.com",
        city="Milan",
        state="NJ",
        country="USA"
    )
    db_session.add(doctor_user)
    db_session.commit()
    
    doctor = Doctor(
        user_id=doctor_user.id,
        doctor_username=doctor_user.username,
        phone_number="777-888-9999",
        specialization="Electrical Engineering",
        license_number="LIC555555"
    )
    db_session.add(doctor)
    db_session.commit()
    
    appointment = Appointment(
        user_id=user.id,
        doctor_id=doctor.id,
        appointment_date=date(2024, 6, 15),
        appointment_time=time(16, 45),
        appointment_note="Innovations in energy storage",
        status=AppointmentStatus.SCHEDULED
    )
    db_session.add(appointment)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(doctor)
    
    # Verify relationships
    fetched_user = db_session.query(User).filter(User.id == user.id).first()
    fetched_doctor = db_session.query(Doctor).filter(Doctor.id == doctor.id).first()
    
    assert len(fetched_user.appointments) == 1
    assert fetched_user.appointments[0].appointment_note == "Innovations in energy storage"
    
    assert len(fetched_doctor.appointments) == 1
    assert fetched_doctor.appointments[0].user.username == "lauraingalls"

    # Assertions to validate cascading deletions
    db_session.delete(fetched_user)
    db_session.commit()
    assert db_session.query(Appointment).filter(Appointment.user_id == user.id).count() == 0
    db_session.rollback()
