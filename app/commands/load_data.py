import json
import logging
from pathlib import Path

from app.db.dao.bidder import bidder_dao
from app.db.dao.supply import supply_dao
from app.db.session import session_factory
from app.models.dao.bidder import BidderCreate
from app.models.dao.supply import SupplyCreate

logger = logging.getLogger(__name__)


async def load_json_to_db(json_path: Path) -> dict[str, int]:
    # Load data from json to db
    logger.info(f"Loading data from {json_path}...")

    with open(json_path, "r") as f:
        data = json.load(f)

    supplies_data = data.get("supplies", {})
    bidders_data = data.get("bidders", {})

    async with session_factory() as session:
        added_bidders_count = 0
        bidder_objects = {}

        for bidder_id, bidder_info in bidders_data.items():
            # id is role name here
            existing_bidder = await bidder_dao.get(session, bidder_id)

            if existing_bidder:
                bidder_objects[bidder_id] = existing_bidder
                logger.info(f"Bidder {bidder_id} already exists, skipping")
            else:
                # not saved yet!!!
                bidder = await bidder_dao.create(
                    session,
                    obj_in=BidderCreate(id=bidder_id, country=bidder_info["country"]),
                    autocommit=False,
                )
                bidder_objects[bidder_id] = bidder
                added_bidders_count += 1
                logger.info(f"Added bidder {bidder_id} to current session.")

        # Save any bidders to db
        await session.flush()

        added_supplies_count = 0
        for supply_id, bidder_ids in supplies_data.items():
            existing_supply = await supply_dao.get(session, supply_id)
            bidders = [bidder_objects[bid_id] for bid_id in bidder_ids if bid_id in bidder_objects]

            if existing_supply:
                logger.info(f"Supply {supply_id} already exists, updating bidders")
                await supply_dao.update_with_bidders(session, existing_supply, bidders=bidders, autocommit=False)
            else:
                supply = await supply_dao.create(session, obj_in=SupplyCreate(id=supply_id), autocommit=False)
                await supply_dao.update_with_bidders(session, supply, bidders=bidders, autocommit=False)
                added_supplies_count += 1
                logger.info(f"Added supply {supply_id}")

        # commit!
        await session.commit()

    logger.info(f"Complete: {added_supplies_count=}, {added_bidders_count=}")

    return {
        "added_supplies_count": added_supplies_count,
        "added_bidders_count": added_bidders_count,
    }
