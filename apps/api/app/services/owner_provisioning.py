"""Bootstrap owner credentials without overwriting subsequent password rotation."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_password, verify_password
from app.config import get_settings
from app.models.user import User, UserRole


async def ensure_owner_from_env(session: AsyncSession) -> None:
    """Create or update the owner user for DEFAULT_ADMIN_EMAIL / DEFAULT_ADMIN_PASSWORD."""
    settings = get_settings()
    email = settings.default_admin_email.strip().lower()

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
                    password_hash=hash_password(settings.default_admin_password),
                    full_name="Business Owner",
                    role=UserRole.OWNER,
                    is_active=True,
                )
            )
            return

    if user.role != UserRole.OWNER:
        raise RuntimeError("Configured owner email belongs to a non-owner account")
    # Existing owner credentials and activation state are authoritative.


AUDITOR_MIN_PASSWORD = 16


async def ensure_e2e_auditor_from_env(session: AsyncSession) -> str:
    """Provision the read-only browser-test account from E2E_AUDITOR_EMAIL / E2E_AUDITOR_PASSWORD.

    * both set: create or update the account as role AUDITOR (GET-only access).
    * email set, password empty: deactivate the account (revocation).
    * never converts an existing non-auditor account, and never touches the owner.
    """
    import logging

    log = logging.getLogger(__name__)
    settings = get_settings()
    email = (settings.e2e_auditor_email or "").strip().lower()
    password = settings.e2e_auditor_password or ""
    if not email:
        return "not_configured"
    if email == settings.default_admin_email.strip().lower():
        log.error("E2E_AUDITOR_EMAIL must not be the owner account; skipping")
        return "refused_owner"

    user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is not None and user.role != UserRole.AUDITOR:
        log.error("E2E_AUDITOR_EMAIL belongs to a %s account; refusing to change it", user.role.value)
        return "refused_existing_role"

    if not password:
        if user is not None and user.is_active:
            user.is_active = False
            return "deactivated"
        return "inactive"
    if len(password) < AUDITOR_MIN_PASSWORD:
        log.error("E2E_AUDITOR_PASSWORD must be at least %s characters; skipping", AUDITOR_MIN_PASSWORD)
        return "refused_weak_password"

    if user is None:
        session.add(
            User(
                email=email,
                password_hash=hash_password(password),
                full_name="Automated test (read-only)",
                role=UserRole.AUDITOR,
                is_active=True,
            )
        )
        return "created"
    user.is_active = True
    if not verify_password(password, user.password_hash):
        user.password_hash = hash_password(password)
    return "updated"


async def rotate_owner_password(session: AsyncSession, *, new_password: str) -> None:
    settings = get_settings()
    email = settings.default_admin_email.strip().lower()
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            email=email,
            full_name="Business Owner",
            password_hash=hash_password(new_password),
            role=UserRole.OWNER,
            is_active=True,
        )
        session.add(user)
    elif user.role != UserRole.OWNER:
        raise RuntimeError("Configured owner email belongs to a non-owner account")
    user.password_hash = hash_password(new_password)
    user.is_active = True
    user.role = UserRole.OWNER