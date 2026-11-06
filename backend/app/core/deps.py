import time
import uuid
from contextvars import ContextVar
from typing import Optional

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_token

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if credentials:
            payload = decode_token(credentials.credentials)
            if not payload:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
            request.state.user = payload
            return credentials
        return None


def get_current_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if user:
        return user
    # 兜底：直接从 Authorization header 解码
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        payload = decode_token(auth[7:])
        if payload:
            return payload
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated")


def require_role(*roles: str):
    def _check(request: Request):
        user = get_current_user(request)
        if user.get("role") not in roles and user.get("role") != "ADMIN":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="permission denied")
        return user
    return _check


def gen_request_id() -> str:
    return f"{int(time.time()*1000)}-{uuid.uuid4().hex[:8]}"
