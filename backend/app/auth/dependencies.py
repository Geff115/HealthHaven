#!/usr/bin/env python3
"""
Authentication dependencies
"""
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ..models.user import User, UserRole, UserStatus
from .jwt import verify_token
from ..db.session import get_db_session


logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current authenticated user"""
    logger = logging.getLogger(__name__)
    logger.info(f"Verifying token: {token[:20]}...")  # Log first 20 chars of token for debugging

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_token(token)
        if payload is None:
            logger.warning("Token verification failed")
            raise credentials_exception

        username: str = payload.get("sub")
        if username is None:
            logger.warning("Username not found in token")
            raise credentials_exception

        with get_db_session() as session:
            user = User.get_user_by_username(username)
            if user is None:
                logger.warning(f"User {username} not found in database")
                raise credentials_exception
            logger.info(f"User authenticated: {username}, Role: {user.role}")
            return user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise credentials_exception

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
):
    """Check if user is active"""
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_admin_user(current_user: User = Depends(get_current_active_user)):
    """Verify admin access using UserRole enum"""
    logger.info(f"Checking admin access for user: {current_user.username}, Role: {current_user.role}")
    
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"Admin access denied for user: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user