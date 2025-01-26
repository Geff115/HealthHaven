#!/usr/bin/env python3
"""
Setting up the database engine
for postgresql
"""

import os
from dotenv import load_dotenv


# Explicit path to the .env file
dotenv_path = os.path.join(os.path.dirname(__file__), "env", ".env")
load_dotenv(dotenv_path)

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_url is not set in the .env file")