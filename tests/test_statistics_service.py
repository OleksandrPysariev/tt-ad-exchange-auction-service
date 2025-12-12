import pytest
import pytest_asyncio
from redis.asyncio import StrictRedis

from app.config.settings import settings
from app.models.services.statistics import StatisticsResult
from app.services.statistics import StatisticsService


@pytest_asyncio.fixture
async def test_redis():
    """Create a fresh Redis client for each test."""
    redis = StrictRedis(
        host=settings.redis.startup_nodes[0].get("host"),
        port=settings.redis.startup_nodes[0].get("port"),
        decode_responses=True,
    )
    yield redis
    # Cleanup: clear all test keys
    await redis.flushdb()
    await redis.aclose()


@pytest_asyncio.fixture
async def statistics_service(test_redis):
    """Create StatisticsService instance for testing."""
    service = StatisticsService(test_redis)
    yield service


@pytest.mark.asyncio
async def test_record_request(statistics_service, test_redis):
    """Test recording auction requests."""
    supply_id = "test_supply"
    country = "US"

    # Record request
    await statistics_service.record_request(supply_id, country)

    # Verify data in Redis
    key = f"stats:{supply_id}"
    total_reqs = await test_redis.hget(key, "total_reqs")
    country_reqs = await test_redis.hget(key, f"country:{country}")

    assert total_reqs == "1"
    assert country_reqs == "1"


@pytest.mark.asyncio
async def test_record_multiple_requests(statistics_service, test_redis):
    """Test recording multiple requests increments counters."""
    supply_id = "test_supply"
    country = "US"

    # Record 5 requests
    for _ in range(5):
        await statistics_service.record_request(supply_id, country)

    # Verify counters
    key = f"stats:{supply_id}"
    total_reqs = await test_redis.hget(key, "total_reqs")
    country_reqs = await test_redis.hget(key, f"country:{country}")

    assert total_reqs == "5"
    assert country_reqs == "5"


@pytest.mark.asyncio
async def test_record_requests_multiple_countries(statistics_service, test_redis):
    """Test recording requests from different countries."""
    supply_id = "test_supply"

    # Record requests from different countries
    await statistics_service.record_request(supply_id, "US")
    await statistics_service.record_request(supply_id, "US")
    await statistics_service.record_request(supply_id, "GB")
    await statistics_service.record_request(supply_id, "FR")
    await statistics_service.record_request(supply_id, "GB")

    # Verify data
    key = f"stats:{supply_id}"
    total_reqs = await test_redis.hget(key, "total_reqs")
    us_reqs = await test_redis.hget(key, "country:US")
    gb_reqs = await test_redis.hget(key, "country:GB")
    fr_reqs = await test_redis.hget(key, "country:FR")

    assert total_reqs == "5"
    assert us_reqs == "2"
    assert gb_reqs == "2"
    assert fr_reqs == "1"


@pytest.mark.asyncio
async def test_record_auction_result_with_winner(statistics_service, test_redis):
    """Test recording auction result with a winner."""
    supply_id = "test_supply"
    winner_id = "bidder1"
    winning_price = 0.75
    no_bid_ids = ["bidder2"]
    timeout_ids = ["bidder3"]

    # Record auction result
    await statistics_service.record_auction_result(
        supply_id=supply_id,
        winner_id=winner_id,
        winning_price=winning_price,
        no_bid_ids=no_bid_ids,
        timeout_ids=timeout_ids,
    )

    # Verify data in Redis
    key = f"stats:{supply_id}"
    wins = await test_redis.hget(key, f"bidder:{winner_id}:wins")
    revenue = await test_redis.hget(key, f"bidder:{winner_id}:revenue")
    no_bids = await test_redis.hget(key, f"bidder:bidder2:no_bids")
    timeouts = await test_redis.hget(key, f"bidder:bidder3:timeouts")

    assert wins == "1"
    assert float(revenue) == 0.75
    assert no_bids == "1"
    assert timeouts == "1"


@pytest.mark.asyncio
async def test_record_auction_result_without_winner(statistics_service, test_redis):
    """Test recording auction result when all bidders skip/timeout."""
    supply_id = "test_supply"
    no_bid_ids = ["bidder1", "bidder2"]
    timeout_ids = ["bidder3"]

    # Record auction result with no winner
    await statistics_service.record_auction_result(
        supply_id=supply_id,
        winner_id=None,
        winning_price=0.0,
        no_bid_ids=no_bid_ids,
        timeout_ids=timeout_ids,
    )

    # Verify data in Redis
    key = f"stats:{supply_id}"
    no_bids_1 = await test_redis.hget(key, "bidder:bidder1:no_bids")
    no_bids_2 = await test_redis.hget(key, "bidder:bidder2:no_bids")
    timeouts = await test_redis.hget(key, "bidder:bidder3:timeouts")

    assert no_bids_1 == "1"
    assert no_bids_2 == "1"
    assert timeouts == "1"


