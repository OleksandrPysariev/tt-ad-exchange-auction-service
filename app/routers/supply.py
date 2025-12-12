import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dao.supply import supply_dao
from app.db.session import get_db_session
from app.models.api.response.supply import SupplyResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["supply"])


@router.get(
    "/supplies",
    response_model=list[SupplyResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all available supplies",
    description="Returns a list of all available supply IDs that can be used in the /bid endpoint",
    responses={
        200: {
            "description": "List of supplies retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {"id": "supply1"},
                        {"id": "supply2"},
                        {"id": "supply3"}
                    ]
                }
            },
        }
    },
)
async def get_supplies(
    session: AsyncSession = Depends(get_db_session),
) -> list[SupplyResponse]:
    logger.info("Fetching all supplies")
    supplies = await supply_dao.get_all(session)
    return [SupplyResponse.model_validate(supply) for supply in supplies]
