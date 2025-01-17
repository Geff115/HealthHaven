#!/usr/bin/env python3
"""
Authentication routes
"""
import secrets
import aioredis
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi_limiter.depends import RateLimiter
from datetime import datetime, timedelta
from ..auth.jwt import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, verify_token
from ..auth.dependencies import get_current_active_user
from ..models.user import User
from ..db.session import get_db_session
from ..db.redis import redis
from ..logging import security_logger
from pydantic import BaseModel, EmailStr
from ..email.sender import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    dob: str
    city: str
    state: str
    country: str


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint"""
    with get_db_session() as session:
        user = User.get_user_by_username(form_data.username)
        if not user or not user.check_password(form_data.password):
            security_logger.warning(f"Failed login attempt for username: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        security_logger.info(f"User {form_data.username} logged in successfully")
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register")
async def register(user_data: UserCreate):
    """Register new user with validated data"""
    with get_db_session() as session:
        try:
            # Add password strength validation
            if len(user_data.password) < 8:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password must be at least 8 characters long"
                )

            if User.get_user_by_username(user_data.username):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )
            if User.get_user_by_email(user_data.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )

            user = User.create_user(**user_data.dict())
            security_logger.info(f"New user registered: {user.username}")
            return {"message": "User created successfully", "user_id": user.id}

        except HTTPException as he:
            raise he
        except Exception as e:
            security_logger.error(f"Error during user registration: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

@router.post("/logout")
async def logout():
    """Logout endpoint - We'll just return a success message since the actual token 
    invalidation will be handled on the frontend"""
    return {"message": "Successfully logged out"}

@router.post("/request-password-reset")
async def request_password_reset(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks
):
    """Request a password reset"""
    try:
        with get_db_session() as session:
            user = User.get_user_by_email(request.email)
            if not user:
                security_logger.info(f"Password reset requested for non-existent email: {request.email}")
                return {"message": "If the email exists, a password reset link will be sent"}

            token = secrets.token_urlsafe(32)

            try:
                await redis.setex(f"password_reset_token:{token}", 3600, request.email)
            except Exception as redis_error:
                security_logger.error(f"Redis error during password reset: {str(redis_error)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error processing request"
                )

            reset_link = f"http://localhost:8000/reset-password.html?token={token}"

            # Simplified background task function
            async def send_email_background():
                try:
                    await send_password_reset_email(request.email, reset_link)
                except Exception as email_error:
                    security_logger.error(f"Failed to send password reset email to {request.email}: {str(email_error)}")
                    await redis.delete(f"password_reset_token:{token}")
                    # Don't raise here, as it's in a background task
                    return

            background_tasks.add_task(send_email_background)

            security_logger.info(f"Password reset process initiated for user: {user.username}")
            return {"message": "If the email exists, a password reset link will be sent"}

    except Exception as e:
        security_logger.error(f"Error in password reset request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing request"
        )

@router.get("/verify-reset-token/{token}")
async def verify_reset_token(token: str):
    """Verify if the reset token is valid"""
    try:
        email = await redis.get(f"password_reset_token:{token}")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        return {"valid": True}
    except Exception as e:
        security_logger.error(f"Error verifying reset token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset):
    """Reset password using token"""
    # Fetch token from Redis
    email = await redis.get(f"password_reset_token:{reset_data.token}")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    with get_db_session() as session:
        user = User.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )

        # Update user password
        user.update_user(password_hash=reset_data.new_password)
        session.commit()

        # Remove the token from Redis
        await redis.delete(f"password_reset_token:{reset_data.token}")

    return {"message": "Password successfully reset"}


@router.post("/refresh-token", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def refresh_token(token: str = Depends(oauth2_scheme)):
    """
    Refresh access token endpoint
    Validates the provided token and refreshes it if it's about to expire.
    Limited to 5 requests per minute per user.
    """
    try:
        # Verify the provided token
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        # Check token expiration
        exp = datetime.fromtimestamp(payload.get("exp"))
        time_until_expire = exp - datetime.utcnow()

        # If the token is valid and has more than 5 minutes remaining
        if time_until_expire > timedelta(minutes=5):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token is still valid",
                headers={"X-Token-Expire-Time": str(exp)}
            )

        # Create a new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": payload.get("sub")},
            expires_delta=access_token_expires
        )
        new_expiry = datetime.utcnow() + access_token_expires

        # Log the token refresh
        security_logger.info(f"Token refreshed for user: {payload.get('sub')}")

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds()),
            "expires_at": new_expiry.isoformat()
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        security_logger.error(f"Error during token refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )