"""Rate limiter for human-like scraping behavior.

Implements delays between requests to avoid being blocked by websites
and to behave like a responsible web scraper.
"""
import asyncio
import time
import random
from typing import Optional

from src.config import settings, get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter with configurable delay for human-like scraping.

    Ensures minimum delay between requests to avoid overwhelming servers
    and to mimic human browsing patterns.

    Attributes:
        min_delay: Minimum delay in seconds between requests
        max_delay: Maximum delay in seconds between requests
        last_request_time: Timestamp of last request (Unix time)
    """

    def __init__(
        self,
        min_delay: Optional[float] = None,
        max_delay: Optional[float] = None
    ):
        """Initialize rate limiter with configurable delays.

        Args:
            min_delay: Minimum delay in seconds (default from config)
            max_delay: Maximum delay in seconds (default from config)
        """
        self.min_delay = min_delay if min_delay is not None else settings.rate_limit_min
        self.max_delay = max_delay if max_delay is not None else settings.rate_limit_max
        self.last_request_time: Optional[float] = None

        if self.min_delay < 0:
            raise ValueError("min_delay must be non-negative")
        if self.max_delay < self.min_delay:
            raise ValueError("max_delay must be >= min_delay")

        logger.info(
            "Rate limiter initialized",
            min_delay=self.min_delay,
            max_delay=self.max_delay
        )

    async def wait(self) -> float:
        """Wait appropriate amount of time before next request.

        Calculates time since last request and sleeps if needed to maintain
        minimum delay. Uses random delay within range for human-like behavior.

        Returns:
            float: Actual delay applied in seconds

        Example:
            >>> limiter = RateLimiter(min_delay=2.0, max_delay=5.0)
            >>> await limiter.wait()  # Waits 2-5 seconds
            3.2
        """
        current_time = time.time()

        # Calculate random delay for this request
        target_delay = random.uniform(self.min_delay, self.max_delay)

        # If this is first request, just wait the target delay
        if self.last_request_time is None:
            logger.debug("First request, applying initial delay", delay=target_delay)
            await asyncio.sleep(target_delay)
            self.last_request_time = time.time()
            return target_delay

        # Calculate time since last request
        time_since_last = current_time - self.last_request_time

        # If enough time has passed, no need to wait
        if time_since_last >= target_delay:
            logger.debug(
                "Sufficient time passed since last request",
                time_since_last=time_since_last,
                target_delay=target_delay
            )
            self.last_request_time = current_time
            return 0.0

        # Calculate remaining wait time
        remaining_wait = target_delay - time_since_last

        logger.info(
            "Rate limiting: waiting before next request",
            time_since_last=time_since_last,
            remaining_wait=remaining_wait,
            target_delay=target_delay
        )

        await asyncio.sleep(remaining_wait)
        self.last_request_time = time.time()
        return remaining_wait

    def reset(self) -> None:
        """Reset rate limiter state.

        Clears last request time, useful for starting fresh scraping session.
        """
        logger.debug("Rate limiter reset")
        self.last_request_time = None

    def get_time_since_last_request(self) -> Optional[float]:
        """Get time elapsed since last request.

        Returns:
            Optional[float]: Seconds since last request, or None if no requests yet
        """
        if self.last_request_time is None:
            return None
        return time.time() - self.last_request_time

    def __repr__(self) -> str:
        """String representation of rate limiter."""
        return (
            f"RateLimiter(min_delay={self.min_delay}, max_delay={self.max_delay}, "
            f"last_request={self.last_request_time})"
        )
