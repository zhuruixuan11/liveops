from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.deps import get_current_user
from app.models.all import AuthUser, Staff
from app.schemas.all import LoginIn, RegisterIn, TokenOut, MeOut

router = APIRouter()


@router.post("/register", response_model=MeOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    exists = db.scalar(select(AuthUser).where(AuthUser.username == payload.username))
    if exists:
        raise HTTPException(status_code=400, detail="username already exists")
    user = AuthUser(
        username=payload.username,
        password_hash=hash_password(payload.password),
        phone=payload.phone,
        role=payload.role or "CUSTOMER",
        status=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(AuthUser).where(AuthUser.username == payload.username))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="bad credentials")
    token = create_access_token(sub=str(user.user_id), role=user.role)
    return TokenOut(access_token=token)


@router.post("/refresh", response_model=TokenOut)
def refresh(current_user: dict = Depends(get_current_user)):
    token = create_access_token(sub=current_user["sub"], role=current_user.get("role"))
    return TokenOut(access_token=token)


@router.get("/me", response_model=MeOut)
def me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = int(current_user["sub"])
    user = db.scalar(select(AuthUser).where(AuthUser.user_id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    out = MeOut.model_validate(user).model_dump()
    staff = db.scalar(select(Staff).where(Staff.user_id == user_id))
    if staff:
        out["staff_id"] = staff.staff_id
        out["store_id"] = staff.store_id
    return out
