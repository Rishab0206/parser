import os
import hashlib
import secrets
import datetime
from typing import Optional, List
import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

security_bearer = HTTPBearer(auto_error=False)

class Role:
    ADMIN = "Admin"
    STAFF = "Staff"
    UNDERWRITER = "Admin"  # Backward compatibility
    SALES_DSA = "Staff"    # Backward compatibility

class CurrentUser:
    def __init__(self, user_id: str, email: str, name: str, role: str):
        self.user_id = user_id
        self.username = email
        self.email = email
        self.name = name
        self.role = role

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}${key.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    try:
        salt, key_hex = hashed.split('$')
        computed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return secrets.compare_digest(computed.hex(), key_hex)
    except Exception:
        return False

def create_access_token(user_id: str, email: str, name: str, role: str) -> str:
    # 8 hours expiration
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=getattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES', 480)
    )
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "role": role,
        "exp": expire
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> CurrentUser:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in."
        )
    
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email") or payload.get("username", "user")
        name = payload.get("name", email.split('@')[0])
        role = payload.get("role", Role.STAFF)
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        return CurrentUser(user_id=user_id, email=email, name=name, role=role)
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid. Please log in again.")

def require_roles(allowed_roles: List[str]):
    def role_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Action requires one of roles: {allowed_roles}"
            )
        return current_user
    return role_checker

def verify_application_access(application_id: str, current_user: CurrentUser, db) -> any:
    from app.models.models import LoanApplication
    app_obj = db.query(LoanApplication).filter(LoanApplication.id == application_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Customer application not found")
    if current_user.role != Role.ADMIN and app_obj.owner_user_id and app_obj.owner_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to access this customer record."
        )
    return app_obj
