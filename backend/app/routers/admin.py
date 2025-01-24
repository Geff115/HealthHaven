#!/usr/bin/env python3
"""
Admin routes
"""
import traceback
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from math import ceil
from datetime import datetime

from ..auth.dependencies import get_admin_user
from ..models.user import User, UserRole, UserStatus
from ..models.doctor import Doctor, DoctorStatus
from ..db.session import get_db_session
from ..logging import security_logger

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    first_name: str
    last_name: str
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        orm_mode = True

class PaginatedResponse(BaseModel):
    total: int
    total_pages: int
    page: int
    per_page: int
    users: List[UserOut]
    next_page: Optional[int]
    prev_page: Optional[int]

class DoctorRequestDetails(BaseModel):
    id: int
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    created_at: datetime
    credentials: Optional[dict]
    specialization: Optional[str]
    license_number: Optional[str]

    class Config:
        orm_mode = True

class DoctorRequestResponse(BaseModel):
    total: int
    total_pages: int
    page: int
    per_page: int
    requests: List[DoctorRequestDetails]
    next_page: Optional[int]
    prev_page: Optional[int]

class DashboardStats(BaseModel):
    total_users: int
    role_summary: dict
    pending_doctor_requests: int
    top_pending_requests: List[dict]
    recent_activities: List[dict]

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/verify", response_model=dict)
async def verify_admin_access(admin_user: User = Depends(get_admin_user)):
    """Verify admin access"""
    return {"status": "ok", "role": str(admin_user.role)}

