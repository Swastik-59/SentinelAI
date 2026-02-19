"""
SentinelAI — Authentication Router

POST /auth/login       — Authenticate and get JWT token
POST /auth/register    — Create new user account
GET  /auth/me          — Get current user profile
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional

from app.database import create_user, get_user_by_username
from app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_role,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4, max_length=128)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4, max_length=128)
    role: str = Field(default="analyst", pattern="^(analyst|reviewer|admin)$")
    full_name: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class UserProfile(BaseModel):
    id: str
    username: str
    role: str
    full_name: Optional[str]


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    user = await get_user_by_username(request.username)
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(user["id"], user["username"], user["role"])
    return TokenResponse(
        access_token=token,
        role=user["role"],
        username=user["username"],
    )


@router.post("/register", response_model=UserProfile)
async def register(request: RegisterRequest):
    """
    Register a new user. In production, restrict to admin-only.
    For hackathon demo, open registration.
    """
    existing = await get_user_by_username(request.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")

    password_hash = hash_password(request.password)
    user_id = await create_user(
        username=request.username,
        password_hash=password_hash,
        role=request.role,
        full_name=request.full_name or request.username,
    )
    return UserProfile(
        id=user_id,
        username=request.username,
        role=request.role,
        full_name=request.full_name,
    )


@router.get("/me", response_model=UserProfile)
async def me(user=Depends(require_role("analyst"))):
    """Get current authenticated user profile."""
    return UserProfile(
        id=user["id"],
        username=user["username"],
        role=user["role"],
        full_name=user["full_name"],
    )
