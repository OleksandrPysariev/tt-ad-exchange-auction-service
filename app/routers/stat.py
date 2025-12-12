import logging

from fastapi import APIRouter, status

from app.builders.api.statistics import StatisticsResponseBuilder
from app.models.api.response.statistics import StatisticsResponse
from app.services.statistics import statistics_service

router = APIRouter(tags=["bid"])

logger = logging.getLogger(__name__)


@router.get(
    "/stat",
    response_model=dict[str, StatisticsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get auction statistics",
    description="Returns overall service statistics such as total requests, bidder wins, and revenue grouped per supply",
    responses={
        200: {
            "description": "Statistics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "supply1": {
                            "total_reqs": 10,
                            "reqs_per_country": {"US": 5, "GB": 5},
                            "bidders": {
                                "bidder1": {"wins": 2, "total_revenue": 0.4, "no_bids": 3},
                                "bidder2": {"wins": 3, "total_revenue": 0.7, "no_bids": 1},
                            },
                        }
                    }
                }
            },
        }
    },
)
async def get_statistics() -> dict[str, StatisticsResponse]:
    statistics_result = await statistics_service.get_all_statistics()
    return StatisticsResponseBuilder.build(statistics_result)
