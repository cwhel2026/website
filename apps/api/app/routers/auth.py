import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    clear_session_cookies,
    create_access_token,
    get_current_user,
    set_session_cookies,
    verify_password_or_dummy,
)
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.rate_limit import limiter
from app.security.startup import FACTORY_DEFAULT_PASSWORDS
from app.schemas.auth import LoginRequest, OwnerPasswordResetRequest, SessionOut, Token, UserOut
from app.services.owner_provisioning import rotate_owner_password

router = APIRouter(prefix="/auth", tags=["auth"])


async def _authenticate(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not verify_password_or_dummy(password, user):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    if get_settings().environment.lower() == "production" and password in FACTORY_DEFAULT_PASSWORDS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The factory default password is disabled in production. "
            "Set DEFAULT_ADMIN_PASSWORD in Railway and redeploy, then sign in with the new password.",
        )
    return user


@router.post("/token", response_model=Token)
@limiter.limit("30/minute")
async def login_form(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """Bearer token for scripts and API clients. Browsers use /auth/login (cookie session)."""
    user = await _authenticate(db, form_data.username, form_data.password)
    return Token(access_token=create_access_token(str(user.id)))


@router.post("/login", response_model=SessionOut)
@limiter.limit("30/minute")
async def login_json(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionOut:
    """Browser sign-in: sets an HttpOnly session cookie plus a CSRF cookie. No token in the body."""
    user = await _authenticate(db, body.email, body.password)
    set_session_cookies(response, str(user.id))
    return SessionOut(ok=True, user=UserOut.model_validate(user, from_attributes=True))


@router.post("/logout")
async def logout(response: Response) -> dict:
    clear_session_cookies(response)
    return {"ok": True}


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
    if not key or not hmac.compare_digest(body.setup_key.encode(), key.encode()):
        raise HTTPException(status_code=401, detail="Invalid recovery request")
    if len(body.new_password) < 12:
        raise HTTPException(status_code=400, detail="Password must be at least 12 characters")
    await rotate_owner_password(db, new_password=body.new_password)
    await db.commit()
    return {"ok": True, "message": "Owner password updated. Sign in with your email and new password."}
