#!/usr/bin/env python3
"""
User model
"""
from datetime import datetime
from .base import Base
from ..db.session import get_db_session
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Session, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(40), nullable=False, index=True)
    last_name = Column(String(40), nullable=False, index=True)
    dob = Column(String(40), nullable=False)
    username = Column(String(40), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(40), unique=True, nullable=False)
    city = Column(String(80), nullable=False, index=True)
    state = Column(String(40), nullable=False, index=True)
    country = Column(String(40), nullable=False, index=True)
    status = Column(String(20), default="active", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Defining relationship between User and Doctor, Symptom, MedicalRecord
    doctor = relationship("Doctor", back_populates='user', uselist=False, foreign_keys='Doctor.user_id')
    appointments = relationship("Appointment", back_populates='user', cascade="all, delete")
    symptoms = relationship("Symptom", back_populates='user')
    medical_records = relationship("MedicalRecord", back_populates='user')


    def __repr__(self):
        """
        String representation of the User
        """
        return f'<User {self.first_name} {self.last_name}>'

    @staticmethod
    def set_password(password):
        """
        Setting the password for a user
        """
        # Password validation
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return generate_password_hash(password)

    def check_password(self, password):
        """
        Verifying a user's password
        """
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get_user_by_username(cls, username):
        """
        Fetch a user from the database based on the username.
        It returns the user object if found, else None.
        """
        with get_db_session() as session:
            return session.query(cls).filter(cls.username == username).first()

    @classmethod
    def get_user_by_id(cls, user_id):
        """
        Getting a user from the database based on the
        user id.
        """
        with get_db_session() as session:
            return session.query(cls).filter(cls.id == user_id).first()

    @classmethod
    def get_user_by_email(cls, user_email):
        """
        Getting a user from the database based on the
        user email.
        """
        with get_db_session() as session:
            return session.query(cls).filter(cls.email == user_email).first()
    
    @classmethod
    def create_user(cls, email, password, **kwargs):
        """
        Creating a user and storing it in the
        database
        """
        if not email or not password:
            raise ValueError("email and password are required")
        if not isinstance(email, str) or not isinstance(password, str):
            raise TypeError("email and password must be strings")

        # calling set_password to hash he password
        hashed_password = cls.set_password(password)

        # Create a user instance
        user = cls(email=email, password_hash=hashed_password, **kwargs)

        # saving the user instance to the database
        with get_db_session() as session:
            session.add(user)
            session.commit()
            session.refresh(user)

        return user
    
    @property
    def age(self):
        """
        Validating the age of a user
        """
        if not self.dob:
            return None

        try:
            birth_date = datetime.strptime(self.dob, "%Y-%m-%d")
            today = datetime.today()
            return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        except ValueError:
            return None

    def update_user(self, **kwargs):
        """
        Updating a user details using keyword
        arguments for the field to update
        """
        if not kwargs:
            return {"message": "Please pass in a keyword argument"}

        updated = False
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                updated = True
            else:
                raise KeyError(f"User does not have the attribute '{key}'")

        if updated:
            return {"message": "user updated successfully"}
        return {"message": "no valid fields to update"}

    @classmethod
    def delete_user_by_id(cls, user_id):
        """
        Deleting a user by ID by fetching them from the
        database.
        """
        with get_db_session() as session:
            user = cls.get_user_by_id(user_id)
            if not user:
                return {"message": "User does not exist"}

            session.delete(user)
            session.commit()
            return {"message": "user deleted successfully"}
    
    def delete(self):
        """
        Delete a user instance from the database
        """
        with get_db_session() as session:
            session.delete(self)
            session.commit()
            return {"message": f"User {self.id} deleted successfully"}
