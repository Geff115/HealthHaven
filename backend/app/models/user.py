#!/usr/bin/env python3
"""
User model
"""
from datetime import datetime
from app.models.base import Base, SessionLocal
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(40), nullable=False, index=True)
    last_name = Column(String(40), nullable=False, index=True)
    username = Column(String(40), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(40), unique=True)
    role = Column(String(40), nullable=False, index=True)
    city = Column(String(80), nullable=False, index=True)
    state = Column(String(40), nullable=False, index=True)
    country = Column(String(40), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    def __repr__(self):
        """
        String representation of the User
        """
        return f'<User {self.first_name} {self.last_name}>'

    def set_password(self, password):
        """
        Setting the password for a user
        """
        self.password_hash = generate_password_hash(password)

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
        with SessionLocal() as session:
            return session.query(cls).filter(cls.username == username).first()

    @classmethod
    def get_user_by_id(cls, user_id):
        """
        Getting a user from the database based on the
        user id.
        """
        with SessionLocal() as session:
            return session.query(cls).filter(cls.id == user_id).first()

    @classmethod
    def get_user_by_email(cls, user_email):
        """
        Getting a user from the database based on the
        user email.
        """
        with SessionLocal() as session:
            return session.query(cls).filter(cls.email == user_email).first()

    async def update_user(self, **kwargs):
        """
        Updating a user details using keyword
        arguments for the field to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                updated = True
            else:
                raise KeyError(f"User does not have the attribute '{key}'")

        if updated:
            with SessionLocal() as session:
                session.add(self)  # Add the updated
                session.commit()
                return {"message": "user updated successfully"}
        return {"message": "no valid fields to update"}

    @classmethod
    def delete_user_by_id(cls, user_id):
        """
        Deleting a user by ID by fetching them from the
        database.
        """
        with SessionLocal() as session:
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
        with SessionLocal() as session:
            session.delet(self)
            session.commit()
            return {"message": f"User {self.id} deleted successfully"}
