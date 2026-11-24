from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings


def _build_limiter() -> Limiter:
    settings = get_settings()
    if settings.rate_limit_storage_redis and settings.redis_url:
        return Limiter(key_func=get_remote_address, default_limits=[], storage_uri=settings.redis_url)
    return Limiter(key_func=get_remote_address, default_limits=[])


limiter = _build_limiter()