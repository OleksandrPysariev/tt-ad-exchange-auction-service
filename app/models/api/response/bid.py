from pydantic import BaseModel, Field


class BidResponse(BaseModel):
    winner: str = Field(description="Winning bidder ID")
    price: float = Field(description="Winning bid price")

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
