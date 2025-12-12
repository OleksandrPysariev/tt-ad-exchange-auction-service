import asyncio

import pytest
import pytest_asyncio
from redis.asyncio import StrictRedis

from app.config.settings import settings
from app.services.rate_limiter import RedisRateLimiter


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
async def rate_limiter(test_redis):
    """Create rate limiter instance for testing."""
    limiter = RedisRateLimiter(
        redis_client=test_redis,
        max_requests=3,
        window_seconds=60,
    )
    yield limiter


@pytest.mark.asyncio
async def test_rate_limiter_allows_requests_under_limit(rate_limiter: RedisRateLimiter) -> None:
    """Test that requests under the limit are allowed."""
    test_ip = "192.168.1.1"

    # First 3 requests should be allowed
    for i in range(3):
        is_allowed = await rate_limiter.is_allowed(test_ip)
        assert is_allowed is True, f"Request {i+1} should be allowed"

    # 4th request should be blocked
    is_allowed = await rate_limiter.is_allowed(test_ip)
    assert is_allowed is False, "4th request should be blocked"


@pytest.mark.asyncio
async def test_rate_limiter_blocks_requests_over_limit(rate_limiter: RedisRateLimiter) -> None:
    """Test that requests exceeding the limit are blocked."""
    test_ip = "192.168.1.2"

    # Make 3 requests (all should pass)
    for _ in range(3):
        is_allowed = await rate_limiter.is_allowed(test_ip)
        assert is_allowed is True

    # Next 5 requests should be blocked
    for i in range(5):
        is_allowed = await rate_limiter.is_allowed(test_ip)
        assert is_allowed is False, f"Request {i+4} should be blocked"


@pytest.mark.asyncio
async def test_rate_limiter_sliding_window(test_redis) -> None:
    """Test that sliding window properly expires old requests."""
    # Create limiter with short window for testing
    test_limiter = RedisRateLimiter(
        redis_client=test_redis,
        max_requests=3,
        window_seconds=2,  # 2 second window for faster testing
    )
    test_ip = "192.168.1.3"

    # Make 3 requests
    for i in range(3):
        is_allowed = await test_limiter.is_allowed(test_ip)
        assert is_allowed is True, f"Request {i+1} should be allowed"

    # 4th request should be blocked
    is_allowed = await test_limiter.is_allowed(test_ip)
    assert is_allowed is False, "4th request should be blocked"

    # Wait for window to expire
    await asyncio.sleep(2.1)

    # After window expires, request should be allowed again
    is_allowed = await test_limiter.is_allowed(test_ip)
    assert is_allowed is True, "Request should be allowed after window expiration"


@pytest.mark.asyncio
async def test_rate_limiter_multiple_ips(rate_limiter: RedisRateLimiter) -> None:
    """Test that rate limits are independent per IP."""
    ip1 = "192.168.1.4"
    ip2 = "192.168.1.5"

    # IP1: Make 3 requests
    for i in range(3):
        is_allowed = await rate_limiter.is_allowed(ip1)
        assert is_allowed is True, f"IP1 request {i+1} should be allowed"

    # IP1 should be blocked
    is_allowed = await rate_limiter.is_allowed(ip1)
    assert is_allowed is False, "IP1 should be blocked"

    # IP2 should still be allowed
    for i in range(3):
        is_allowed = await rate_limiter.is_allowed(ip2)
        assert is_allowed is True, f"IP2 request {i+1} should be allowed"

    # IP2 should now be blocked too
    is_allowed = await rate_limiter.is_allowed(ip2)
    assert is_allowed is False, "IP2 should be blocked"


