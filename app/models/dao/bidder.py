from pydantic import BaseModel, Field


class BidderCreate(BaseModel):
    id: str = Field(description="Unique string name of the Bidder.")
    country: str = Field(max_length=2, description="Two-letter country code.")


class BidderUpdate(BaseModel):
    country: str = Field(max_length=2, description="Two-letter country code.")
