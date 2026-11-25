"""Persistent marketing media on a mounted volume (same pattern as finance receipts)."""

from __future__ import annotations

import hashlib
import re
import uuid
from pathlib import Path

from app.config import get_settings


def media_root() -> Path:
    root = Path(get_settings().marketing_media_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def safe_filename(name: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9._-]", "_", name)[:180]
    return base or "upload.bin"


def store_bytes(*, data: bytes, filename: str, subdir: str = "uploads") -> tuple[str, str]:
    digest = hashlib.sha256(data).hexdigest()
    folder = media_root() / subdir / digest[:2]
    folder.mkdir(parents=True, exist_ok=True)
    key = f"{subdir}/{digest[:2]}/{digest}_{safe_filename(filename)}"
    path = media_root() / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return key, digest


def resolve_path(storage_key: str) -> Path:
    root = media_root().resolve()
    target = (root / storage_key).resolve()
    if not str(target).startswith(str(root)):
        raise ValueError("Invalid storage key")
    return target