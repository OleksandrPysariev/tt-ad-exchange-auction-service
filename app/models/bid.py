from pydantic import BaseModel, Field


class BidRequest(BaseModel):
    supply_id: str = Field(..., description="Supply ID for the auction")
    ip: str = Field(..., description="IP address of the requester")
    country: str = Field(..., description="Country code (e.g., US, GB)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "supply_id": "supply1",
                    "ip": "123.45.67.89",
                    "country": "US",
                }
            ]
        }
    }


class BidResponse(BaseModel):
    winner: str = Field(..., description="Winning bidder ID")
    price: float = Field(..., description="Winning bid price")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "winner": "bidder2",
                    "price": 0.83,
                }
            ]
        }
    }
