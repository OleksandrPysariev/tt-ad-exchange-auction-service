import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.builders.api.bidding import BiddingResponseBuilder
from app.db.session import get_db_session
from app.dependencies.rate_limit import check_rate_limit
from app.models.api.request.bid import BidRequest
from app.models.api.response.bid import BidResponse
from app.services.bidding import BiddingService
from app.services.statistics import statistics_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["bid"])


@router.post(
    "/bid",
    response_model=BidResponse,
    status_code=status.HTTP_200_OK,
    summary="Start a new auction",
    description="Starts a new auction for a given supply ID with rate limiting (max 3 requests per minute per IP)",
    responses={
        200: {
            "description": "Auction completed successfully",
            "content": {
                "application/json": {
                    "example": {"winner": "bidder2", "price": 0.83}
                }
            },
        },
        400: {
            "description": "Invalid supply or no eligible bidders",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Supply not found"
                    }
                }
            },
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Rate limit exceeded. Maximum 3 requests per minute per IP address."
                    }
                }
            },
        },
    },
)
async def bid(
    request: BidRequest = Depends(check_rate_limit),
    session: AsyncSession = Depends(get_db_session),
) -> BidResponse:
    logger.info(
        f"Auction request for {request.supply_id=}, {request.ip=}, "
        f"{request.country=}, {request.tmax=}ms"
    )

    bidding_service = BiddingService(session, statistics_service)

    try:
        result = await bidding_service.run_auction(request.supply_id, request.country, request.tmax)
        return BiddingResponseBuilder.build(auction_result=result)
    except ValueError as e:
        logger.error(f"Auction failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
