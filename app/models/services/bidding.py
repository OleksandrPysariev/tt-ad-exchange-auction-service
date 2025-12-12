from pydantic import BaseModel, Field


class AuctionResult(BaseModel):
    winner: str = Field(description="Winning bidder ID")
    price: float = Field(description="Winning bid price")
