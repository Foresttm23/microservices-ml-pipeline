from fastapi import Depends
from fastapi_limiter.depends import RateLimiter

from gateway.core.config import get_settings

RateLimiterGlobalDep = Depends(
    RateLimiter(times=get_settings().RATE_LIMIT_REQUESTS_PER_MINUTE, seconds=60)
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
