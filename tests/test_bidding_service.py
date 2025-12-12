import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.bidder import Bidder
from app.db.models.supply import Supply
from app.models.services.bidding import AuctionResult
from app.services.bidding import BiddingService
from app.services.statistics import StatisticsService


@pytest_asyncio.fixture
def mock_session():
    """Create a mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest_asyncio.fixture
def mock_statistics_service():
    """Create a mock statistics service."""
    service = AsyncMock(spec=StatisticsService)
    service.record_request = AsyncMock()
    service.record_auction_result = AsyncMock()
    return service


@pytest_asyncio.fixture
def bidding_service(mock_session, mock_statistics_service):
    """Create a BiddingService instance with mocked dependencies."""
    return BiddingService(mock_session, mock_statistics_service)


def create_mock_bidder(bidder_id: str, country: str) -> Bidder:
    """Helper to create a mock bidder."""
    bidder = MagicMock(spec=Bidder)
    bidder.id = bidder_id
    bidder.country = country
    return bidder


def create_mock_supply(supply_id: str, bidders: list[Bidder]) -> Supply:
    """Helper to create a mock supply."""
    supply = MagicMock(spec=Supply)
    supply.id = supply_id
    supply.bidders = bidders
    return supply


@pytest.mark.asyncio
async def test_run_auction_successful(bidding_service, mock_statistics_service):
    """Test successful auction with eligible bidders."""
    supply_id = "test_supply"
    country = "US"
    tmax = 200

    # Mock eligible bidders
    bidders = [
        create_mock_bidder("bidder1", "US"),
        create_mock_bidder("bidder2", "US"),
        create_mock_bidder("bidder3", "US"),
    ]

    # Mock supply exists
    mock_supply = create_mock_supply(supply_id, bidders)

    with patch("app.services.bidding.supply_dao") as mock_supply_dao, \
         patch("app.services.bidding.bidder_dao") as mock_bidder_dao, \
         patch("random.random", return_value=0.5), \
         patch("random.uniform", return_value=0.75), \
         patch("random.randint", return_value=50):  # Low latency, no timeouts

        mock_supply_dao.get = AsyncMock(return_value=mock_supply)
        mock_bidder_dao.get_eligible_for_supply = AsyncMock(return_value=bidders)

        # Run auction
        result = await bidding_service.run_auction(supply_id, country, tmax)

        # Assertions
        assert isinstance(result, AuctionResult)
        assert result.winner in ["bidder1", "bidder2", "bidder3"]
        assert 0.01 <= result.price <= 1.0

        # Verify statistics were recorded
        mock_statistics_service.record_request.assert_called_once_with(supply_id, country)
        mock_statistics_service.record_auction_result.assert_called_once()


@pytest.mark.asyncio
async def test_run_auction_supply_not_found(bidding_service, mock_statistics_service):
    """Test auction fails when supply doesn't exist."""
    supply_id = "nonexistent_supply"
    country = "US"

    with patch("app.services.bidding.supply_dao") as mock_supply_dao:
        mock_supply_dao.get = AsyncMock(return_value=None)

        # Should raise ValueError
        with pytest.raises(ValueError, match="Supply .* not found"):
            await bidding_service.run_auction(supply_id, country)

        # Statistics request should still be recorded
        mock_statistics_service.record_request.assert_called_once_with(supply_id, country)
        mock_statistics_service.record_auction_result.assert_not_called()


@pytest.mark.asyncio
async def test_run_auction_no_eligible_bidders(bidding_service, mock_statistics_service):
    """Test auction fails when no eligible bidders found."""
    supply_id = "test_supply"
    country = "US"

    mock_supply = create_mock_supply(supply_id, [])

    with patch("app.services.bidding.supply_dao") as mock_supply_dao, \
         patch("app.services.bidding.bidder_dao") as mock_bidder_dao:

        mock_supply_dao.get = AsyncMock(return_value=mock_supply)
        mock_bidder_dao.get_eligible_for_supply = AsyncMock(return_value=[])

        # Should raise ValueError
        with pytest.raises(ValueError, match="No eligible bidders found"):
            await bidding_service.run_auction(supply_id, country)

        # Statistics recorded
        mock_statistics_service.record_request.assert_called_once()
        mock_statistics_service.record_auction_result.assert_not_called()


