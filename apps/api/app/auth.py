import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

import bcrypt
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User, UserRole

# auto_error=False: browser sessions authenticate with the HttpOnly cookie instead.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

settings = get_settings()

SESSION_COOKIE = "sc_session"
CSRF_COOKIE = "sc_csrf"
CSRF_HEADER = "X-CSRF-Token"
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

ADMIN_ROLES = frozenset({UserRole.OWNER, UserRole.ADMIN})
FINANCE_ROLES = ADMIN_ROLES | {UserRole.ACCOUNTANT}
READ_ONLY_ROLES = frozenset({UserRole.AUDITOR})

# Equalises response time for unknown accounts so login cannot enumerate emails.
_DUMMY_HASH = bcrypt.hashpw(b"timing-equaliser", bcrypt.gensalt()).decode()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def verify_password_or_dummy(plain: str, user: User | None) -> bool:
    if user is None:
        verify_password(plain, _DUMMY_HASH)
        return False
    return verify_password(plain, user.password_hash)


def create_access_token(subject: str, *, csrf: str | None = None) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict = {"sub": subject, "exp": expire}
    if csrf:
        payload["csrf"] = csrf
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _cookie_secure() -> bool:
    return settings.environment.lower() in ("production", "staging")


def set_session_cookies(response: Response, user_id: str) -> None:
    csrf = secrets.token_urlsafe(32)
    token = create_access_token(user_id, csrf=csrf)
    max_age = settings.access_token_expire_minutes * 60
    secure = _cookie_secure()
    response.set_cookie(
        SESSION_COOKIE, token, max_age=max_age, httponly=True, secure=secure, samesite="lax", path="/"
    )
    # Readable by the portal's JavaScript so it can echo it in the CSRF header.
    response.set_cookie(
        CSRF_COOKIE, csrf, max_age=max_age, httponly=False, secure=secure, samesite="lax", path="/"
    )


def clear_session_cookies(response: Response) -> None:
    for name in (SESSION_COOKIE, CSRF_COOKIE):
        response.delete_cookie(name, path="/", secure=_cookie_secure(), samesite="lax")


async def get_current_user(
    request: Request,
    bearer: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    from_cookie = False
    token = bearer
    if not token:
        token = request.cookies.get(SESSION_COOKIE)
        from_cookie = True
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        user_id = UUID(sub)
    except (JWTError, ValueError) as exc:
        raise credentials_exception from exc

    if from_cookie and request.method not in SAFE_METHODS:
        expected = payload.get("csrf") or ""
        provided = request.headers.get(CSRF_HEADER) or ""
        if not expected or not provided or not hmac.compare_digest(expected, provided):
            raise HTTPException(status_code=403, detail="CSRF token missing or invalid")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def _authorise(request: Request, user: User, allowed: frozenset) -> User:
    if user.role in allowed:
        return user
    if user.role in READ_ONLY_ROLES and request.method in SAFE_METHODS:
        return user
    raise HTTPException(status_code=403, detail="Insufficient permissions")


async def get_current_admin(
    request: Request, user: Annotated[User, Depends(get_current_user)]
) -> User:
    return _authorise(request, user, ADMIN_ROLES)


async def get_current_admin_writer(user: Annotated[User, Depends(get_current_user)]) -> User:
    """Admin-only even for GET: for GET endpoints that start external flows or change state."""
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return user


async def get_current_accountant_or_admin(
    request: Request, user: Annotated[User, Depends(get_current_user)]
) -> User:
    return _authorise(request, user, FINANCE_ROLES)
