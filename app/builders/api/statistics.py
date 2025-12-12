from collections import defaultdict

from app.builders.base import BaseBuilder
from app.models.api.response.statistics import BidderStats, StatisticsResponse
from app.models.services.statistics import StatisticsResult


class StatisticsResponseBuilder(BaseBuilder):
    @classmethod
    def build(cls, statistics_result: StatisticsResult | None = None, *args, **kwargs) -> dict[str, StatisticsResponse]:
        response: dict[str, StatisticsResponse] = {}

        if not statistics_result:
            return {}

        for supply_id, redis_data in statistics_result.supplies.items():
            response[supply_id] = cls._parse_supply_data(redis_data)

        return response

    @classmethod
    def _parse_supply_data(cls, redis_data: dict[str, str]) -> StatisticsResponse:
        total_reqs = int(redis_data.get("total_reqs", 0))

        reqs_per_country: dict[str, int] = {}
        bidders_data: dict[str, dict[str, float | int]] = defaultdict(dict)

        for field, value in redis_data.items():
            if field.startswith("country:"):
                country = field.split(":", 1)[1]
                reqs_per_country[country] = int(value)

            elif field.startswith("bidder:"):
                parts = field.split(":")
                bidder_id = parts[1]
                metric = parts[2]

                # Store as float for revenue, int for others
                if metric == "revenue":
                    bidders_data[bidder_id][metric] = float(value)
                else:
                    bidders_data[bidder_id][metric] = int(value)

        bidders: dict[str, BidderStats] = {}
        for bidder_id, metrics in bidders_data.items():
            bidders[bidder_id] = BidderStats(
                wins=int(metrics.get("wins", 0)),
                total_revenue=round(float(metrics.get("revenue", 0.0)), 2),
                no_bids=int(metrics.get("no_bids", 0)),
                timeouts=int(metrics.get("timeouts", 0)),
            )

        return StatisticsResponse(
            total_reqs=total_reqs,
            reqs_per_country=reqs_per_country,
            bidders=bidders,
        )
