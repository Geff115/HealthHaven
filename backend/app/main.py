#!/usr/bin/env python3
"""
Entry point of the
application
"""
import os
import redis
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from .routers import auth, users, admin, homepage
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter


app = FastAPI(title="Health Haven API")

# Get the absolute path of the frontend, static, and js directories
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__name__), "../frontend"))

# Get the absolute path of the backend to handle file upload
backend_path = os.path.abspath(os.path.join(os.path.dirname(__name__), "../backend"))

static_path = os.path.join(frontend_path, "static")
js_path = os.path.join(frontend_path, "js")
upload_path = os.path.join(backend_path, "uploads")

# mounting the js directory
app.mount("/js", StaticFiles(directory=js_path), name="js")

# mounting the static directory
app.mount("/static", StaticFiles(directory=static_path), name="static")

# mounting the uploads directory
app.mount("/uploads", StaticFiles(directory=upload_path), name="uploads")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(homepage.router)


@app.on_event("startup")
async def startup():
    redis_client = redis.asyncio.from_url("redis://localhost:6379", decode_responses=True)
    await FastAPILimiter.init(redis_client)


# serve the html files
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open(os.path.join(frontend_path, "index.html")) as f:
        return f.read()

@app.get("/login.html", response_class=HTMLResponse)
async def serve_login():
    with open(os.path.join(frontend_path, "login.html")) as f:
        return f.read()

@app.get("/signup.html", response_class=HTMLResponse)
async def serve_signup():
    with open(os.path.join(frontend_path, "signup.html")) as f:
        return f.read()

@app.get("/appointment.html", response_class=HTMLResponse)
async def serve_appointment():
    with open(os.path.join(frontend_path, "appointment.html")) as f:
        return f.read()

@app.get("/forgot-password.html", response_class=HTMLResponse)
async def serve_forgot_password():
    with open(os.path.join(frontend_path, "forgot-password.html")) as f:
        return f.read()

@app.get("/reset-password.html", response_class=HTMLResponse)
async def serve_reset_password():
    with open(os.path.join(frontend_path, "reset-password.html")) as f:
        return f.read()

@app.get("/profile.html", response_class=HTMLResponse)
async def serve_reset_password():
    with open(os.path.join(frontend_path, "profile.html")) as f:
        return f.read()

@app.get("/dashboard.html", response_class=HTMLResponse)
async def serve_reset_password():
    with open(os.path.join(frontend_path, "dashboard.html")) as f:
        return f.read()

@app.get("/service.html", response_class=HTMLResponse)
async def serve_reset_password():
    with open(os.path.join(frontend_path, "service.html")) as f:
        return f.read()


# exception handlers
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