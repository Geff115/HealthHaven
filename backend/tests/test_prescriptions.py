#!/usr/bin/env python3
"""
Testing the Prescription model
"""
import pytest
from .conftest import db_session
from ..app.models.user import User
from ..app.models.doctor import Doctor
from ..app.models.appointment import Appointment, AppointmentStatus
from ..app.models.prescription import Prescription, PrescriptionStatus
from sqlalchemy.exc import IntegrityError
from datetime import date, time, timedelta
from pytz import UTC


def test_create_prescription(db_session):
    user = User(
        first_name="Victor",
        last_name="Hugo",
        username="victorhugo",
        dob="2003-04-04",
        password_hash=User.set_password("lesmis"),
        email="victor.hugo@example.com",
        city="Paris",
        state="",
        country="France"
    )
    doctor_user = User(
        first_name="Marie",
        last_name="Curie",
        username="mariecurie",
        dob="2002-09-17",
        password_hash=User.set_password("radiation"),
        email="marie.curie@example.com",
        city="Warsaw",
        state="",
        country="Poland"
    )
    db_session.add_all([user, doctor_user])
    db_session.commit()

    doctor = Doctor(
        user_id=doctor_user.id,
        doctor_username=doctor_user.username,
        phone_number="222-333-4444",
        specialization="Chemistry",
        license_number="LIC333333"
    )
    db_session.add(doctor)
    db_session.commit()

    appointment = Appointment(
        doctor_id=doctor.id,
        user_id=user.id,
        appointment_date=date.today(),
        appointment_time=time(9, 15),
        appointment_note="Follow-up on treatment",
        status=AppointmentStatus.SCHEDULED
    )
    db_session.add(appointment)
    db_session.commit()

    prescription = Prescription(
        doctor_id=doctor.id,
        appointment_id=appointment.id,
        medication_name="Amoxicillin",
        dosage="500mg",
        instructions="Take three times a day",
        status=PrescriptionStatus.ACTIVE
    )
    db_session.add(prescription)
    db_session.commit()
    db_session.refresh(prescription)

    assert prescription.id is not None
    assert prescription.medication_name == "Amoxicillin"
    assert prescription.status == PrescriptionStatus.ACTIVE
    assert prescription.doctor.doctor_username == "mariecurie"
    assert prescription.appointment.appointment_note == "Follow-up on treatment"

def test_prescription_enum_validation(db_session):
    user = User(
        first_name="Ernest",
        last_name="Hemingway",
        username="ernesthemingway",
        dob="2004-08-14",
        password_hash=User.set_password("forwhom"),
        email="ernest.hemingway@example.com",
        city="Oak Park",
        state="IL",
        country="USA"
    )
    doctor_user = User(
        first_name="Nikola",
        last_name="Tesla",
        username="nikolatesla",
        dob="1999-04-14",
        password_hash=User.set_password("alternating"),
        email="nikola.tesla@example.com",
        city="Smiljan",
        state="",
        country="Croatia"
    )
    db_session.add_all([user, doctor_user])
    db_session.commit()

    doctor = Doctor(
        user_id=doctor_user.id,
        doctor_username=doctor_user.username,
        phone_number="555-666-7777",
        specialization="Electrical Engineering",
        license_number="LIC444444"
    )
    db_session.add(doctor)
    db_session.commit()

    appointment = Appointment(
        doctor_id=doctor.id,
        user_id=user.id,
        appointment_date=date.today(),
        appointment_time=time(11, 0),
        appointment_note="Electrical safety review",
        status=AppointmentStatus.SCHEDULED
    )
    db_session.add(appointment)
    db_session.commit()

    # Attempt to set an invalid status
    with pytest.raises(ValueError, match="Invalid status"):
        prescription = Prescription(
            doctor_id=doctor.id,
            appointment_id=appointment.id,
            medication_name="Ibuprofen",
            dosage="200mg",
            instructions="Take as needed",
            status="invalid_status"  # Invalid status
        )
        db_session.add(prescription)
        db_session.commit()

