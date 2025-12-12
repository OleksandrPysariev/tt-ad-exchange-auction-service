from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.dao.common import CommonDAO
from app.db.models.supply import Supply
from app.models.dao.supply import SupplyCreate, SupplyUpdate


class SupplyDAO(CommonDAO[Supply, SupplyCreate, SupplyUpdate]):
    async def get(self, session: AsyncSession, supply_id: str) -> Optional[Supply]:
        result = await session.execute(select(Supply).where(Supply.id == supply_id).options(selectinload(Supply.bidders)))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_with_bidders(
        session: AsyncSession,
        supply: Supply,
        bidders: list["Bidder"],
        autocommit: bool = True,
    ) -> Supply:
        supply.bidders = bidders
        session.add(supply)
        if autocommit:
            await session.commit()
            await session.refresh(supply)
        return supply


supply_dao = SupplyDAO(Supply)
