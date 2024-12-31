#!/usr/bin/env python3
"""
Authentication dependencies
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ..models.user import User
from .jwt import verify_token
from ..db.session import get_db_session


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    with get_db_session() as session:
        user = User.get_user_by_username(username)
        if user is None:
            raise credentials_exception
        return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Check if user is active"""
    if current_user.status != "active":
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user