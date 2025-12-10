import json
import random
from pathlib import Path


COUNTRIES = ["US", "GB", "CA", "DE", "FR", "AU", "JP", "BR"]

SUPPLY_NAMES = [
    "cnn_mobile",
    "forbes_desktop",
    "espn_app",
    "nytimes_web",
    "reddit_mobile",
    "twitter_feed",
    "youtube_preroll",
    "spotify_audio",
    "twitch_video",
    "instagram_stories",
    "tiktok_infeed",
    "linkedin_feed",
    "weather_app",
    "news_aggregator",
    "gaming_portal",
    "tech_blog",
    "finance_hub",
    "lifestyle_magazine",
    "sports_network",
    "music_streaming",
]

BIDDER_NAMES = [
    "google_dv360",
    "amazon_dsp",
    "thetradedesk",
    "xandr",
    "verizon_media",
    "criteo",
    "mediamath",
    "adobe_adcloud",
    "pubmatic",
    "magnite",
    "openx",
    "index_exchange",
    "sovrn",
    "appnexus",
    "rubicon",
    "smartadserver",
    "tribalfusion",
    "undertone",
    "pulsepoint",
    "conversant",
]


def generate_auction_data(
    output_path: Path,
    num_supplies: int = 10,
    num_bidders: int = 12,
) -> dict[str, int]:
    """
    Generate auction data with supplies and bidders.

    Args:
        output_path: Path where to save the JSON file
        num_supplies: Number of supplies to generate
        num_bidders: Number of bidders to generate

    Returns:
        Dictionary with counts of generated entities
    """
    # Generate bidders with random countries
    bidders: dict[str, dict[str, str]] = {}
    selected_bidder_names = random.sample(BIDDER_NAMES, min(num_bidders, len(BIDDER_NAMES)))

    for bidder_name in selected_bidder_names:
        bidders[bidder_name] = {"country": random.choice(COUNTRIES)}

    # Generate supplies with random bidder assignments
    supplies: dict[str, list[str]] = {}
    selected_supply_names = random.sample(SUPPLY_NAMES, min(num_supplies, len(SUPPLY_NAMES)))
    all_bidder_ids = list(bidders.keys())

    for supply_name in selected_supply_names:
        # Each supply gets 2 to all bidders assigned randomly
        num_assigned = random.randint(2, len(all_bidder_ids))
        supplies[supply_name] = random.sample(all_bidder_ids, num_assigned)

    # Create the data structure
    data = {
        "supplies": supplies,
        "bidders": bidders,
    }

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    return {
        "supplies_count": len(supplies),
        "bidders_count": len(bidders),
    }
