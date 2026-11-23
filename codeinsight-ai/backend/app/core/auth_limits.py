import hashlib
from functools import lru_cache

from fastapi import HTTPException, Request
from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings

WINDOW_SECONDS = 60
COUNTER = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return count
"""


@lru_cache
def redis_client(url):
    return Redis.from_url(url, socket_timeout=2, socket_connect_timeout=2)


def limit_auth(request: Request):
    settings = get_settings()
    if not settings.production:
        return
    address = request.client.host if request.client else "unknown"
    scope = request.url.path
    digest = hashlib.sha256(f"{scope}:{address}".encode()).hexdigest()
    maximum = 5 if scope.endswith("/signup") else 20
    try:
        count = redis_client(settings.redis_url).eval(COUNTER, 1, f"codeguard:auth:{digest}", WINDOW_SECONDS)
    except RedisError as exc:
        raise HTTPException(503, "Authentication is temporarily unavailable") from exc
    if count > maximum:
        raise HTTPException(429, "Too many authentication requests", headers={"Retry-After": str(WINDOW_SECONDS)})
