import json
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.bidder import Bidder
from app.db.models.supply import Supply
from app.db.session import session_factory

logger = logging.getLogger(__name__)


async def load_json_to_db(json_path: Path) -> dict[str, int]:
    """
    Load data from JSON file into database.

    Args:
        json_path: Path to the JSON file containing supplies and bidders

    Returns:
        Dictionary with counts of loaded entities
    """
    logger.info(f"Loading data from {json_path}...")

    # Read JSON file
    with open(json_path, "r") as f:
        data = json.load(f)

    supplies_data = data.get("supplies", {})
    bidders_data = data.get("bidders", {})

    async with session_factory() as session:
        # Load bidders first
        bidders_count = 0
        bidder_objects = {}

        for bidder_id, bidder_info in bidders_data.items():
            # Check if bidder already exists
            result = await session.execute(
                select(Bidder).where(Bidder.id == bidder_id)
            )
            existing_bidder = result.scalar_one_or_none()

            if existing_bidder:
                bidder_objects[bidder_id] = existing_bidder
                logger.debug(f"Bidder {bidder_id} already exists, skipping")
            else:
                bidder = Bidder(
                    id=bidder_id,
                    country=bidder_info["country"],
                )
                session.add(bidder)
                bidder_objects[bidder_id] = bidder
                bidders_count += 1
                logger.debug(f"Added bidder {bidder_id}")

        await session.flush()

        # Load supplies
        supplies_count = 0
        for supply_id, bidder_ids in supplies_data.items():
            # Check if supply already exists
            result = await session.execute(
                select(Supply).where(Supply.id == supply_id)
            )
            existing_supply = result.scalar_one_or_none()

            if existing_supply:
                logger.debug(f"Supply {supply_id} already exists, updating bidders")
                supply = existing_supply
            else:
                supply = Supply(id=supply_id)
                session.add(supply)
                supplies_count += 1
                logger.debug(f"Added supply {supply_id}")

            # Associate bidders with supply
            supply.bidders = [bidder_objects[bid_id] for bid_id in bidder_ids if bid_id in bidder_objects]

        await session.commit()

    logger.info(
        f"Data load complete: {supplies_count} supplies, {bidders_count} bidders"
    )

    return {
        "supplies_count": supplies_count,
        "bidders_count": bidders_count,
    }