@pytest.mark.asyncio
async def test_record_multiple_auction_results(statistics_service, test_redis):
    """Test recording multiple auction results accumulates statistics."""
    supply_id = "test_supply"

    # Auction 1: bidder1 wins
    await statistics_service.record_auction_result(
        supply_id=supply_id,
        winner_id="bidder1",
        winning_price=0.50,
        no_bid_ids=["bidder2"],
        timeout_ids=[],
    )

    # Auction 2: bidder1 wins again
    await statistics_service.record_auction_result(
        supply_id=supply_id,
        winner_id="bidder1",
        winning_price=0.30,
        no_bid_ids=[],
        timeout_ids=["bidder2"],
    )

    # Auction 3: bidder3 wins
    await statistics_service.record_auction_result(
        supply_id=supply_id,
        winner_id="bidder3",
        winning_price=0.80,
        no_bid_ids=["bidder1"],
        timeout_ids=[],
    )

    # Verify accumulated statistics
    key = f"stats:{supply_id}"
    bidder1_wins = await test_redis.hget(key, "bidder:bidder1:wins")
    bidder1_revenue = await test_redis.hget(key, "bidder:bidder1:revenue")
    bidder1_no_bids = await test_redis.hget(key, "bidder:bidder1:no_bids")
    bidder2_no_bids = await test_redis.hget(key, "bidder:bidder2:no_bids")
    bidder2_timeouts = await test_redis.hget(key, "bidder:bidder2:timeouts")
    bidder3_wins = await test_redis.hget(key, "bidder:bidder3:wins")
    bidder3_revenue = await test_redis.hget(key, "bidder:bidder3:revenue")

    assert bidder1_wins == "2"
    assert float(bidder1_revenue) == 0.80  # 0.50 + 0.30
    assert bidder1_no_bids == "1"
    assert bidder2_no_bids == "1"
    assert bidder2_timeouts == "1"
    assert bidder3_wins == "1"
    assert float(bidder3_revenue) == 0.80


@pytest.mark.asyncio
async def test_get_all_statistics_empty(statistics_service):
    """Test getting statistics when no data exists."""
    result = await statistics_service.get_all_statistics()

    assert result is None


@pytest.mark.asyncio
async def test_get_all_statistics_single_supply(statistics_service, test_redis):
    """Test retrieving statistics for a single supply."""
    supply_id = "test_supply"

    # Record some data
    await statistics_service.record_request(supply_id, "US")
    await statistics_service.record_request(supply_id, "GB")
    await statistics_service.record_auction_result(
        supply_id=supply_id,
        winner_id="bidder1",
        winning_price=0.75,
        no_bid_ids=["bidder2"],
        timeout_ids=["bidder3"],
    )

    # Get statistics
    result = await statistics_service.get_all_statistics()

    assert isinstance(result, StatisticsResult)
    assert supply_id in result.supplies

    supply_data = result.supplies[supply_id]
    assert supply_data["total_reqs"] == "2"
    assert supply_data["country:US"] == "1"
    assert supply_data["country:GB"] == "1"
    assert supply_data["bidder:bidder1:wins"] == "1"
    assert supply_data["bidder:bidder1:revenue"] == "0.75"
    assert supply_data["bidder:bidder2:no_bids"] == "1"
    assert supply_data["bidder:bidder3:timeouts"] == "1"


@pytest.mark.asyncio
async def test_get_all_statistics_multiple_supplies(statistics_service, test_redis):
    """Test retrieving statistics for multiple supplies."""
    # Record data for supply1
    await statistics_service.record_request("supply1", "US")
    await statistics_service.record_auction_result(
        supply_id="supply1",
        winner_id="bidder1",
        winning_price=0.50,
        no_bid_ids=[],
        timeout_ids=[],
    )

    # Record data for supply2
    await statistics_service.record_request("supply2", "GB")
    await statistics_service.record_request("supply2", "FR")
    await statistics_service.record_auction_result(
        supply_id="supply2",
        winner_id="bidder2",
        winning_price=0.85,
        no_bid_ids=["bidder1"],
        timeout_ids=[],
    )

    # Get all statistics
    result = await statistics_service.get_all_statistics()

    assert isinstance(result, StatisticsResult)
    assert len(result.supplies) == 2
    assert "supply1" in result.supplies
    assert "supply2" in result.supplies

    # Verify supply1 data
    supply1_data = result.supplies["supply1"]
    assert supply1_data["total_reqs"] == "1"
    assert supply1_data["country:US"] == "1"
    assert supply1_data["bidder:bidder1:wins"] == "1"

    # Verify supply2 data
    supply2_data = result.supplies["supply2"]
    assert supply2_data["total_reqs"] == "2"
    assert supply2_data["country:GB"] == "1"
    assert supply2_data["country:FR"] == "1"
    assert supply2_data["bidder:bidder2:wins"] == "1"


