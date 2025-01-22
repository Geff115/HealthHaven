#!/usr/bin/env python3
"""
Admin routes
"""
from fastapi import APIRouter, Depends, HTTPException
from ..auth.dependencies import get_admin_user
from ..models.user import User, UserRole, UserStatus
from ..db.session import get_db_session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from pydantic import BaseModel
from fastapi import Query
from math import ceil
from fastapi.responses import JSONResponse


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    first_name: str
    last_name: str

    class Config:
        orm_mode = True


class PaginatedResponse(BaseModel):
    total: int
    total_pages: int
    page: int
    per_page: int
    users: List[UserOut]


router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users", response_model=PaginatedResponse, summary="Fetch Users", description="Fetch all users with pagination")
async def get_all_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    search: str = Query(None, description="Search by username or email"),
    admin_user: User = Depends(get_admin_user),
):
    """Fetch all users with pagination and metadata"""
    with get_db_session() as session:
        query = session.query(User)
        if search:
            query = query.filter(User.username.ilike(f"%{search}%") | User.email.ilike(f"%{search}%"))
        total_users = query.count()
        total_pages = ceil(total_users / limit)
        users = query.offset(skip).limit(limit).all()
        return {
            "total": total_users,
            "total_pages": total_pages,
            "page": (skip // limit) + 1,
            "per_page": limit,
            "users": users,
        }


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    new_role: str,
    admin_user: User = Depends(get_admin_user),
):
    """Update a user's role"""
    valid_roles = [role.value for role in UserRole]
    if new_role not in valid_roles:
        raise HTTPException(
            status_code=400, detail=f"Invalid role: {new_role}. Valid roles: {valid_roles}"
        )
    with get_db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        try:
            user.role = new_role
            session.commit()
            return JSONResponse(
                content={
                    "message": f"Role updated to {new_role} for user {user.username}"
                }
            )
        except SQLAlchemyError:
            session.rollback()
            raise HTTPException(
                status_code=500, detail="Failed to update role"
            )

@router.get("/doctor-requests", response_model=PaginatedResponse)
async def get_doctor_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    admin_user: User = Depends(get_admin_user),
):
    """Fetch all pending doctor requests with pagination"""
    with get_db_session() as session:
        query = session.query(User).filter(User.role == UserRole.DOCTOR_PENDING)
        total_requests = query.count()
        total_pages = ceil(total_requests / limit)
        pending_doctors = query.offset(skip).limit(limit).all()
        return {
            "total": total_requests,
            "total_pages": total_pages,
            "page": (skip // limit) + 1,
            "per_page": limit,
            "users": pending_doctors,
        }

@router.put("/doctor-requests/{user_id}/approve")
async def approve_doctor_request(user_id: int, admin_user: User = Depends(get_admin_user)):
    """Approve a doctor request"""
    with get_db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user or user.role != UserRole.DOCTOR_PENDING:
            raise HTTPException(status_code=404, detail="Doctor request not found")
        try:
            user.role = UserRole.DOCTOR
            session.commit()
            return {"message": f"Doctor request approved for user {user.username}"}
        except SQLAlchemyError:
            session.rollback()
            raise HTTPException(status_code=500, detail="Failed to approve doctor request")

@router.put("/doctor-requests/{user_id}/reject")
async def reject_doctor_request(user_id: int, admin_user: User = Depends(get_admin_user)):
    """Reject a doctor request"""
    with get_db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user or user.role != UserRole.DOCTOR_PENDING:
            raise HTTPException(status_code=404, detail="Doctor request not found")
        try:
            user.role = UserRole.USER
            session.commit()
            return {"message": f"Doctor request rejected for user {user.username}"}
        except SQLAlchemyError:
            session.rollback()
            raise HTTPException(status_code=500, detail="Failed to reject doctor request")