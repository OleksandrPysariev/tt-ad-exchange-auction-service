from pydantic import BaseModel, Field


class SupplyResponse(BaseModel):
    id: str = Field(description="Supply ID")

    class Config:
        from_attributes = True
