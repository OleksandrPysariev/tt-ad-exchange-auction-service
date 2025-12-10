import logging
from pathlib import Path

from app.commands.generate_auction_data import generate_auction_data

logger = logging.getLogger(__name__)


def setup() -> None:
    """
    Setup function to ensure required data files exist.

    Checks if any JSON file exists in the current directory.
    If not, generates a default data.json file with auction data.
    """
    current_dir = Path.cwd()
    json_files = list(current_dir.glob("*.json"))

    if not json_files:
        logger.info("No JSON files found in current directory. Generating data.json...")
        output_path = current_dir / "data.json"

        result = generate_auction_data(
            output_path=output_path,
            num_supplies=10,
            num_bidders=12,
        )

        logger.info(
            f"Generated {output_path} with {result['supplies_count']} supplies "
            f"and {result['bidders_count']} bidders"
        )
    else:
        logger.info(f"Found existing JSON file(s): {[f.name for f in json_files]}")