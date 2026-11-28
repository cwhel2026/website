"""Lightweight public website SEO audit — fetches real HTML only."""

from __future__ import annotations

import re
from datetime import UTC, datetime

import httpx

from app.config import get_settings


async def audit_public_site() -> dict:
    settings = get_settings()
    base = (settings.public_dashboard_base_url or (settings.cors_origin_list[0] if settings.cors_origin_list else "")).rstrip("/")
    if not base:
        return {"audited_at": datetime.now(UTC).isoformat(), "pages": [], "state": "site_url_not_configured"}
    pages = ["/", "/services/tarmac-restoration", "/quote", "/contact", "/privacy", "/terms"]
    results = []
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        for path in pages:
            url = f"{base}{path}"
            try:
                r = await client.get(url)
                html = r.text[:50000]
                title = _meta(html, "title")
                desc = _meta(html, 'meta name="description"')
                canonical = _canonical(html)
                results.append(
                    {
                        "url": url,
                        "status": r.status_code,
                        "title": title,
                        "description": desc,
                        "canonical": canonical,
                        "has_json_ld": "application/ld+json" in html,
                    }
                )
            except httpx.HTTPError:
                results.append({"url": url, "error": "Website request failed"})
    return {"audited_at": datetime.now(UTC).isoformat(), "pages": results}


def _meta(html: str, pattern: str) -> str | None:
    if pattern == "title":
        m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
        return m.group(1).strip() if m else None
    m = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)', html, re.I)
    return m.group(1) if m else None


def _canonical(html: str) -> str | None:
    m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', html, re.I)
    return m.group(1) if m else None