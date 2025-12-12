from app.builders.base import BaseBuilder
from app.models.api.response.bid import BidResponse
from app.models.services.bidding import AuctionResult


class BiddingResponseBuilder(BaseBuilder):
    @classmethod
    def build(cls, auction_result: AuctionResult, *args, **kwargs) -> BidResponse:
        return BidResponse(
            winner=auction_result.winner,
            price=auction_result.price,
        )
