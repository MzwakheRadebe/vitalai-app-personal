"""Authentication routes

Handles user registration, login, and token verification.
Users are persisted in the database (PostgreSQL or SQLite).
"""

import logging

from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Optional
from pydantic import BaseModel, Field, EmailStr

from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    require_roles,
)
from app.config import get_settings
from app.doctors import DOCTOR_BY_EMAIL, STAFF_ACCESS_CODE

router = APIRouter(prefix="/auth")
logger = logging.getLogger("auth")

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: EmailStr
    # Minimum 8 chars, at least one letter and one digit (OWASP recommendation)
    password: str = Field(
        min_length=8, max_length=128,
        description="Min 8 characters with at least one letter and one digit"
    )
    role: str = Field(default="patient")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str = "patient"  # Returned so frontend can set role-based routing
    name: Optional[str] = None
    department: Optional[str] = None


class StaffLoginRequest(BaseModel):
    doctor_email: str
    access_code: str


class UserResponse(BaseModel):
    email: str
    role: str


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

async def _get_user(email: str) -> dict | None:
    """Fetch a user by email. Returns None if not found."""
    from app.db_adapter import get_db
    async with get_db() as db:
        row = await db.fetchone(
            "SELECT email, password_hash, role FROM users WHERE email = ?", (email,)
        )
        if row:
            return {"email": row[0], "password_hash": row[1], "role": row[2]}
        return None


async def _create_user(email: str, password_hash: str, role: str) -> None:
    """Insert a new user into the database."""
    from app.db_adapter import get_db
    async with get_db() as db:
        await db.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            (email, password_hash, role),
        )
        await db.commit()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(req: RegisterRequest):
    """Register a new user. Emails must be unique."""
    email = req.email.lower().strip()

    existing = await _get_user(email)
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    hashed = hash_password(req.password)
    await _create_user(email, hashed, req.role)
    return UserResponse(email=email, role=req.role)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Authenticate and return a JWT access token."""
    email = req.email.lower().strip()
    user = await _get_user(email)

    if not user or not verify_password(req.password, user["password_hash"]):
        logger.warning("Failed login attempt for email: %s", email)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    role = user.get("role", "patient")
    token = create_access_token(subject=email, role=role)
    logger.info("User logged in: %s (role=%s)", email, role)
    return TokenResponse(access_token=token, role=role)


@router.get("/me", response_model=UserResponse)
async def me(request: Request):
    """Return the currently authenticated user's info."""
    header = request.headers.get("Authorization") or ""
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = header.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    return UserResponse(email=payload.get("sub"), role=payload.get("role", "patient"))


@router.get("/users", response_model=list[UserResponse])
async def list_users(_: dict = Depends(require_roles(["admin"]))):
    """List all registered users. Admin only."""
    from app.db_adapter import get_db
    async with get_db() as db:
        rows = await db.fetchall(
            "SELECT email, role FROM users ORDER BY email", ()
        )
    # rows are tuples: (email, role)  [index 0 and 1]
    return [{"email": r[0], "role": r[1]} for r in rows]


@router.post("/staff-login", response_model=TokenResponse)
async def staff_login(req: StaffLoginRequest):
    """
    Staff login using doctor selection + universal access code.
    No personal password needed — doctors pick their name and enter the shared code.
    """
    if req.access_code != STAFF_ACCESS_CODE:
        raise HTTPException(status_code=401, detail="Invalid staff access code")

    doctor = DOCTOR_BY_EMAIL.get(req.doctor_email.lower().strip())
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    token = create_access_token(subject=doctor["email"], role="staff")
    logger.info("Staff login: %s (%s)", doctor["name"], doctor["department"])
    return TokenResponse(
        access_token=token,
        role="staff",
        name=doctor["name"],
        department=doctor["department"],
    )
