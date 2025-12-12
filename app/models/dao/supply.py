from pydantic import BaseModel, Field


class SupplyCreate(BaseModel):
    id: str = Field(description="Unique string name of the Supply.")
    bidders: list[str] = Field(default_factory=list, description="List of bidder IDs associated with this supply.")


class SupplyUpdate(BaseModel):
    bidders: list[str] = Field(default_factory=list, description="List of bidder IDs to associate with this supply.")

