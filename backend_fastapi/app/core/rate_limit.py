from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request


def get_client_ip(request: Request) -> str:
    """
    Extract client IP for rate limiting.
    Checks X-Forwarded-For header first (for proxy/load balancer scenarios),
    then falls back to direct client IP.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# Create rate limiter instance
limiter = Limiter(key_func=get_client_ip)
