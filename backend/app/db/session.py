#!/usr/bin/env python3
"""
Database session management
"""
from contextlib import contextmanager
from ..models.base import SessionLocal

@contextmanager
def get_db_session():
    """Database session context manager"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()