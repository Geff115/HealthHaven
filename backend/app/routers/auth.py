#!/usr/bin/env python3
"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from ..auth.jwt import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from ..models.user import User
from ..db.session import get_db_session
from ..logging import security_logger
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["authentication"])

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