import logging
import random

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dao.bidder import bidder_dao
from app.db.dao.supply import supply_dao
from app.models.bid import BidResponse

logger = logging.getLogger(__name__)


class BiddingService:
    NO_BID_PROBABILITY = 0.3
    MIN_BID_PRICE = 0.01
    MAX_BID_PRICE = 1.00

    def __init__(self, session: AsyncSession):
        self.session = session

    async def run_auction(self, supply_id: str, country: str) -> BidResponse:
        if not await supply_dao.get(
            session=self.session,
            supply_id=supply_id
        ):
            logger.error(f"Supply {supply_id} not found")
            raise ValueError(f"Supply {supply_id} not found")

        if not (
            eligible_bidders := await bidder_dao.get_eligible_for_supply(
                session=self.session,
                supply_id=supply_id,
                country=country,
            )
        ):
            logger.warning(f"No eligible bidders for supply {supply_id} with country {country}")
            raise ValueError(f"No eligible bidders found for country {country}")

        logger.info(f"Auction for {supply_id} (country={country}):")

        bids: dict[str, float] = {}

        for bidder in eligible_bidders:
            if random.random() < self.NO_BID_PROBABILITY:
                logger.info(f"{bidder.id} - no bid")
                continue

            bids[bidder.id] = (
                bid_price := round(random.uniform(self.MIN_BID_PRICE, self.MAX_BID_PRICE), 2)
            )
            logger.info(f"{bidder.id} - price {bid_price:.2f}")

        if not bids.keys():
            logger.warning(f"All bidders skipped for supply {supply_id}")
            raise ValueError("No bids received - all bidders skipped")

        winner_id = max(bids, key=bids.get)
        winning_price = bids[winner_id]

        logger.info(f"Winner: {winner_id} ({winning_price:.2f})")

        return BidResponse(winner=winner_id, price=winning_price)
