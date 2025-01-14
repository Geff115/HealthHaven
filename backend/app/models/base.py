#!/usr/bin/env python3
"""
SQLAlchemy configuration module that provides:
- Declarative base for models
- Database engine setup with retry logic
- Session management
- Generic search functionality for models
"""
from typing import List, Optional, Type, Any
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from sqlalchemy import create_engine, or_, String, Column
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DatabaseError
from sqlalchemy.engine.base import Engine

from config import database_url

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """
    Database connection manager with retry logic
    """
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((OperationalError, DatabaseError)),
        before_sleep=lambda retry_state: logger.warning(
            f"Database connection attempt {retry_state.attempt_number} failed. Retrying..."
        )
    )
    def connect(self) -> Engine:
        """
        Establish database connection with retry logic
        """
        try:
            self.engine = create_engine(
                self.db_url,
                echo=True,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
            )
            # Test the connection
            self.engine.connect()
            logger.info("Database connection established successfully")
            return self.engine
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise

    def init_session(self) -> sessionmaker:
        """
        Initialize session maker with the engine
        """
        if not self.engine:
            self.connect()
        
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=False,
        )
        return self.SessionLocal

# Initialize database connection
db = DatabaseConnection(database_url)
try:
    engine = db.connect()
    SessionLocal = db.init_session()
except Exception as e:
    logger.error(f"Failed to initialize database: {str(e)}")
    raise

# Initialize declarative base
Base = declarative_base()

def search(cls: Type[Base], 
          keyword: str, 
          *columns: str, 
          session: Optional[Session] = None) -> List[Any]:
    """
    Generic search method for SQLAlchemy models.
    """
    use_provided_session = session is not None
    
    if not use_provided_session:
        session = SessionLocal()
    
    try:
        if not columns:
            searchable_columns = [
                c for c in cls.__table__.columns 
                if isinstance(c.type, String)
            ]
        else:
            searchable_columns = []
            for column_name in columns:
                column = getattr(cls, column_name, None)
                if not isinstance(column, Column):
                    raise ValueError(f"Invalid column name: {column_name}")
                searchable_columns.append(column)

        conditions = [
            column.ilike(f"%{keyword}%") 
            for column in searchable_columns
        ]
        
        return session.query(cls).filter(or_(*conditions)).all()

    except SQLAlchemyError as e:
        session.rollback()
        raise RuntimeError(f"Database error during search: {str(e)}") from e
    
    finally:
        if not use_provided_session:
            session.close()

# Attach search method to Base
Base.search = classmethod(search)