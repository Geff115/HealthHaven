#!/usr/bin/env python3
"""
Entry point of the
application
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from .routers import auth, users, admin, homepage
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="Health Haven API")

# Determine the absolute path to the frontend directory
frontend_path = os.path.abspath(
    os.path.join(os.path.dirname(__name__), "../frontend")
)

# Determine the path to the index.html file in the frontend directory
index_path = os.path.join(frontend_path, "index.html")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from the "frontend" directory
static_path = os.path.join(frontend_path, "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Determine the absolute path to the "js" directory inside "frontend"
js_path = os.path.join(frontend_path, "js")

# Mount the "js" directory
app.mount("/js", StaticFiles(directory=js_path), name="js")

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(homepage.router)


@app.get("/")
async def serve_homepage():
    """Serve the homepage."""
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"detail": "Frontend index.html file not found"}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors."""
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all unhandled exceptions."""
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred. Please try again later."},
    )