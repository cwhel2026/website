"""Branded before/after layouts — crops and arranges only; no fake restoration edits."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.services.marketing.media_store import resolve_path, store_bytes

FORMATS = {
    "facebook_landscape": (1200, 630),
    "instagram_square": (1080, 1080),
    "instagram_portrait": (1080, 1350),
    "story_vertical": (1080, 1920),
}


def _load_image(storage_key: str) -> Image.Image:
    path = resolve_path(storage_key)
    return Image.open(path).convert("RGB")


def _fit(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    img.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, (15, 23, 42))
    ox = (size[0] - img.width) // 2
    oy = (size[1] - img.height) // 2
    canvas.paste(img, (ox, oy))
    return canvas


def render_before_after(
    *,
    before_key: str,
    after_key: str,
    format_name: str,
    brand_name: str = "Revive My Drive Ltd",
    website: str = "revivemydrive.co.uk",
    location_caption: str | None = None,
) -> tuple[str, bytes]:
    if format_name not in FORMATS:
        raise ValueError(f"Unknown format: {format_name}")
    target = FORMATS[format_name]
    before = _load_image(before_key)
    after = _load_image(after_key)
    half_w = target[0] // 2
    half_size = (half_w, target[1] - 80)
    left = _fit(before, half_size)
    right = _fit(after, half_size)
    canvas = Image.new("RGB", target, (4, 120, 87))
    canvas.paste(left, (0, 40))
    canvas.paste(right, (half_w, 40))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
        small = font
    draw.text((20, 8), brand_name, fill=(255, 255, 255), font=font)
    draw.text((half_w - 50, 8), "BEFORE", fill=(255, 255, 255), font=small)
    draw.text((half_w + half_w // 2 - 30, 8), "AFTER", fill=(255, 255, 255), font=small)
    footer = location_caption or website
    draw.text((20, target[1] - 32), footer[:80], fill=(230, 255, 245), font=small)
    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=90)
    data = buf.getvalue()
    key, _ = store_bytes(data=data, filename=f"{format_name}.jpg", subdir="rendered")
    return key, data