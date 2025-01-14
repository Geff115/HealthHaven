#!/usr/bin/env python3
"""
Database session management
"""
from contextlib import contextmanager
import time
import logging
from typing import Generator

from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_session_maker():
    """
    Import SessionLocal here to avoid circular imports
    """
    from models.base import SessionLocal
    return SessionLocal

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions with retry logic.
    
    Usage:
        with get_db_session() as session:
            session.query(Model).all()
    
    Yields:
        SQLAlchemy Session object
    """
    SessionLocal = get_session_maker()
    max_retries = 3
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        session = SessionLocal()
        try:
            yield session
            session.commit()
            break
        except OperationalError as e:
            session.rollback()
            if attempt == max_retries - 1:
                logger.error(f"Max retries reached. Database operation failed: {str(e)}")
                raise
            logger.warning(f"Database operation failed, attempt {attempt + 1} of {max_retries}")
            time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()