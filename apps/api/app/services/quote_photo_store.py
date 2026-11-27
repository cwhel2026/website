"""Private driveway photograph bytes. Metadata is stripped by re-encoding."""

from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path

from PIL import Image, ImageOps

from app.config import get_settings

MAX_UPLOAD_BYTES = 12 * 1024 * 1024
MAX_EDGE = 1600
TARGET_MAX_BYTES = 500 * 1024
MAX_PHOTOS = 8
# Stay large enough for a close-up of a crack. Byte size gives way once this floor is reached.
DETAIL_FLOOR_EDGE = 1280


def photos_root() -> Path:
    settings = get_settings()
    raw = (settings.quote_photos_dir or "").strip() or "/tmp/surfacecoat-quote-photos"
    path = Path(raw).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def prepare_image(raw: bytes) -> bytes:
    """Validate, compress and drop EXIF. Raises ValueError for anything that is not a photo."""
    if not raw or len(raw) > MAX_UPLOAD_BYTES:
        raise ValueError("Photograph is too large")
    if not _looks_like_image(raw):
        raise ValueError("Upload a photograph")
    try:
        image = Image.open(io.BytesIO(raw))
        image.load()
    except Exception as exc:
        raise ValueError("Upload a photograph") from exc
    image = ImageOps.exif_transpose(image)
    if image.mode != "RGB":
        image = image.convert("RGB")
    best = b""
    for edge in (MAX_EDGE, 1400, DETAIL_FLOOR_EDGE):
        working = image.copy()
        working.thumbnail((edge, edge), Image.Resampling.LANCZOS)
        working.info = {}
        for quality in (78, 70, 62):
            out = io.BytesIO()
            working.save(out, format="JPEG", quality=quality, optimize=True)
            best = out.getvalue()
            if len(best) <= TARGET_MAX_BYTES:
                return best
    return best


def save_photo_bytes(data: bytes) -> tuple[str, str]:
    digest = hashlib.sha256(data).hexdigest()
    key = f"{digest[:2]}/{digest}.jpg"
    root = photos_root()
    dest = (root / key).resolve()
    if not dest.is_relative_to(root):
        raise ValueError("invalid path")
    dest.parent.mkdir(parents=True, exist_ok=True)
    temporary = dest.with_suffix(".part")
    temporary.write_bytes(data)
    os.chmod(temporary, 0o600)
    os.replace(temporary, dest)
    os.chmod(dest, 0o600)
    return key, digest


def read_photo_bytes(key: str) -> bytes:
    path = photo_file(key)
    return path.read_bytes()


def photo_file(key: str) -> Path:
    root = photos_root()
    dest = (root / key).resolve()
    if not dest.is_relative_to(root) or not dest.is_file():
        raise FileNotFoundError(key)
    return dest


def delete_photo_file(key: str) -> None:
    try:
        photo_file(key).unlink()
    except FileNotFoundError:
        return


def _looks_like_image(raw: bytes) -> bool:
    if raw.startswith(b"\xff\xd8\xff"):
        return True
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    return len(raw) > 12 and raw.startswith(b"RIFF") and raw[8:12] == b"WEBP"
