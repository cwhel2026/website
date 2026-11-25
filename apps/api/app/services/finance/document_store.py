"""Local receipt blob storage — configure FINANCE_RECEIPTS_DIR on persistent volume in production."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from app.config import get_settings


def receipts_root() -> Path:
    settings = get_settings()
    root = Path(settings.finance_receipts_dir or "/tmp/rmd-finance-receipts")
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_receipt_bytes(content: bytes, filename: str) -> tuple[str, str]:
    digest = hashlib.sha256(content).hexdigest()
    ext = Path(filename).suffix or ".bin"
    storage_key = f"{digest[:32]}{ext}"
    path = receipts_root() / storage_key
    if not path.exists():
        path.write_bytes(content)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
    return storage_key, digest


def receipt_file_path(storage_key: str) -> Path:
    return receipts_root() / storage_key