def test_prescription_relationships(db_session):
    user = User(
        first_name="George",
        last_name="Orwell",
        username="georgeorwell",
        dob="2002-04-14",
        password_hash=User.set_password("1984"),
        email="george.orwell@example.com",
        city="Motihari",
        state="",
        country="India"
    )
    doctor_user = User(
        first_name="Ada",
        last_name="Lovelace",
        username="adalovelace",
        dob="2002-09-19",
        password_hash=User.set_password("computing"),
        email="ada.lovelace@example.com",
        city="London",
        state="",
        country="UK"
    )
    db_session.add_all([user, doctor_user])
    db_session.commit()

    doctor = Doctor(
        user_id=doctor_user.id,
        doctor_username=doctor_user.username,
        phone_number="333-444-5555",
        specialization="Computer Science",
        license_number="LIC666666"
    )
    db_session.add(doctor)
    db_session.commit()

    appointment = Appointment(
        doctor_id=doctor.id,
        user_id=user.id,
        appointment_date=date(2024, 7, 10),
        appointment_time=time(13, 30),
        appointment_note="Algorithm optimization",
        status=AppointmentStatus.SCHEDULED
    )
    db_session.add(appointment)
    db_session.commit()

    prescription1 = Prescription(
        doctor_id=doctor.id,
        appointment_id=appointment.id,
        medication_name="Paracetamol",
        dosage="500mg",
        instructions="Take after meals",
        status=PrescriptionStatus.ACTIVE
    )
    prescription2 = Prescription(
        doctor_id=doctor.id,
        appointment_id=appointment.id,
        medication_name="Metformin",
        dosage="850mg",
        instructions="Twice daily with breakfast and dinner",
        status=PrescriptionStatus.ACTIVE
    )
    db_session.add_all([prescription1, prescription2])
    db_session.commit()
    db_session.rollback()

    fetched_doctor = db_session.query(Doctor).filter(Doctor.id == doctor.id).first()
    assert len(fetched_doctor.prescriptions) == 2
    assert fetched_doctor.prescriptions[0].medication_name == "Paracetamol"
    assert fetched_doctor.prescriptions[1].medication_name == "Metformin"

def test_check_expired_prescriptions(db_session):
    from datetime import datetime
    from pytz import timezone

    # Setup entities: user, doctor, appointment, prescription
    user = User(
        first_name="Harry",
        last_name="Potter",
        username="harrypotter",
        dob="2001-10-10",
        password_hash=User.set_password("expelliarmus"),
        email="harry.potter@example.com",
        city="London",
        state="",
        country="UK"
    )
    doctor_user = User(
        first_name="Severus",
        last_name="Snape",
        username="severussnape",
        dob="2006-04-07",
        password_hash=User.set_password("potions"),
        email="severus.snape@example.com",
        city="London",
        state="",
        country="UK"
    )
    db_session.add_all([user, doctor_user])
    db_session.commit()

    doctor = Doctor(
        user_id=doctor_user.id,
        doctor_username=doctor_user.username,
        phone_number="888-999-0000",
        specialization="Potions",
        license_number="LIC101010"
    )
    db_session.add(doctor)
    db_session.commit()

    appointment = Appointment(
        doctor_id=doctor.id,
        user_id=user.id,
        appointment_date=date.today(),
        appointment_time=time(15, 0),
        appointment_note="Advanced potion brewing",
        status=AppointmentStatus.COMPLETED
    )
    db_session.add(appointment)
    db_session.commit()

    lagos_timezone = timezone("Africa/Lagos")
    expiry_date = lagos_timezone.localize(datetime(2024, 12, 25, 9, 0, 0))

    prescription = Prescription(
        doctor_id=doctor.id,
        appointment_id=appointment.id,
        medication_name="Felix Felicis",
        dosage="10ml",
        instructions="Drink once for good luck",
        status=PrescriptionStatus.ACTIVE,
        expiry_date=expiry_date
    )
    db_session.add(prescription)
    db_session.commit()

    # Call check_expired_prescriptions
    expired_prescriptions = Prescription.check_expired_prescriptions(db_session)

    # Verify results
    assert len(expired_prescriptions) == 1
    updated_prescription = expired_prescriptions[0]
    assert updated_prescription.status == PrescriptionStatus.EXPIRED

    # Query the database to confirm status was updated
    refreshed_prescription = db_session.query(Prescription).filter_by(id=prescription.id).first()
    assert refreshed_prescription.status == PrescriptionStatus.EXPIRED