async def validate_user_exists(user_id: int, session) -> User:
    """Helper function to validate user existence"""
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/users", response_model=PaginatedResponse, summary="Fetch Users")
async def get_all_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, min_length=2, description="Search by username, email, or name"),
    role: Optional[str] = Query(None, description="Filter by user role"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    admin_user: User = Depends(get_admin_user),
):
    """
    Fetch all users with advanced filtering, sorting, and pagination
    """
    try:
        with get_db_session() as session:
            query = session.query(User)

            # Apply filters
            if search:
                search = f"%{search}%"
                query = query.filter(
                    (User.username.ilike(search)) |
                    (User.email.ilike(search)) |
                    (User.first_name.ilike(search)) |
                    (User.last_name.ilike(search))
                )
            
            if role and role in [r.value for r in UserRole]:
                query = query.filter(User.role == role)

            # Apply sorting
            sort_column = getattr(User, sort_by, User.created_at)
            if sort_order.lower() == "desc":
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)

            # Get total count for pagination
            total_users = query.count()
            total_pages = ceil(total_users / limit)
            current_page = (skip // limit) + 1

            # Get paginated results
            users = query.offset(skip).limit(limit).all()

            # Calculate next and previous pages
            next_page = current_page + 1 if current_page < total_pages else None
            prev_page = current_page - 1 if current_page > 1 else None

            return {
                "total": total_users,
                "total_pages": total_pages,
                "page": current_page,
                "per_page": limit,
                "users": users,
                "next_page": next_page,
                "prev_page": prev_page,
            }
    except Exception as e:
        security_logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    new_role: str,
    admin_user: User = Depends(get_admin_user),
):
    """Update a user's role with additional validation and logging"""
    valid_roles = [role.value for role in UserRole]
    if new_role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role: {new_role}. Valid roles: {valid_roles}"
        )

    try:
        with get_db_session() as session:
            user = await validate_user_exists(user_id, session)
            
            # Prevent admin from modifying their own role
            if user.id == admin_user.id:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot modify your own role"
                )

            old_role = user.role
            user.role = new_role
            user.updated_at = datetime.utcnow()
            session.commit()

            security_logger.info(
                f"User role updated | User: {user.username} | "
                f"Old role: {old_role} | New role: {new_role} | "
                f"Updated by: {admin_user.username}"
            )

            return JSONResponse(
                content={
                    "message": f"Role updated to {new_role} for user {user.username}",
                    "old_role": old_role,
                    "new_role": new_role
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        security_logger.error(f"Error updating user role: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update role")


@router.get("/doctor-requests", response_model=DoctorRequestResponse)
async def get_doctor_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: str = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    admin_user: User = Depends(get_admin_user),
):
    try:
        with get_db_session() as session:
            query = session.query(User)

            # Apply status filter using correct enum values
            if status == "pending":
                query = query.filter(User.role == UserRole.DOCTOR_PENDING)
            elif status == "approved":
                query = query.filter(User.role == UserRole.DOCTOR)
            else:
                # Default to showing pending requests
                query = query.filter(User.role == UserRole.DOCTOR_PENDING)

            # Apply sorting
            sort_column = getattr(User, sort_by, User.created_at)
            if sort_order.lower() == "desc":
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)

            total_requests = query.count()
            total_pages = ceil(total_requests / limit)
            current_page = (skip // limit) + 1

            users = query.offset(skip).limit(limit).all()

            return {
                "total": total_requests,
                "total_pages": total_pages,
                "page": current_page,
                "per_page": limit,
                "requests": [{
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "created_at": user.created_at,
                    "credentials": None,  # We'll add this back once basic query works
                    "role": user.role.value
                } for user in users],
                "next_page": current_page + 1 if current_page < total_pages else None,
                "prev_page": current_page - 1 if current_page > 1 else None
            }
    except Exception as e:
        security_logger.error(f"Error fetching doctor requests: {str(e)}")
        security_logger.error(f"Error type: {type(e)}")
        security_logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to fetch doctor requests")

@router.put("/doctor-requests/{user_id}/approve")
async def approve_doctor_request(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    approval_notes: Optional[str] = None
):
    """
    Approve a doctor request with optional approval notes
    """
    try:
        with get_db_session() as session:
            user = await validate_user_exists(user_id, session)
            
            if user.role != UserRole.DOCTOR_PENDING:
                raise HTTPException(
                    status_code=400,
                    detail="Can only approve pending doctor requests"
                )

            user.role = UserRole.DOCTOR
            doctor.status = DoctorStatus.APPROVED
            doctor.approved_by = admin_user.id
            doctor.approved_at = datetime.utcnow()

            if approval_notes:
                user.approval_notes = approval_notes

            session.commit()

            # Log the approval
            security_logger.info(
                f"Doctor request approved | User: {user.username} | "
                f"Approved by: {admin_user.username} | "
                f"Notes: {approval_notes or 'None'}"
            )

            return JSONResponse(
                content={
                    "message": f"Doctor request approved for user {user.username}",
                    "approval_date": user.approval_date.isoformat(),
                    "approved_by": admin_user.username
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving doctor request: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to approve doctor request")

@router.put("/doctor-requests/{user_id}/reject")
async def reject_doctor_request(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    rejection_reason: str = Query(..., min_length=10, description="Reason for rejection")
):
    """
    Reject a doctor request with a mandatory rejection reason
    """
    try:
        with get_db_session() as session:
            user = await validate_user_exists(user_id, session)
            
            if user.role != UserRole.DOCTOR_PENDING:
                raise HTTPException(
                    status_code=400,
                    detail="Can only reject pending doctor requests"
                )

            user.role = UserRole.USER
            user.previous_role = UserRole.DOCTOR_PENDING
            user.rejection_date = datetime.utcnow()
            user.rejected_by = admin_user.id
            user.rejection_reason = rejection_reason

            session.commit()

            # Log the rejection
            security_logger.info(
                f"Doctor request rejected | User: {user.username} | "
                f"Rejected by: {admin_user.username} | "
                f"Reason: {rejection_reason}"
            )

            return JSONResponse(
                content={
                    "message": f"Doctor request rejected for user {user.username}",
                    "rejection_date": user.rejection_date.isoformat(),
                    "rejected_by": admin_user.username,
                    "reason": rejection_reason
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        security_logger.error(f"Error rejecting doctor request: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reject doctor request")

@router.get("/dashboard", response_model=DashboardStats)
async def get_admin_dashboard(
    admin_user: User = Depends(get_admin_user),
    days: int = Query(30, ge=1, le=365)
):
    try:
        with get_db_session() as session:
            # Basic stats
            total_users = session.query(User).count()

            # Role distribution
            role_counts = (
                session.query(User.role, func.count(User.role))
                .group_by(User.role)
                .all()
            )
            role_summary = {role.value: count for role, count in role_counts}

            # Pending doctor requests using the correct enum value
            pending_count = (
                session.query(func.count(User.id))
                .filter(User.role == UserRole.DOCTOR_PENDING)
                .scalar() or 0
            )

            # Recent pending requests
            recent_pending = (
                session.query(User)
                .filter(User.role == UserRole.DOCTOR_PENDING)
                .order_by(User.created_at.desc())
                .limit(5)
                .all()
            )

            return {
                "total_users": total_users,
                "role_summary": role_summary,
                "pending_doctor_requests": pending_count,
                "top_pending_requests": [
                    {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "created_at": user.created_at,
                        "first_name": user.first_name,
                        "last_name": user.last_name
                    }
                    for user in recent_pending
                ],
                "recent_activities": []
            }

    except Exception as e:
        security_logger.error(f"Error fetching dashboard data: {str(e)}")
        security_logger.error(f"Error type: {type(e)}")
        security_logger.error(f"Error traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard data")