@pytest.mark.asyncio
async def test_revenue_accumulation_precision(statistics_service, test_redis):
    """Test that revenue accumulation maintains precision with floats."""
    supply_id = "test_supply"

    # Record multiple small revenues
    await statistics_service.record_auction_result(
        supply_id=supply_id,
        winner_id="bidder1",
        winning_price=0.33,
        no_bid_ids=[],
        timeout_ids=[],
    )
    await statistics_service.record_auction_result(
        supply_id=supply_id,
        winner_id="bidder1",
        winning_price=0.27,
        no_bid_ids=[],
        timeout_ids=[],
    )
    await statistics_service.record_auction_result(
        supply_id=supply_id,
        winner_id="bidder1",
        winning_price=0.15,
        no_bid_ids=[],
        timeout_ids=[],
    )

    # Get revenue
    key = f"stats:{supply_id}"
    revenue = await test_redis.hget(key, "bidder:bidder1:revenue")

    # Should be 0.75 (0.33 + 0.27 + 0.15)
    assert float(revenue) == pytest.approx(0.75, rel=1e-5)


@pytest.mark.asyncio
async def test_statistics_key_format(statistics_service, test_redis):
    """Test that Redis keys follow the correct format."""
    supply_id = "test_supply_123"

    await statistics_service.record_request(supply_id, "US")

    # Check key exists with correct format
    expected_key = f"stats:{supply_id}"
    exists = await test_redis.exists(expected_key)
    assert exists == 1


@pytest.mark.asyncio
async def test_timeout_tracking_only(statistics_service, test_redis):
    """Test recording only timeouts without winner."""
    supply_id = "test_supply"
    timeout_ids = ["bidder1", "bidder2", "bidder3"]

    await statistics_service.record_auction_result(
        supply_id=supply_id,
        winner_id=None,
        winning_price=0.0,
        no_bid_ids=[],
        timeout_ids=timeout_ids,
    )

    # Verify timeouts are recorded
    key = f"stats:{supply_id}"
    for bidder_id in timeout_ids:
        timeouts = await test_redis.hget(key, f"bidder:{bidder_id}:timeouts")
        assert timeouts == "1"


@pytest.mark.asyncio
async def test_no_bid_tracking_only(statistics_service, test_redis):
    """Test recording only no-bids without winner."""
    supply_id = "test_supply"
    no_bid_ids = ["bidder1", "bidder2"]

    await statistics_service.record_auction_result(
        supply_id=supply_id,
        winner_id=None,
        winning_price=0.0,
        no_bid_ids=no_bid_ids,
        timeout_ids=[],
    )

    # Verify no-bids are recorded
    key = f"stats:{supply_id}"
    for bidder_id in no_bid_ids:
        no_bids = await test_redis.hget(key, f"bidder:{bidder_id}:no_bids")
        assert no_bids == "1"


@pytest.mark.asyncio
async def test_pipeline_efficiency(statistics_service, test_redis):
    """Test that operations use Redis pipeline for efficiency."""
    supply_id = "test_supply"

    # Record complex auction result
    await statistics_service.record_auction_result(
        supply_id=supply_id,
        winner_id="winner",
        winning_price=0.75,
        no_bid_ids=["bidder1", "bidder2", "bidder3"],
        timeout_ids=["bidder4", "bidder5"],
    )

    # Verify all data was written (pipeline should execute all at once)
    key = f"stats:{supply_id}"
    data = await test_redis.hgetall(key)

    assert "bidder:winner:wins" in data
    assert "bidder:winner:revenue" in data
    assert "bidder:bidder1:no_bids" in data
    assert "bidder:bidder2:no_bids" in data
    assert "bidder:bidder3:no_bids" in data
    assert "bidder:bidder4:timeouts" in data
    assert "bidder:bidder5:timeouts" in data


@pytest.mark.asyncio
async def test_get_statistics_returns_all_fields(statistics_service, test_redis):
    """Test that get_all_statistics returns complete data structure."""
    supply_id = "complete_supply"

    # Create comprehensive statistics
    await statistics_service.record_request(supply_id, "US")
    await statistics_service.record_request(supply_id, "GB")
    await statistics_service.record_auction_result(
        supply_id=supply_id,
        winner_id="bidder1",
        winning_price=0.65,
        no_bid_ids=["bidder2"],
        timeout_ids=["bidder3"],
    )

    # Retrieve statistics
    result = await statistics_service.get_all_statistics()

    # Verify structure
    assert result is not None
    assert isinstance(result, StatisticsResult)
    assert isinstance(result.supplies, dict)
    assert supply_id in result.supplies

    supply_data = result.supplies[supply_id]
    assert isinstance(supply_data, dict)

    # All values should be strings (Redis stores everything as strings)
    for key, value in supply_data.items():
        assert isinstance(key, str)
        assert isinstance(value, str)