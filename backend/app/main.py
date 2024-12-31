#!/usr/bin/env python3
"""
Entry point of the
application
"""
from fastapi import FastAPI
from .routers import auth, users  # Import your routers

app = FastAPI(title="Health Haven API")

# Include routers
app.include_router(auth.router)
app.include_router(users.router)