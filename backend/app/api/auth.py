import secrets
import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import User, Invite, LoanApplication
from app.core.security import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_roles, CurrentUser, Role
)

router = APIRouter(prefix="/api", tags=["Auth & Admin Control"])

class LoginRequest(BaseModel):
    email: str
    password: str

class InviteCreateRequest(BaseModel):
    name: str
    email: str
    role: str = "Staff"

class AcceptInviteRequest(BaseModel):
    token: str
    password: str

# 1. Login endpoint (Public)
@router.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated. Please contact administrator."
        )

    token = create_access_token(user.id, user.email, user.name, user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role
        }
    }

# 2. Current User Profile
@router.get("/auth/me")
def get_me(current_user: CurrentUser = Depends(get_current_user)):
    return {
        "id": current_user.user_id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role
    }

# 3. Create Staff Invite (Admin Only)
@router.post("/admin/invites")
def create_invite(
    req: InviteCreateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles([Role.ADMIN]))
):
    email = req.email.strip().lower()

    # Check if user already exists
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail=f"User with email {email} already exists.")

    # Max 5 Staff Members enforcement
    active_staff_count = db.query(User).filter(User.role == Role.STAFF).count()
    now = datetime.datetime.utcnow()
    pending_invites_count = db.query(Invite).filter(
        Invite.is_used == False,
        Invite.expires_at > now
    ).count()

    if active_staff_count + pending_invites_count >= 5:
        raise HTTPException(
            status_code=400,
            detail="Maximum limit of 5 staff members reached. Please remove an existing staff member to invite a new one."
        )

    # 24-hour expiration
    token = secrets.token_urlsafe(32)
    expires_at = now + datetime.timedelta(hours=24)

    invite = Invite(
        token=token,
        email=email,
        name=req.name.strip(),
        role=Role.STAFF,
        created_by_user_id=current_user.user_id,
        expires_at=expires_at,
        is_used=False
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    return {
        "id": invite.id,
        "token": invite.token,
        "email": invite.email,
        "name": invite.name,
        "role": invite.role,
        "expires_at": invite.expires_at.isoformat()
    }

# 4. List Invites (Admin Only)
@router.get("/admin/invites")
def list_invites(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles([Role.ADMIN]))
):
    invites = db.query(Invite).order_by(Invite.created_at.desc()).all()
    now = datetime.datetime.utcnow()
    results = []
    for inv in invites:
        is_expired = inv.expires_at < now
        status_str = "ACCEPTED" if inv.is_used else ("EXPIRED" if is_expired else "PENDING")
        results.append({
            "id": inv.id,
            "token": inv.token,
            "email": inv.email,
            "name": inv.name,
            "role": inv.role,
            "status": status_str,
            "is_used": inv.is_used,
            "expires_at": inv.expires_at.isoformat(),
            "created_at": inv.created_at.isoformat()
        })
    return results

# 5. List Users (Admin Only)
@router.get("/admin/users")
def list_users(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles([Role.ADMIN]))
):
    users = db.query(User).order_by(User.created_at.asc()).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "role": u.role,
            "is_active": u.is_active,
            "customers_count": len(u.applications),
            "created_at": u.created_at.isoformat()
        } for u in users
    ]

# 6. Delete/Deactivate Staff (Admin Only)
@router.delete("/admin/users/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles([Role.ADMIN]))
):
    if user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    db.delete(user)
    db.commit()
    return {"message": f"User {user.email} removed successfully."}

# 7. Check Invite Details (Public for Staff using invite link)
@router.get("/auth/invite/{token}")
def get_invite_details(token: str, db: Session = Depends(get_db)):
    invite = db.query(Invite).filter(Invite.token == token).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid invite link.")
    if invite.is_used:
        raise HTTPException(status_code=400, detail="This invite link has already been used. Please log in.")
    if invite.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="This invite link has expired (24-hour limit). Contact Admin for a new invite.")
    
    return {
        "email": invite.email,
        "name": invite.name,
        "role": invite.role,
        "expires_at": invite.expires_at.isoformat()
    }

# 8. Accept Invite & Set Password (Public)
@router.post("/auth/accept-invite")
def accept_invite(req: AcceptInviteRequest, db: Session = Depends(get_db)):
    invite = db.query(Invite).filter(Invite.token == req.token).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid invite token.")
    if invite.is_used:
        raise HTTPException(status_code=400, detail="This invite has already been used.")
    if invite.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite link has expired.")

    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")

    # Check if user with email already created
    existing = db.query(User).filter(User.email == invite.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    new_user = User(
        email=invite.email,
        name=invite.name,
        hashed_password=hash_password(req.password),
        role=invite.role,
        is_active=True
    )
    db.add(new_user)
    db.flush()

    # Mark invite used
    invite.is_used = True
    invite.used_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(new_user)

    # Return access token
    token = create_access_token(new_user.id, new_user.email, new_user.name, new_user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.name,
            "role": new_user.role
        }
    }

