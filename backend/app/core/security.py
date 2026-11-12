import datetime
from typing import Optional, List
import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.errors import UnauthorizedException, ForbiddenException

security_bearer = HTTPBearer(auto_error=False)

# Roles definition
class Role:
    ADMIN = "Admin"
    UNDERWRITER = "Underwriter"
    SALES_DSA = "Sales/DSA"
    VIEWER = "Viewer"

class CurrentUser:
    def __init__(self, user_id: str, username: str, role: str, dsa_id: Optional[str] = None):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.dsa_id = dsa_id

def create_access_token(user_id: str, username: str, role: str, dsa_id: Optional[str] = None) -> str:
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "dsa_id": dsa_id,
        "exp": expire
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> CurrentUser:
    if not credentials:
        # For development / initial access fallback to default Underwriter
        return CurrentUser(
            user_id="usr_default_underwriter",
            username="underwriter@bank.internal",
            role=Role.UNDERWRITER
        )
    
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        username = payload.get("username", "user")
        role = payload.get("role", Role.VIEWER)
        dsa_id = payload.get("dsa_id")
        if not user_id:
            raise UnauthorizedException("Invalid token payload")
        return CurrentUser(user_id=user_id, username=username, role=role, dsa_id=dsa_id)
    except jwt.PyJWTError:
        raise UnauthorizedException("Could not validate credentials")

def require_roles(allowed_roles: List[str]):
    def role_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles and current_user.role != Role.ADMIN:
            raise ForbiddenException(f"Action requires one of roles: {allowed_roles}")
        return current_user
    return role_checker