@pytest.mark.asyncio
async def test_run_auction_all_bidders_skip(bidding_service, mock_statistics_service):
    """Test auction fails when all bidders skip (no bid)."""
    supply_id = "test_supply"
    country = "US"
    tmax = 200

    bidders = [
        create_mock_bidder("bidder1", "US"),
        create_mock_bidder("bidder2", "US"),
    ]

    mock_supply = create_mock_supply(supply_id, bidders)

    with patch("app.services.bidding.supply_dao") as mock_supply_dao, \
         patch("app.services.bidding.bidder_dao") as mock_bidder_dao, \
         patch("random.random", return_value=0.1), \
         patch("random.randint", return_value=50):  # All skip (< NO_BID_PROBABILITY)

        mock_supply_dao.get = AsyncMock(return_value=mock_supply)
        mock_bidder_dao.get_eligible_for_supply = AsyncMock(return_value=bidders)

        # Should raise ValueError
        with pytest.raises(ValueError, match="No bids received"):
            await bidding_service.run_auction(supply_id, country, tmax)

        # Statistics should record the failure
        mock_statistics_service.record_auction_result.assert_called_once()
        call_args = mock_statistics_service.record_auction_result.call_args
        assert call_args.kwargs["winner_id"] is None
        assert len(call_args.kwargs["no_bid_ids"]) == 2


@pytest.mark.asyncio
async def test_run_auction_with_timeouts(bidding_service, mock_statistics_service):
    """Test auction tracks bidder timeouts correctly."""
    supply_id = "test_supply"
    country = "US"
    tmax = 100  # 100ms timeout

    bidders = [
        create_mock_bidder("bidder1", "US"),  # Will timeout
        create_mock_bidder("bidder2", "US"),  # Will bid
        create_mock_bidder("bidder3", "US"),  # Will timeout
    ]

    mock_supply = create_mock_supply(supply_id, bidders)

    # Simulate latencies: bidder1=150ms (timeout), bidder2=50ms (ok), bidder3=120ms (timeout)
    latencies = [150, 50, 120]
    latency_index = [0]

    def mock_randint(min_val, max_val):
        idx = latency_index[0]
        latency_index[0] += 1
        return latencies[idx] if idx < len(latencies) else 50

    with patch("app.services.bidding.supply_dao") as mock_supply_dao, \
         patch("app.services.bidding.bidder_dao") as mock_bidder_dao, \
         patch("random.random", return_value=0.5), \
         patch("random.uniform", return_value=0.75), \
         patch("random.randint", side_effect=mock_randint), \
         patch("asyncio.sleep", new_callable=AsyncMock):

        mock_supply_dao.get = AsyncMock(return_value=mock_supply)
        mock_bidder_dao.get_eligible_for_supply = AsyncMock(return_value=bidders)

        # Run auction
        result = await bidding_service.run_auction(supply_id, country, tmax)

        # Only bidder2 should win (others timed out)
        assert result.winner == "bidder2"

        # Check statistics recorded timeouts
        call_args = mock_statistics_service.record_auction_result.call_args
        timeout_ids = call_args.kwargs["timeout_ids"]
        assert len(timeout_ids) == 2
        assert "bidder1" in timeout_ids
        assert "bidder3" in timeout_ids


@pytest.mark.asyncio
async def test_run_auction_highest_bid_wins(bidding_service, mock_statistics_service):
    """Test that the highest bid wins the auction."""
    supply_id = "test_supply"
    country = "US"
    tmax = 200

    bidders = [
        create_mock_bidder("bidder1", "US"),
        create_mock_bidder("bidder2", "US"),
        create_mock_bidder("bidder3", "US"),
    ]

    mock_supply = create_mock_supply(supply_id, bidders)

    # Set specific bid prices
    bid_prices = [0.25, 0.85, 0.50]
    price_index = [0]

    def mock_uniform(min_val, max_val):
        idx = price_index[0]
        price_index[0] += 1
        return bid_prices[idx] if idx < len(bid_prices) else 0.5

    with patch("app.services.bidding.supply_dao") as mock_supply_dao, \
         patch("app.services.bidding.bidder_dao") as mock_bidder_dao, \
         patch("random.random", return_value=0.5), \
         patch("random.uniform", side_effect=mock_uniform), \
         patch("random.randint", return_value=50):

        mock_supply_dao.get = AsyncMock(return_value=mock_supply)
        mock_bidder_dao.get_eligible_for_supply = AsyncMock(return_value=bidders)

        # Run auction
        result = await bidding_service.run_auction(supply_id, country, tmax)

        # Bidder2 should win with highest bid (0.85)
        assert result.winner == "bidder2"
        assert result.price == 0.85


