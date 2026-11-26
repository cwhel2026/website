"""Ensure the owner account exists and matches DEFAULT_ADMIN_* from the environment."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_password, verify_password
from app.config import get_settings
from app.models.user import User, UserRole


async def ensure_owner_from_env(session: AsyncSession) -> None:
    """Create or update the owner user for DEFAULT_ADMIN_EMAIL / DEFAULT_ADMIN_PASSWORD."""
    settings = get_settings()
    email = settings.default_admin_email.strip().lower()
    desired_hash = hash_password(settings.default_admin_password)

    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        legacy = (
            await session.execute(
                select(User).where(User.role == UserRole.OWNER).order_by(User.created_at).limit(1)
            )
        ).scalar_one_or_none()
        if legacy and legacy.email != email:
            legacy.email = email
            user = legacy
        else:
            session.add(
                User(
                    email=email,
                    password_hash=desired_hash,
                    full_name="Business Owner",
                    role=UserRole.OWNER,
                    is_active=True,
                )
            )
            return

    user.role = UserRole.OWNER
    user.is_active = True
    if not verify_password(settings.default_admin_password, user.password_hash):
        user.password_hash = desired_hash


async def rotate_owner_password(session: AsyncSession, *, new_password: str) -> None:
    settings = get_settings()
    email = settings.default_admin_email.strip().lower()
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            email=email,
            full_name="Business Owner",
            role=UserRole.OWNER,
            is_active=True,
        )
        session.add(user)
        await session.flush()
    user.password_hash = hash_password(new_password)
    user.is_active = True
    user.role = UserRole.OWNER