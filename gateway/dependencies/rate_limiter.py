from fastapi import Depends, Request
from fastapi_limiter.depends import RateLimiter

from gateway.core.config import get_settings


async def global_identifier(request: Request):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0]
    else:
        # TODO later change to the user_id check instead.
        ip = request.client.host if request.client else "127.0.0.1"
    # Ensure all routes using this limiter share the same redis key bucket for this IP
    return f"global_limit:{ip}"


RateLimiterGlobalDep = Depends(
    RateLimiter(
        times=get_settings().RATE_LIMIT_REQUESTS_PER_MINUTE,
        seconds=60,
        identifier=global_identifier,
    )
)
RateLimiterLoginDep = Depends(
    RateLimiter(times=get_settings().RATE_LIMIT_AUTH_LOGIN, seconds=60)
)
RateLimiterRegisterDep = Depends(
    RateLimiter(times=get_settings().RATE_LIMIT_AUTH_REGISTER, seconds=60)
)
RateLimiterRefreshDep = Depends(
    RateLimiter(times=get_settings().RATE_LIMIT_AUTH_REFRESH, seconds=60)
)
RateLimiterLogoutDep = Depends(
    RateLimiter(times=get_settings().RATE_LIMIT_AUTH_LOGOUT, seconds=60)
)
RateLimiterMeDep = Depends(
    RateLimiter(times=get_settings().RATE_LIMIT_AUTH_ME, seconds=60)
)
RateLimiterQueryRunDep = Depends(
    RateLimiter(times=get_settings().RATE_LIMIT_QUERY_RUN, seconds=60)
)