@pytest.mark.asyncio
async def test_run_auction_mixed_outcomes(bidding_service, mock_statistics_service):
    """Test auction with mix of bids, no-bids, and timeouts."""
    supply_id = "test_supply"
    country = "US"
    tmax = 100

    bidders = [
        create_mock_bidder("bidder1", "US"),  # Will bid
        create_mock_bidder("bidder2", "US"),  # Will skip (no bid)
        create_mock_bidder("bidder3", "US"),  # Will timeout
        create_mock_bidder("bidder4", "US"),  # Will bid
    ]

    mock_supply = create_mock_supply(supply_id, bidders)

    # Control randomness
    random_values = [0.5, 0.1, 0.5, 0.5]  # bidder2 skips (0.1 < 0.3)
    random_index = [0]

    def mock_random():
        idx = random_index[0]
        random_index[0] += 1
        return random_values[idx] if idx < len(random_values) else 0.5

    latencies = [50, 50, 150, 50]  # bidder3 times out (150 > 100)
    latency_index = [0]

    def mock_randint(min_val, max_val):
        idx = latency_index[0]
        latency_index[0] += 1
        return latencies[idx] if idx < len(latencies) else 50

    with patch("app.services.bidding.supply_dao") as mock_supply_dao, \
         patch("app.services.bidding.bidder_dao") as mock_bidder_dao, \
         patch("random.random", side_effect=mock_random), \
         patch("random.uniform", return_value=0.75), \
         patch("random.randint", side_effect=mock_randint), \
         patch("asyncio.sleep", new_callable=AsyncMock):

        mock_supply_dao.get = AsyncMock(return_value=mock_supply)
        mock_bidder_dao.get_eligible_for_supply = AsyncMock(return_value=bidders)

        # Run auction
        result = await bidding_service.run_auction(supply_id, country, tmax)

        # Should have a winner (bidder1 or bidder4)
        assert result.winner in ["bidder1", "bidder4"]

        # Check statistics
        call_args = mock_statistics_service.record_auction_result.call_args
        no_bid_ids = call_args.kwargs["no_bid_ids"]
        timeout_ids = call_args.kwargs["timeout_ids"]

        assert "bidder2" in no_bid_ids  # Skipped
        assert "bidder3" in timeout_ids  # Timed out


@pytest.mark.asyncio
async def test_run_auction_default_tmax(bidding_service, mock_statistics_service):
    """Test auction uses default tmax when not specified."""
    supply_id = "test_supply"
    country = "US"

    bidders = [create_mock_bidder("bidder1", "US")]
    mock_supply = create_mock_supply(supply_id, bidders)

    with patch("app.services.bidding.supply_dao") as mock_supply_dao, \
         patch("app.services.bidding.bidder_dao") as mock_bidder_dao, \
         patch("random.random", return_value=0.5), \
         patch("random.uniform", return_value=0.75), \
         patch("random.randint", return_value=50):

        mock_supply_dao.get = AsyncMock(return_value=mock_supply)
        mock_bidder_dao.get_eligible_for_supply = AsyncMock(return_value=bidders)

        # Run auction without specifying tmax (should use default 200)
        result = await bidding_service.run_auction(supply_id, country)

        assert isinstance(result, AuctionResult)
        assert result.winner == "bidder1"


@pytest.mark.asyncio
async def test_run_auction_latency_simulation(bidding_service, mock_statistics_service):
    """Test that latency simulation is actually called."""
    supply_id = "test_supply"
    country = "US"
    tmax = 200

    bidders = [create_mock_bidder("bidder1", "US")]
    mock_supply = create_mock_supply(supply_id, bidders)

    with patch("app.services.bidding.supply_dao") as mock_supply_dao, \
         patch("app.services.bidding.bidder_dao") as mock_bidder_dao, \
         patch("random.random", return_value=0.5), \
         patch("random.uniform", return_value=0.75), \
         patch("random.randint", return_value=100), \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

        mock_supply_dao.get = AsyncMock(return_value=mock_supply)
        mock_bidder_dao.get_eligible_for_supply = AsyncMock(return_value=bidders)

        # Run auction
        await bidding_service.run_auction(supply_id, country, tmax)

        # Verify asyncio.sleep was called with correct latency (100ms = 0.1s)
        mock_sleep.assert_called_once_with(0.1)