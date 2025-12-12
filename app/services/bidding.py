import asyncio
import logging
import random

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dao.bidder import bidder_dao
from app.db.dao.supply import supply_dao
from app.models.services.bidding import AuctionResult
from app.services.statistics import StatisticsService

logger = logging.getLogger(__name__)


class BiddingService:
    NO_BID_PROBABILITY = 0.3
    MIN_BID_PRICE = 0.01
    MAX_BID_PRICE = 1.00

    def __init__(self, session: AsyncSession, statistics_service: StatisticsService):
        self.session = session
        self.statistics_service = statistics_service

    async def run_auction(self, supply_id: str, country: str, tmax: int = 200) -> AuctionResult:
        """
        Run an auction with latency simulation and timeout tracking.

        Args:
            supply_id: Supply ID
            country: Country code
            tmax: Maximum time in milliseconds for bidder to respond

        Returns:
            AuctionResult with winner and price
        """
        await self.statistics_service.record_request(supply_id, country)

        # Validate supply exists
        if not await supply_dao.get(
            session=self.session,
            supply_id=supply_id
        ):
            logger.error(f"Supply {supply_id} not found")
            raise ValueError(f"Supply {supply_id} not found")

        # Get eligible bidders
        if not (
            eligible_bidders := await bidder_dao.get_eligible_for_supply(
                session=self.session,
                supply_id=supply_id,
                country=country,
            )
        ):
            logger.warning(f"No eligible bidders for supply {supply_id} with country {country}")
            raise ValueError(f"No eligible bidders found for country {country}")

        logger.info(f"Auction for {supply_id} (country={country}, tmax={tmax}ms):")

        bids: dict[str, float] = {}
        no_bid_ids: list[str] = []
        timeout_ids: list[str] = []

        # Run auction with latency simulation
        for bidder in eligible_bidders:
            # Simulate bidder response latency (0 to 1.5x tmax)
            latency_ms = random.randint(0, int(tmax * 1.5))

            # Check if bidder times out
            if latency_ms > tmax:
                logger.warning(f"{bidder.id} - timeout (latency: {latency_ms}ms > tmax: {tmax}ms)")
                timeout_ids.append(bidder.id)
                continue

            # Simulate delay
            if latency_ms > 0:
                await asyncio.sleep(latency_ms / 1000)  # Convert to seconds
                if latency_ms > tmax * 0.8:  # Log if delay is > 80% of tmax
                    logger.info(f"{bidder.id} - delayed response (latency: {latency_ms}ms)")

            # Check if bidder decides not to bid
            if random.random() < self.NO_BID_PROBABILITY:
                logger.info(f"{bidder.id} - no bid")
                no_bid_ids.append(bidder.id)
                continue

            # Generate bid
            bids[bidder.id] = (
                bid_price := round(random.uniform(self.MIN_BID_PRICE, self.MAX_BID_PRICE), 2)
            )
            logger.info(f"{bidder.id} - price {bid_price:.2f}")

        # Check if we have any bids
        if not bids.keys():
            logger.warning(f"All bidders skipped for supply {supply_id} (no_bids={len(no_bid_ids)}, timeouts={len(timeout_ids)})")
            # Record that all bidders skipped
            await self.statistics_service.record_auction_result(
                supply_id=supply_id,
                winner_id=None,
                winning_price=0.0,
                no_bid_ids=no_bid_ids,
                timeout_ids=timeout_ids,
            )
            raise ValueError("No bids received - all bidders skipped or timed out")

        # Determine winner
        winner_id = max(bids, key=bids.get)
        winning_price = bids[winner_id]

        logger.info(f"Winner: {winner_id} ({winning_price:.2f})")

        # Record auction result
        await self.statistics_service.record_auction_result(
            supply_id=supply_id,
            winner_id=winner_id,
            winning_price=winning_price,
            no_bid_ids=no_bid_ids,
            timeout_ids=timeout_ids,
        )

        return AuctionResult(winner=winner_id, price=winning_price)
