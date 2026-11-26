from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.config import get_settings

_LOOPBACK = {"127.0.0.1", "::1", "localhost"}


def client_ip(request: Request) -> str:
    """Rate-limit key.

    In the combined container every request reaches uvicorn from the Next.js proxy
    on loopback, so the peer address is the same for all visitors. Only then is
    X-Forwarded-For trusted, and only its right-most entry (appended by the
    Railway edge), which a client cannot forge.
    """
    peer = get_remote_address(request)
    if peer in _LOOPBACK:
        forwarded = request.headers.get("x-forwarded-for", "")
        hops = [h.strip() for h in forwarded.split(",") if h.strip()]
        if hops:
            return hops[-1]
    return peer


def _build_limiter() -> Limiter:
    settings = get_settings()
    if settings.rate_limit_storage_redis and settings.redis_url:
        return Limiter(key_func=client_ip, default_limits=[], storage_uri=settings.redis_url)
    return Limiter(key_func=client_ip, default_limits=[])


limiter = _build_limiter()
