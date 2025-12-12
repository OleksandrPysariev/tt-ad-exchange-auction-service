import logging
from typing import Optional

import redis.asyncio as redis

from app.models.services.statistics import StatisticsResult
from app.redis_db.client import redis_client

logger = logging.getLogger(__name__)


class StatisticsService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    @staticmethod
    def _get_supply_key(supply_id: str) -> str:
        return f"stats:{supply_id}"

    async def record_request(self, supply_id: str, country: str) -> None:
        try:
            key = self._get_supply_key(supply_id)
            pipe = self.redis.pipeline()
            await pipe.hincrby(key, "total_reqs", 1)
            await pipe.hincrby(key, f"country:{country}", 1)
            await pipe.execute()

        except Exception as e:
            logger.error(f"Error recording request: {e}", exc_info=True)

    async def record_auction_result(
        self,
        supply_id: str,
        winner_id: Optional[str],
        winning_price: float,
        no_bid_ids: list[str],
        timeout_ids: list[str] = None,
    ) -> None:
        try:
            key = self._get_supply_key(supply_id)
            pipe = self.redis.pipeline()

            if winner_id:
                await pipe.hincrby(key, f"bidder:{winner_id}:wins", 1)
                await pipe.hincrbyfloat(key, f"bidder:{winner_id}:revenue", winning_price)

            for bidder_id in no_bid_ids:
                await pipe.hincrby(key, f"bidder:{bidder_id}:no_bids", 1)

            if timeout_ids:
                for bidder_id in timeout_ids:
                    await pipe.hincrby(key, f"bidder:{bidder_id}:timeouts", 1)

            await pipe.execute()

        except Exception as e:
            logger.error(f"Error recording auction result: {e}", exc_info=True)

    async def get_all_statistics(self) -> StatisticsResult | None:
        try:
            keys = await self.redis.keys("stats:*")

            if not keys:
                return

            pipe = self.redis.pipeline()
            for key in keys:
                await pipe.hgetall(key)

            results = await pipe.execute()

            stats: dict[str, dict] = {}
            for key, data in zip(keys, results):
                supply_id = key.split(":", 1)[1]
                stats[supply_id] = data

            return StatisticsResult(supplies=stats)
        except Exception as e:
            logger.error(f"Error getting statistics: {e}", exc_info=True)


statistics_service = StatisticsService(redis_client=redis_client)
