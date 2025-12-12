from pydantic import BaseModel, Field


class BidRequest(BaseModel):
    supply_id: str = Field(description="Supply ID for the auction")
    ip: str = Field(description="IP address of the requester")
    country: str = Field(description="Country code (e.g., US, GB)")
    tmax: int = Field(
        default=200,
        description="Maximum time in milliseconds for a bidder to respond during auction process",
        ge=1,
        le=5000,
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "supply_id": "supply1",
                    "ip": "123.45.67.89",
                    "country": "US",
                    "tmax": 200,
                }
            ]
        }
    }
