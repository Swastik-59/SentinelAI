"""
SentinelAI — Authentication & RBAC Service

Role hierarchy:
- analyst  : Can view cases, add notes, run analyses
- reviewer : Can resolve/close cases, manage assignments
- admin    : Full access including delete logs, manage users

JWT-based stateless auth with bcrypt password hashing.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.database import get_user_by_username, get_user_by_id

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SENTINEL_JWT_SECRET", "sentinel-dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("SENTINEL_TOKEN_EXPIRY", "480"))  # 8 hours

# ── Password Hashing ──────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT Token ──────────────────────────────────────────────────────────────
def create_access_token(user_id: str, username: str, role: str) -> str:
    """Create a signed JWT with user claims."""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT. Raises on invalid/expired."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── FastAPI Dependencies ──────────────────────────────────────────────────
security = HTTPBearer(auto_error=False)

ROLE_HIERARCHY = {"admin": 3, "reviewer": 2, "analyst": 1}


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[Dict[str, Any]]:
    """
    Extract current user from Bearer token.
    Returns None if no token provided (allows optional auth).
    """
    if credentials is None:
        return None
    payload = decode_token(credentials.credentials)
    user = await get_user_by_id(payload.get("sub", ""))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "full_name": user["full_name"],
    }


def require_role(minimum_role: str):
    """
    Dependency factory: require at least `minimum_role` level.

    Usage:
        @router.post("/...", dependencies=[Depends(require_role("reviewer"))])
    """
    min_level = ROLE_HIERARCHY.get(minimum_role, 0)

    async def _check(
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    ) -> Dict[str, Any]:
        payload = decode_token(credentials.credentials)
        user_role = payload.get("role", "analyst")
        user_level = ROLE_HIERARCHY.get(user_role, 0)
        if user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {minimum_role} role or higher. You have: {user_role}",
            )
        user = await get_user_by_id(payload.get("sub", ""))
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "full_name": user["full_name"],
        }

    return _check
