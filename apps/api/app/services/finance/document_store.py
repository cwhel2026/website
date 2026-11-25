"""Local receipt blob storage — configure FINANCE_RECEIPTS_DIR on persistent volume in production."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import shutil

from app.config import get_settings


def _valid_backup_root() -> Path | None:
    settings = get_settings()
    raw = (settings.finance_receipts_backup_dir or "").strip()
    if not raw:
        return None
    return Path(raw).resolve()


def receipts_root() -> Path:
    settings = get_settings()
    root = Path(settings.finance_receipts_dir or "/tmp/rmd-finance-receipts")
    root.mkdir(parents=True, exist_ok=True)
    return root


def backup_receipt_copy(storage_key: str) -> bool:
    backup_root = _valid_backup_root()
    if backup_root is None:
        return False
    backup_root.mkdir(parents=True, exist_ok=True)
    src = receipts_root() / storage_key
    if not src.exists():
        return False
    dest = backup_root / storage_key
    if dest.exists() and dest.stat().st_size == src.stat().st_size:
        return True
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    shutil.copy2(src, tmp)
    os.replace(tmp, dest)
    try:
        os.chmod(dest, 0o600)
    except OSError:
        pass
    return True


def save_receipt_bytes(content: bytes, filename: str) -> tuple[str, str]:
    digest = hashlib.sha256(content).hexdigest()
    ext = Path(filename).suffix or ".bin"
    storage_key = f"{digest[:32]}{ext}"
    path = receipts_root() / storage_key
    if not path.exists():
        tmp = path.with_suffix(path.suffix + ".part")
        tmp.write_bytes(content)
        os.replace(tmp, path)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        verify = hashlib.sha256(path.read_bytes()).hexdigest()
        if verify != digest:
            raise OSError("receipt integrity check failed after write")
    backup_receipt_copy(storage_key)
    return storage_key, digest


def receipt_file_path(storage_key: str) -> Path:
    return receipts_root() / storage_key


def verify_receipt_integrity(storage_key: str, expected_sha256: str) -> bool:
    path = receipt_file_path(storage_key)
    if not path.exists():
        return False
    return hashlib.sha256(path.read_bytes()).hexdigest() == expected_sha256