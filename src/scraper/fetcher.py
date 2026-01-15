"""HTML fetcher using Playwright for JavaScript-heavy pages."""
import asyncio
from typing import Optional, List
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout

from src.config import settings, get_logger
from src.scraper.rate_limiter import RateLimiter

logger = get_logger(__name__)

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]


class FetchError(Exception):
    """Raised when fetching a page fails."""
    pass


class HTMLFetcher:
    """Fetches HTML content using Playwright browser automation.

    Handles JavaScript-heavy sites and implements retry logic with
    exponential backoff.
    """

    def __init__(self, rate_limiter: Optional[RateLimiter] = None):
        """Initialize HTML fetcher.

        Args:
            rate_limiter: Rate limiter instance (creates default if None)
        """
        self.rate_limiter = rate_limiter or RateLimiter()
        self.browser: Optional[Browser] = None
        self._playwright = None
        self._user_agent_index = 0

        logger.info("HTML fetcher initialized")

    async def _get_next_user_agent(self) -> str:
        """Get next user agent from rotation list.

        Returns:
            str: User agent string
        """
        user_agent = USER_AGENTS[self._user_agent_index]
        self._user_agent_index = (self._user_agent_index + 1) % len(USER_AGENTS)
        return user_agent

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self) -> None:
        """Start Playwright browser instance."""
        if self.browser is not None:
            logger.warning("Browser already started")
            return

        logger.info("Starting Playwright browser")
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        logger.info("Playwright browser started successfully")

    async def close(self) -> None:
        """Close Playwright browser instance."""
        if self.browser:
            await self.browser.close()
            self.browser = None
            logger.info("Playwright browser closed")

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def fetch_page(
        self,
        url: str,
        max_retries: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> str:
        """Fetch HTML content from URL with retry logic.

        Args:
            url: URL to fetch
            max_retries: Maximum retry attempts (default from config)
            timeout: Timeout in seconds (default from config)

        Returns:
            str: HTML content

        Raises:
            FetchError: If fetching fails after all retries
        """
        if self.browser is None:
            raise RuntimeError("Browser not started. Call start() or use async context manager")

        max_retries = max_retries if max_retries is not None else settings.max_retries
        timeout = (timeout if timeout is not None else settings.request_timeout) * 1000  # Convert to ms

        last_error: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            try:
                # Apply rate limiting
                await self.rate_limiter.wait()

                # Get user agent for this request
                user_agent = await self._get_next_user_agent()

                logger.info(
                    "Fetching page",
                    url=url,
                    attempt=attempt + 1,
                    max_retries=max_retries + 1,
                    user_agent=user_agent[:50]
                )

                # Create new page with custom user agent
                page = await self.browser.new_page(user_agent=user_agent)

                try:
                    # Navigate to URL
                    response = await page.goto(
                        url,
                        timeout=timeout,
                        wait_until="networkidle"
                    )

                    # Check if response is successful
                    if response and response.status >= 400:
                        raise FetchError(f"HTTP {response.status}: {response.status_text}")

                    # Get page content
                    html = await page.content()

                    logger.info(
                        "Page fetched successfully",
                        url=url,
                        html_length=len(html),
                        status=response.status if response else None
                    )

                    return html

                finally:
                    await page.close()

            except PlaywrightTimeout as e:
                last_error = e
                logger.warning(
                    "Fetch timeout",
                    url=url,
                    attempt=attempt + 1,
                    error=str(e)
                )

            except Exception as e:
                last_error = e
                logger.warning(
                    "Fetch error",
                    url=url,
                    attempt=attempt + 1,
                    error=str(e),
                    error_type=type(e).__name__
                )

            # Exponential backoff before retry
            if attempt < max_retries:
                backoff_delay = 2 ** attempt  # 1s, 2s, 4s, ...
                logger.info(f"Retrying after {backoff_delay}s backoff", url=url)
                await asyncio.sleep(backoff_delay)

        # All retries exhausted
        error_msg = f"Failed to fetch {url} after {max_retries + 1} attempts: {str(last_error)}"
        logger.error("Fetch failed after all retries", url=url, error=str(last_error))
        raise FetchError(error_msg)
