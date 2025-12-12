import logging

from fastapi import HTTPException, status

from app.models.api.request.bid import BidRequest
from app.services.rate_limiter import rate_limiter


logger = logging.getLogger(__name__)


async def check_rate_limit(request: BidRequest) -> BidRequest:
    if not await rate_limiter.is_allowed(request.ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 3 requests per minute per IP address.",
        )

    return request
