from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(pw: str) -> str:
    return pwd_ctx.hash(pw)


def verify_password(pw: str, pw_hash: str) -> bool:
    return pwd_ctx.verify(pw, pw_hash)


def create_access_token(sub: str, role: Optional[str] = None, expires_delta: Optional[timedelta] = None) -> str:
    exp = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    payload = {"sub": sub, "exp": exp}
    if role:
        payload["role"] = role
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except JWTError:
        return None
