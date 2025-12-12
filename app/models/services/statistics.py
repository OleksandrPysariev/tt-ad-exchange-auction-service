from pydantic import BaseModel, Field


class StatisticsResult(BaseModel):
    """
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
