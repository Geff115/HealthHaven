#!/usr/bin/env python3
"""
Initializing the SQLAlchemy declarative base for
the models, and setting up the async engine and
sessionmaker for database connections
"""
from config import database_url
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# Setting up SQLAlchemy dclarative base
Base = declarative_base()

# Setting up the engine
engine = create_async_engine(database_url, echo=True)

# Setting up an asynchronous session
async_session = sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)
