#!/usr/bin/env python3
"""
A configuration file for pytest that allows
definition of fixtures that are accessible
across multiple test files
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..app.models.base import Base
from ..app.models.base import SessionLocal
from ..app.models import user, doctor, appointment, prescription, symptom, medical_record


# Using an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

# creating the engine
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

# creating a configured "Session" class
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Creating all tables in the test database
Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Creates a new database session for a test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="module")
def test_client():
    """
    Setting up integration test for FastAPI client.
    """
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    return client