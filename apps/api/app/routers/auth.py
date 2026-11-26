from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, get_current_user, verify_password
from app.database import get_db
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.auth import LoginRequest, OwnerPasswordResetRequest, Token, UserOut
from app.services.owner_provisioning import rotate_owner_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
@limiter.limit("30/minute")
async def login_form(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    token = create_access_token(str(user.id))
    return Token(access_token=token)


@router.post("/login", response_model=Token)
@limiter.limit("30/minute")
async def login_json(
    request: Request,
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return Token(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserOut)
async def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user


@router.post("/owner/recover")
@limiter.limit("5/minute")
async def owner_password_recover(
    request: Request,
    body: OwnerPasswordResetRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """One-time owner password reset when ADMIN_SETUP_KEY is configured (not shown in UI)."""
    from app.config import get_settings

    settings = get_settings()
    key = (settings.admin_setup_key or "").strip()
    if not key or body.setup_key != key:
        raise HTTPException(status_code=401, detail="Invalid recovery request")
    if len(body.new_password) < 12:
        raise HTTPException(status_code=400, detail="Password must be at least 12 characters")
    await rotate_owner_password(db, new_password=body.new_password)
    await db.commit()
    return {"ok": True, "message": "Owner password updated. Sign in with your email and new password."}