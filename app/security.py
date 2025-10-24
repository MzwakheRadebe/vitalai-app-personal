import datetime
import hashlib
import secrets
from typing import Dict, Any

import jwt
from fastapi import HTTPException, Request, Depends

from app.config import get_settings


def _pbkdf2_hash(password: str, salt_hex: str, iterations: int = 120_000) -> str:
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return dk.hex()


def hash_password(password: str) -> str:
    iterations = 120_000
    salt_hex = secrets.token_hex(16)
    hash_hex = _pbkdf2_hash(password, salt_hex, iterations)
    return f"pbkdf2_sha256${iterations}${salt_hex}${hash_hex}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        algo, iters_str, salt_hex, hash_hex = hashed.split("$")
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iters_str)
        calc = _pbkdf2_hash(password, salt_hex, iterations)
        return secrets.compare_digest(calc, hash_hex)
    except Exception:
        return False


def create_access_token(subject: str, role: str = "user", expires_minutes: int = 60) -> str:
    settings = get_settings()
    now = datetime.datetime.now(datetime.timezone.utc)
    exp = now + datetime.timedelta(minutes=expires_minutes)
    payload: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": exp,
        "iss": settings.app_name,
    }
    try:
        return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create access token")


def decode_access_token(token: str) -> Dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_bearer_token(request: Request) -> str:
    header = request.headers.get("Authorization") or ""
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return header.split(" ", 1)[1].strip()


def get_current_user(request: Request) -> Dict[str, Any]:
    token = get_bearer_token(request)
    return decode_access_token(token)


def require_roles(roles: list[str]):
    def dependency(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        role = user.get("role")
        if role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return dependency