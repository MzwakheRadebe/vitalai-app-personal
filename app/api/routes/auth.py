from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field

from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    require_roles,
)
from app.config import get_settings
import jwt


router = APIRouter(prefix="/auth")

# Simple in-memory user store for scaffolding.
# Replace with a real database in production.
_USERS: dict[str, dict] = {}


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(default="user")


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register")
async def register(req: RegisterRequest):
    email = req.email.lower().strip()
    if email in _USERS:
        raise HTTPException(status_code=409, detail="User already exists")
    hashed = hash_password(req.password)
    _USERS[email] = {"password": hashed, "role": req.role}
    return {"status": "registered", "email": email, "role": req.role}


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    email = req.email.lower().strip()
    user = _USERS.get(email)
    if not user or not verify_password(req.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(subject=email, role=user.get("role", "user"))
    return TokenResponse(access_token=token)


def _auth_header_to_token(request: Request) -> str:
    header = request.headers.get("Authorization") or ""
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return header.split(" ", 1)[1].strip()


@router.get("/me")
async def me(request: Request):
    token = _auth_header_to_token(request)
    payload = decode_access_token(token)
    email = payload.get("sub")
    role = payload.get("role")
    return {"email": email, "role": role}


@router.get("/debug/me")
async def debug_me(request: Request):
    token = _auth_header_to_token(request)
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"], options={"verify_exp": False})
    return payload


@router.get("/users")
async def list_users(_: dict = Depends(require_roles(["admin"]))):
    # Expose the in-memory user store for debugging; admin-only.
    return {"users": [{"email": e, "role": u.get("role")} for e, u in _USERS.items()]}