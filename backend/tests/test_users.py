#!/usr/bin/env python3
"""
Testing the User model
"""
import pytest
from .conftest import db_session
from ..app.models.user import User
from sqlalchemy.exc import IntegrityError


def test_create_user(db_session):
    user = User(
        first_name="John",
        last_name="Doe",
        username="johndoe",
        dob="14-08-2002",
        password_hash=User.set_password("securepassword"),
        email="johndoe@example.com",
        city="New York",
        state="NY",
        country="USA"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.username == "johndoe"
    assert user.check_password("securepassword") is True

def test_unique_username(db_session):
    user1 = User(
        first_name="Alice",
        last_name="Smith",
        username="alicesmith",
        dob="1999-08-02",
        password_hash=User.set_password("password1"),
        email="alice.smith@example.com",
        city="Los Angeles",
        state="CA",
        country="USA"
    )
    user2 = User(
        first_name="Alicia",
        last_name="Brown",
        username="alicesmith",  # Duplicate username
        dob="2002-04-19",
        password_hash=User.set_password("password2"),
        email="alicia.brown@example.com",
        city="San Francisco",
        state="CA",
        country="USA"
    )
    
    db_session.add(user1)
    db_session.commit()
    
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()

def test_get_user_by_username(db_session):
    user = User(
        first_name="Bob",
        last_name="Marley",
        username="bobmarley",
        dob="1998-02-09",
        password_hash=User.set_password("rastafari"),
        email="bob.marley@example.com",
        city="Kingston",
        state="",
        country="Jamaica"
    )
    db_session.add(user)
    db_session.commit()

    fetched_user = db_session.query(User).filter(User.username == "bobmarley").first()
    assert fetched_user.email == "bob.marley@example.com"

def test_update_user(db_session):
    user = User(
        first_name="Charlie",
        last_name="Chaplin",
        username="charliechaplin",
        dob="1997-03-13",
        password_hash=User.set_password("funny"),
        email="charlie.chaplin@example.com",
        city="London",
        state="",
        country="UK"
    )
    db_session.add(user)
    db_session.commit()
    
    # Update user details
    user.update_user(city="Hollywood")
    db_session.commit()
    db_session.refresh(user)

    assert user.city == "Hollywood"

def test_delete_user(db_session):
    user = User(
        first_name="Diana",
        last_name="Prince",
        username="dianaprince",
        dob="1996-07-24",
        password_hash=User.set_password("wonderwoman"),
        email="diana.prince@example.com",
        city="Themyscira",
        state="",
        country="Greece"
    )
    db_session.add(user)
    db_session.commit()
    
    user_id = user.id
    db_session.delete(user)
    db_session.commit()

    deleted_user = db_session.query(User).filter(User.id == user_id).first()
    assert deleted_user is None