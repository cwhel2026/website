"""Normalise Railway Postgres URLs for async (asyncpg) and sync (psycopg3) SQLAlchemy drivers."""

from __future__ import annotations

from urllib.parse import urlparse


def _canonical_postgresql(url: str) -> str:
    u = url.strip()
    if u.startswith("postgres://"):
        return "postgresql://" + u[len("postgres://") :]
    return u


def normalize_async_database_url(url: str) -> str:
    """Ensure async SQLAlchemy uses postgresql+asyncpg (never implicit psycopg2)."""
    u = _canonical_postgresql(url)
    if "+asyncpg" in u:
        return u
    if u.startswith("postgresql+psycopg://") or u.startswith("postgresql+psycopg2://"):
        return "postgresql+asyncpg://" + u.split("://", 1)[1]
    if u.startswith("postgresql://"):
        return "postgresql+asyncpg://" + u[len("postgresql://") :]
    return u


def normalize_sync_database_url(url: str) -> str:
    """Ensure sync SQLAlchemy uses postgresql+psycopg (psycopg3), not missing psycopg2."""
    u = _canonical_postgresql(url)
    if "+psycopg://" in u and "+psycopg2" not in u:
        return u
    if u.startswith("postgresql+asyncpg://"):
        return "postgresql+psycopg://" + u[len("postgresql+asyncpg://") :]
    if u.startswith("postgresql+psycopg2://"):
        return "postgresql+psycopg://" + u[len("postgresql+psycopg2://") :]
    if u.startswith("postgresql://"):
        return "postgresql+psycopg://" + u[len("postgresql://") :]
    return u


def derive_sync_from_async(async_url: str) -> str:
    return normalize_sync_database_url(async_url)


def database_target_label(url: str) -> str:
    """Host/user/database for logs — never includes a password."""
    try:
        p = urlparse(normalize_sync_database_url(url).replace("+psycopg", "", 1))
        host = p.hostname or "?"
        port = p.port or 5432
        user = p.username or "?"
        db = (p.path or "/").lstrip("/") or "?"
        return f"user={user} host={host}:{port} db={db}"
    except Exception:
        return "url=unparseable"