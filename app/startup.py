import logging

from app.commands.generate_auction_data import generate_auction_data
from app.commands.load_data import load_json_to_db
from app.config.settings import settings

logger = logging.getLogger(__name__)


async def setup() -> None:
    """
    Setup function to ensure auction data file exist.
    """
    data_file_path = settings.general.data_file_path

    if not data_file_path.exists():
        logger.info(f"Data file not found at {data_file_path}. Generating...")

        result = generate_auction_data(
            output_path=data_file_path,
            num_supplies=10,
            num_bidders=12,
        )

        logger.info(
            f"Generated {data_file_path} with {result['supplies_count']} supplies "
            f"and {result['bidders_count']} bidders"
        )
    else:
        logger.info(f"Found existing data file: {data_file_path}")

    logger.info(f"Loading {data_file_path} to db.")

    load_result = await load_json_to_db(data_file_path)

    logger.info(f"Load successful. {load_result=}")

