from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dao.common import CommonDAO
from app.db.models.bidder import Bidder
from app.db.models.supply import Supply
from app.models.dao.bidder import BidderCreate, BidderUpdate


class BidderDAO(CommonDAO[Bidder, BidderCreate, BidderUpdate]):
    @staticmethod
    async def get_eligible_for_supply(session: AsyncSession, supply_id: str, country: str) -> list[Bidder]:
        stmt = (
            select(Bidder)
            .join(Bidder.supplies)
            .where(and_(Supply.id == supply_id, Bidder.country == country))
        )

        result = await session.execute(stmt)
        return list(result.scalars().all())


bidder_dao = BidderDAO(Bidder)
