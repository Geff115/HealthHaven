#!/usr/bin/env python3
"""
Initializing the SQLAlchemy declarative base for
the models, and setting up the async engine and
sessionmaker for database connections
"""
from config import database_url
from sqlalchemy import create_engine, or_, String
from sqlalchemy.orm import declarative_base, sessionmaker
from ..db.session import get_db_session


# Setting up SQLAlchemy dclarative base
Base = declarative_base()

# Setting up the engine
engine = create_engine(
    database_url,
    echo=True,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Setting up a synchronous session
SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    auto_flush=False,
)


def search(cls: Type[Base], 
          keyword: str, 
          *columns: str, 
          session: Optional[Session] = None) -> List[Any]:
    """
    Generic search method for SQLAlchemy models.
    
    Args:
        cls: The model class to search
        keyword: Search term to find in specified columns
        *columns: Column names to search. If none provided, searches all string columns
        session: Optional existing database session
        
    Returns:
        List of matching model instances
        
    Examples:
        # Search specific columns
        User.search("john", "name", "email")
        
        # Search all string columns
        User.search("john")
        
        # Search with existing session
        with get_db_session() as session:
            User.search("john", session=session)
    """
    use_provided_session = session is not None
    
    if not use_provided_session:
        session = SessionLocal()
    
    try:
        if not columns:
            # Search all string columns if none specified
            searchable_columns = [
                c for c in cls.__table__.columns 
                if isinstance(c.type, String)
            ]
        else:
            # Validate and get specified columns
            searchable_columns = []
            for column_name in columns:
                column = getattr(cls, column_name, None)
                if not isinstance(column, Column):
                    raise ValueError(f"Invalid column name: {column_name}")
                searchable_columns.append(column)

        # Build search conditions
        conditions = [
            column.ilike(f"%{keyword}%") 
            for column in searchable_columns
        ]
        
        # Execute search query
        return session.query(cls).filter(or_(*conditions)).all()

    except SQLAlchemyError as e:
        session.rollback()
        raise RuntimeError(f"Database error during search: {str(e)}") from e
    
    finally:
        if not use_provided_session:
            session.close()

# Attach search method to Base
Base.search = classmethod(search)