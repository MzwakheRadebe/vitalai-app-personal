"""Authentication routes

Handles user registration, login, and token verification.
Users are persisted in the database (PostgreSQL or SQLite).
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field, EmailStr

from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    require_roles,
)
from app.config import get_settings


router = APIRouter(prefix="/auth")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(default="patient")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    email: str
    role: str


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

async def _get_user(email: str) -> dict | None:
    """Fetch a user by email. Returns None if not found."""
    settings = get_settings()

    if settings.database_url:
        import asyncpg
        conn = await asyncpg.connect(settings.database_url)
        row = await conn.fetchrow(
            "SELECT email, password_hash, role FROM users WHERE email = $1", email
        )
        await conn.close()
        if row:
            return dict(row)
        return None
    else:
        import aiosqlite
        async with aiosqlite.connect(settings.sqlite_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT email, password_hash, role FROM users WHERE email = ?", (email,)
            ) as cur:
                row = await cur.fetchone()
                if row:
                    return dict(row)
                return None


async def _create_user(email: str, password_hash: str, role: str) -> None:
    """Insert a new user into the database."""
    settings = get_settings()

    if settings.database_url:
        import asyncpg
        conn = await asyncpg.connect(settings.database_url)
        try:
            await conn.execute(
                "INSERT INTO users (email, password_hash, role) VALUES ($1, $2, $3)",
                email, password_hash, role,
            )
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect(settings.sqlite_path) as db:
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
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(subject=email, role=user.get("role", "patient"))
    return TokenResponse(access_token=token)


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
    settings = get_settings()

    if settings.database_url:
        import asyncpg
        conn = await asyncpg.connect(settings.database_url)
        rows = await conn.fetch("SELECT email, role FROM users ORDER BY email")
        await conn.close()
        return [{"email": r["email"], "role": r["role"]} for r in rows]
    else:
        import aiosqlite
        async with aiosqlite.connect(settings.sqlite_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT email, role FROM users ORDER BY email") as cur:
                rows = await cur.fetchall()
                return [{"email": r["email"], "role": r["role"]} for r in rows]
