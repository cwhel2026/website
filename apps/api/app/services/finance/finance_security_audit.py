"""Production readiness checklist — returns evidence, not a pass/fail certificate."""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.finance.document_store import receipts_root
from app.services.finance.freeagent_adapter import freeagent_status
from app.services.finance.token_vault import encryption_configured


async def run_finance_security_audit(db: AsyncSession) -> dict:
    settings = get_settings()
    root = receipts_root()
    backup_raw = (settings.finance_receipts_backup_dir or "").strip()
    backup = Path(backup_raw).resolve() if backup_raw else None
    sample = next(root.glob("*"), None)

    receipt_perms_ok = True
    if sample and sample.is_file():
        try:
            mode = oct(sample.stat().st_mode)[-3:]
            receipt_perms_ok = mode in ("600", "640")
        except OSError:
            receipt_perms_ok = False

    receipts_path = Path(settings.finance_receipts_dir or "")
    volume_persistent = bool(settings.finance_receipts_dir) and settings.finance_receipts_dir.startswith("/data")
    mount_writable = root.exists() and os.access(root, os.W_OK)
    backup_configured = backup is not None
    backup_readable = backup is not None and backup.exists() and backup.is_dir()
    same_device_as_tmp = False
    try:
        if root.exists():
            same_device_as_tmp = root.stat().st_dev == Path("/tmp").stat().st_dev and str(root).startswith("/tmp")
    except OSError:
        pass

    fa = await freeagent_status(db)
    jwt_prod_ok = settings.environment != "production" or settings.jwt_secret not in (
        "",
        "dev-secret-change-in-production",
    )

    return {
        "encryption_key_configured": encryption_configured(),
        "jwt_production_safe": jwt_prod_ok,
        "receipt_volume_persistent": volume_persistent,
        "receipt_on_ephemeral_storage": same_device_as_tmp,
        "receipt_mount_writable": mount_writable,
        "receipt_backup_configured": backup_configured,
        "receipt_backup_reachable": backup_readable,
        "receipt_backup_not_cwd": backup is None or backup != Path.cwd(),
        "receipt_file_permissions_ok": receipt_perms_ok,
        "finance_telegram_ingest_key_set": bool(settings.finance_telegram_ingest_key),
        "freeagent_oauth_configured": bool(settings.freeagent_client_id and settings.freeagent_redirect_uri),
        "freeagent_connected": fa.can_sync,
        "freeagent_token_refresh_possible": fa.can_sync and encryption_configured(),
        "receipt_attach_flag": settings.finance_receipt_freeagent_attach,
        "receipt_expense_create_flag": settings.finance_receipt_freeagent_expense,
        "celery_broker_configured": bool(settings.celery_broker_url or settings.redis_url),
        "notes": [
            "Receipt blobs on API/worker volume only — website service must forward Telegram to API.",
            "Run alembic through 0010 before production.",
            "Production verification requires owner sign-off on Railway — this audit is configuration-only.",
        ],
        "environment": settings.environment,
        "receipts_dir": settings.finance_receipts_dir or str(root),
        "pid_uid": os.getuid(),
    }