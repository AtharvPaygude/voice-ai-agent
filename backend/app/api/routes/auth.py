"""
Authentication API routes for Aura Voice AI.

Endpoints:
  POST /api/auth/register   — Create a new account (admin or customer)
  POST /api/auth/login      — Login, receive opaque session token
  GET  /api/auth/me         — Return current user info (requires token)
  POST /api/auth/logout     — Invalidate session token
  GET  /api/auth/users      — List all users (admin only)
  PUT  /api/auth/users/{id} — Update user role / profile link (admin only)

Session tokens are opaque 32-byte random hex strings stored as SHA-256 hashes
in the database. No external JWT library is required.
"""
import secrets
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_crypto import hash_password, verify_password, hash_token
from app.db.database import get_db
from app.db.models import User, gen_id

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""
    role: str = "customer"  # "admin" | "customer"
    business_profile_id: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    business_profile_id: Optional[str]
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    token: str
    user: UserResponse


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    business_profile_id: Optional[str] = None
    is_active: Optional[bool] = None


# ---------------------------------------------------------------------------
# Helper: extract + validate session token from Authorization header
# ---------------------------------------------------------------------------

async def _get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency — resolves the bearer token to a User row."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    raw_token = authorization.removeprefix("Bearer ").strip()
    token_hash = hash_token(raw_token)
    result = await db.execute(select(User).where(User.session_token_hash == token_hash))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    return user


async def _require_admin(current_user: User = Depends(_get_current_user)) -> User:
    """Dependency: ensure logged-in user has admin role."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


# Aliases for export to other modules
get_current_user = _get_current_user
require_admin = _require_admin


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    # Validate role
    if data.role not in ("admin", "customer"):
        raise HTTPException(status_code=400, detail="role must be 'admin' or 'customer'")

    # Check duplicate email
    existing = await db.execute(select(User).where(User.email == data.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user = User(
        id=gen_id("usr"),
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        business_profile_id=data.business_profile_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return a session token."""
    result = await db.execute(select(User).where(User.email == data.email.lower()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    # Generate fresh opaque session token
    raw_token = secrets.token_hex(32)
    user.session_token_hash = hash_token(raw_token)
    user.last_login_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)

    return LoginResponse(token=raw_token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(_get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user


@router.post("/logout")
async def logout(
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Invalidate the current session token."""
    current_user.session_token_hash = None
    await db.commit()
    return {"status": "logged_out"}


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    _admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all registered users (admin only)."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    data: UpdateUserRequest,
    _admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's role, profile link, or active status (admin only)."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.role is not None:
        if data.role not in ("admin", "customer"):
            raise HTTPException(status_code=400, detail="role must be 'admin' or 'customer'")
        user.role = data.role
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.business_profile_id is not None:
        user.business_profile_id = data.business_profile_id
    if data.is_active is not None:
        user.is_active = data.is_active

    await db.commit()
    await db.refresh(user)
    return user
