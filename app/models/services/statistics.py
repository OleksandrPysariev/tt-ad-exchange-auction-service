from pydantic import BaseModel, Field


class StatisticsResult(BaseModel):
    """
    Raw statistics data returned from StatisticsService.get_all_statistics().

    Structure: dict[supply_id, redis_hash_data]

    Redis hash fields (all values stored as strings):
        - "total_reqs": Total auction requests (integer as string) - written by hincrby
        - "country:{code}": Requests per country (integer as string) - written by hincrby
            Examples: "country:US", "country:GB", "country:FR"
        - "bidder:{id}:wins": Bidder win count (integer as string) - written by hincrby
            Examples: "bidder:pulsepoint:wins", "bidder:rubicon:wins"
        - "bidder:{id}:revenue": Bidder total revenue (float as string) - written by hincrbyfloat
            Examples: "bidder:pulsepoint:revenue", "bidder:rubicon:revenue"
        - "bidder:{id}:no_bids": Bidder no-bid count (integer as string) - written by hincrby
            Examples: "bidder:pulsepoint:no_bids", "bidder:rubicon:no_bids"
        - "bidder:{id}:timeouts": Bidder timeout count (integer as string) - written by hincrby
            Examples: "bidder:pulsepoint:timeouts", "bidder:rubicon:timeouts"

    Example return value:
        {
            "finance_hub": {
                "total_reqs": "15",
                "country:US": "10",
                "country:GB": "5",
                "bidder:pulsepoint:wins": "3",
                "bidder:pulsepoint:revenue": "1.25",
                "bidder:pulsepoint:no_bids": "5",
                "bidder:pulsepoint:timeouts": "2",
                "bidder:rubicon:wins": "2",
                "bidder:rubicon:revenue": "0.80",
                "bidder:rubicon:no_bids": "8",
                "bidder:rubicon:timeouts": "1"
            }
        }
    """

    supplies: dict[str, dict[str, str]] = Field(
        description="Maps supply_id to Redis hash data (field_name -> string_value)",
    )
