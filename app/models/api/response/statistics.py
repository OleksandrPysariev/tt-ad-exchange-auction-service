from pydantic import BaseModel


class BidderStats(BaseModel):
    wins: int = 0
    total_revenue: float = 0.0
    no_bids: int = 0
    timeouts: int = 0


class StatisticsResponse(BaseModel):
    total_reqs: int = 0
    reqs_per_country: dict[str, int] = {}
    bidders: dict[str, BidderStats] = {}

    class Config:
        json_schema_extra = {
            "example": {
                "supply1": {
                    "total_reqs": 10,
                    "reqs_per_country": {"US": 5, "GB": 5},
                    "bidders": {
                        "bidder1": {"wins": 2, "total_revenue": 0.4, "no_bids": 3, "timeouts": 1},
                        "bidder2": {"wins": 3, "total_revenue": 0.7, "no_bids": 1, "timeouts": 0},
                        "bidder3": {"wins": 0, "total_revenue": 0.0, "no_bids": 6, "timeouts": 2},
                    },
                }
            }
        }