@pytest.mark.asyncio
async def test_rate_limiter_no_burst_at_boundary(test_redis) -> None:
    """
    Test that sliding window prevents burst at window boundaries.

    This is the key advantage over fixed window counter.
    """
    # Create limiter with short window
    test_limiter = RedisRateLimiter(
        redis_client=test_redis,
        max_requests=3,
        window_seconds=1,
    )
    test_ip = "192.168.1.7"

    # Make 3 requests at time T
    for _ in range(3):
        is_allowed = await test_limiter.is_allowed(test_ip)
        assert is_allowed is True

    # Wait 0.5 seconds (still within window)
    await asyncio.sleep(0.5)

    # Should still be blocked (sliding window)
    is_allowed = await test_limiter.is_allowed(test_ip)
    assert is_allowed is False, "Should be blocked within sliding window"

    # Wait another 0.6 seconds (total 1.1s, first requests expired)
    await asyncio.sleep(0.6)

    # Now should be allowed
    is_allowed = await test_limiter.is_allowed(test_ip)
    assert is_allowed is True, "Should be allowed after window expiration"


@pytest.mark.asyncio
async def test_rate_limiter_partial_window_expiry(test_redis) -> None:
    """Test that only expired requests are removed, not all requests."""
    # Create limiter with short window
    test_limiter = RedisRateLimiter(
        redis_client=test_redis,
        max_requests=3,
        window_seconds=2,
    )
    test_ip = "192.168.1.8"

    # Request 1 at T=0
    is_allowed = await test_limiter.is_allowed(test_ip)
    assert is_allowed is True

    # Wait 1 second
    await asyncio.sleep(1)

    # Request 2 and 3 at T=1
    for _ in range(2):
        is_allowed = await test_limiter.is_allowed(test_ip)
        assert is_allowed is True

    # Should be blocked now (3 requests in window)
    is_allowed = await test_limiter.is_allowed(test_ip)
    assert is_allowed is False

    # Wait 1.1 more seconds (T=2.1, request 1 expired but 2 and 3 still valid)
    await asyncio.sleep(1.1)

    # Should be allowed (only 2 requests in last 2 seconds)
    is_allowed = await test_limiter.is_allowed(test_ip)
    assert is_allowed is True


@pytest.mark.asyncio
async def test_rate_limiter_key_format(test_redis) -> None:
    """Test that Redis key format is correct."""
    test_ip = "192.168.1.9"
    expected_key = f"rate_limit:{test_ip}"

    # Create rate limiter and make a request to create the key
    limiter = RedisRateLimiter(redis_client=test_redis, max_requests=3, window_seconds=60)
    await limiter.is_allowed(test_ip)

    # Check if key exists in Redis
    key_exists = await test_redis.exists(expected_key)
    assert key_exists == 1, f"Expected key {expected_key} to exist in Redis"


@pytest.mark.asyncio
async def test_rate_limiter_ttl_set(test_redis) -> None:
    """Test that TTL is properly set on Redis keys."""
    test_ip = "192.168.1.10"
    key = f"rate_limit:{test_ip}"

    # Create rate limiter and make a request
    limiter = RedisRateLimiter(redis_client=test_redis, max_requests=3, window_seconds=60)
    await limiter.is_allowed(test_ip)

    # Check TTL is set
    ttl = await test_redis.ttl(key)
    assert ttl > 0, "TTL should be set on the key"
    assert ttl <= 70, f"TTL should be <= 70 seconds, got {ttl}"


@pytest.mark.asyncio
async def test_rate_limiter_accurate_sliding_window(test_redis) -> None:
    """
    Test accurate sliding window behavior with precise timing.

    Demonstrates that the limiter enforces limits over ANY 60-second period,
    not just fixed windows.
    """
    test_limiter = RedisRateLimiter(
        redis_client=test_redis,
        max_requests=3,
        window_seconds=3,  # 3 second window
    )
    test_ip = "192.168.1.11"

    # T=0: 3 requests
    for _ in range(3):
        assert await test_limiter.is_allowed(test_ip) is True

    # T=0: Should be blocked
    assert await test_limiter.is_allowed(test_ip) is False

    # T=1: Still blocked (3 requests in last 3 seconds)
    await asyncio.sleep(1)
    assert await test_limiter.is_allowed(test_ip) is False

    # T=2: Still blocked
    await asyncio.sleep(1)
    assert await test_limiter.is_allowed(test_ip) is False

    # T=3.1: First request expired, should be allowed
    await asyncio.sleep(1.1)
    assert await test_limiter.is_allowed(test_ip) is True

    # Cleanup
    await test_redis.delete(f"rate_limit:{test_ip}")
