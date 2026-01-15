"""Unit tests for rate limiter."""
import pytest
import asyncio
import time

from src.scraper.rate_limiter import RateLimiter


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_initialization_default_values(self):
        """Test rate limiter initializes with default values from config."""
        limiter = RateLimiter()
        assert limiter.min_delay == 2.0
        assert limiter.max_delay == 5.0
        assert limiter.last_request_time is None

    def test_initialization_custom_values(self):
        """Test rate limiter initializes with custom values."""
        limiter = RateLimiter(min_delay=1.0, max_delay=3.0)
        assert limiter.min_delay == 1.0
        assert limiter.max_delay == 3.0
        assert limiter.last_request_time is None

    def test_initialization_invalid_min_delay(self):
        """Test that negative min_delay raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            RateLimiter(min_delay=-1.0, max_delay=5.0)
        assert "non-negative" in str(exc_info.value)

    def test_initialization_invalid_max_delay(self):
        """Test that max_delay < min_delay raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            RateLimiter(min_delay=5.0, max_delay=2.0)
        assert "max_delay" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_first_wait_applies_delay(self):
        """Test that first wait applies delay."""
        limiter = RateLimiter(min_delay=0.1, max_delay=0.2)

        start_time = time.time()
        delay = await limiter.wait()
        elapsed = time.time() - start_time

        assert delay >= 0.1
        assert delay <= 0.2
        assert elapsed >= 0.1
        assert limiter.last_request_time is not None

    @pytest.mark.asyncio
    async def test_subsequent_wait_enforces_minimum_delay(self):
        """Test that subsequent waits enforce minimum delay."""
        limiter = RateLimiter(min_delay=0.2, max_delay=0.3)

        # First request
        await limiter.wait()

        # Second request immediately after
        start_time = time.time()
        await limiter.wait()
        elapsed = time.time() - start_time

        # Should wait approximately min_delay
        assert elapsed >= 0.15  # Allow small margin

    @pytest.mark.asyncio
    async def test_wait_returns_zero_if_enough_time_passed(self):
        """Test that wait returns 0 if enough time has already passed."""
        limiter = RateLimiter(min_delay=0.1, max_delay=0.2)

        # First request
        await limiter.wait()

        # Wait longer than max_delay
        await asyncio.sleep(0.3)

        # Second request should not wait
        delay = await limiter.wait()
        assert delay == 0.0

    @pytest.mark.asyncio
    async def test_multiple_requests_maintain_rate_limit(self):
        """Test that multiple requests maintain rate limit."""
        limiter = RateLimiter(min_delay=0.1, max_delay=0.15)

        start_time = time.time()

        # Make 5 requests
        for _ in range(5):
            await limiter.wait()

        total_time = time.time() - start_time

        # Should take at least 4 * min_delay (gaps between 5 requests)
        assert total_time >= 0.4

    @pytest.mark.asyncio
    async def test_reset_clears_last_request_time(self):
        """Test that reset clears last request time."""
        limiter = RateLimiter(min_delay=0.1, max_delay=0.2)

        await limiter.wait()
        assert limiter.last_request_time is not None

        limiter.reset()
        assert limiter.last_request_time is None

    @pytest.mark.asyncio
    async def test_reset_allows_immediate_new_session(self):
        """Test that reset allows starting new session immediately."""
        limiter = RateLimiter(min_delay=0.1, max_delay=0.2)

        await limiter.wait()
        await asyncio.sleep(0.05)  # Wait less than min_delay

        limiter.reset()

        # After reset, first wait should apply full delay
        start_time = time.time()
        await limiter.wait()
        elapsed = time.time() - start_time

        assert elapsed >= 0.1

    def test_get_time_since_last_request_none_initially(self):
        """Test that get_time_since_last_request returns None initially."""
        limiter = RateLimiter()
        assert limiter.get_time_since_last_request() is None

    @pytest.mark.asyncio
    async def test_get_time_since_last_request_returns_elapsed_time(self):
        """Test that get_time_since_last_request returns correct elapsed time."""
        limiter = RateLimiter(min_delay=0.1, max_delay=0.2)

        await limiter.wait()
        await asyncio.sleep(0.15)

        elapsed = limiter.get_time_since_last_request()
        assert elapsed is not None
        assert elapsed >= 0.15

    def test_repr(self):
        """Test string representation of rate limiter."""
        limiter = RateLimiter(min_delay=2.0, max_delay=5.0)
        repr_str = repr(limiter)

        assert "RateLimiter" in repr_str
        assert "2.0" in repr_str
        assert "5.0" in repr_str

    @pytest.mark.asyncio
    async def test_concurrent_waits_are_independent(self):
        """Test that multiple rate limiters work independently."""
        limiter1 = RateLimiter(min_delay=0.1, max_delay=0.15)
        limiter2 = RateLimiter(min_delay=0.2, max_delay=0.25)

        # Both start at same time
        start_time = time.time()

        await asyncio.gather(
            limiter1.wait(),
            limiter2.wait()
        )

        elapsed = time.time() - start_time

        # Should wait for the longer delay (limiter2)
        assert elapsed >= 0.2
