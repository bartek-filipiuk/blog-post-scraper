"""Tests for HTML fetcher."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.scraper.fetcher import HTMLFetcher, FetchError
from src.scraper.rate_limiter import RateLimiter


class TestHTMLFetcher:
    """Tests for HTMLFetcher class."""

    def test_initialization(self):
        """Test fetcher initializes correctly."""
        fetcher = HTMLFetcher()
        assert fetcher.browser is None
        assert fetcher.rate_limiter is not None

    def test_initialization_with_custom_rate_limiter(self):
        """Test fetcher accepts custom rate limiter."""
        custom_limiter = RateLimiter(min_delay=1.0, max_delay=2.0)
        fetcher = HTMLFetcher(rate_limiter=custom_limiter)
        assert fetcher.rate_limiter == custom_limiter

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test fetcher works as async context manager."""
        with patch('src.scraper.fetcher.async_playwright') as mock_playwright:
            mock_pw = AsyncMock()
            mock_browser = AsyncMock()
            mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw)

            async with HTMLFetcher() as fetcher:
                assert fetcher.browser is not None

    @pytest.mark.asyncio
    async def test_fetch_page_requires_started_browser(self):
        """Test that fetch_page raises error if browser not started."""
        fetcher = HTMLFetcher()

        with pytest.raises(RuntimeError) as exc_info:
            await fetcher.fetch_page("https://example.com")

        assert "not started" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_user_agent_rotation(self):
        """Test that user agent rotates through list."""
        fetcher = HTMLFetcher()

        # Get all unique user agents
        user_agents = []
        for _ in range(10):
            ua = await fetcher._get_next_user_agent()
            if ua not in user_agents:
                user_agents.append(ua)

        # Should have multiple user agents
        assert len(user_agents) >= 3

        # After enough cycles, should see repeats
        ua_first = await fetcher._get_next_user_agent()
        assert isinstance(ua_first, str)
        assert len(ua_first) > 0

    @pytest.mark.asyncio
    @patch('src.scraper.fetcher.async_playwright')
    async def test_start_launches_browser(self, mock_playwright):
        """Test that start() launches Playwright browser."""
        mock_pw = AsyncMock()
        mock_browser = AsyncMock()
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw)

        fetcher = HTMLFetcher()
        await fetcher.start()

        assert fetcher.browser is not None
        mock_pw.chromium.launch.assert_called_once()

        await fetcher.close()

    @pytest.mark.asyncio
    @patch('src.scraper.fetcher.async_playwright')
    async def test_fetch_page_success(self, mock_playwright):
        """Test successful page fetch."""
        # Setup mocks
        mock_pw = AsyncMock()
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.status_text = "OK"

        mock_page.goto = AsyncMock(return_value=mock_response)
        mock_page.content = AsyncMock(return_value="<html><body>Test</body></html>")
        mock_page.close = AsyncMock()

        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw)

        # Test
        async with HTMLFetcher() as fetcher:
            fetcher.rate_limiter = RateLimiter(min_delay=0.0, max_delay=0.0)  # No delay for test
            html = await fetcher.fetch_page("https://example.com")

        assert html == "<html><body>Test</body></html>"
        mock_page.goto.assert_called_once()
        mock_page.close.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.scraper.fetcher.async_playwright')
    async def test_fetch_page_handles_404(self, mock_playwright):
        """Test that 404 response raises FetchError."""
        mock_pw = AsyncMock()
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.status_text = "Not Found"

        mock_page.goto = AsyncMock(return_value=mock_response)
        mock_page.close = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw)

        async with HTMLFetcher() as fetcher:
            fetcher.rate_limiter = RateLimiter(min_delay=0.0, max_delay=0.0)

            with pytest.raises(FetchError) as exc_info:
                await fetcher.fetch_page("https://example.com/notfound")

            assert "404" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch('src.scraper.fetcher.async_playwright')
    async def test_fetch_page_retries_on_failure(self, mock_playwright):
        """Test that fetch_page retries on failure."""
        mock_pw = AsyncMock()
        mock_browser = AsyncMock()
        mock_page = AsyncMock()

        # First two attempts fail, third succeeds
        mock_response = MagicMock()
        mock_response.status = 200
        mock_page.goto = AsyncMock(
            side_effect=[
                Exception("Connection error"),
                Exception("Timeout"),
                mock_response
            ]
        )
        mock_page.content = AsyncMock(return_value="<html>Success</html>")
        mock_page.close = AsyncMock()

        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw)

        async with HTMLFetcher() as fetcher:
            fetcher.rate_limiter = RateLimiter(min_delay=0.0, max_delay=0.0)

            with patch('asyncio.sleep', new=AsyncMock()):  # Skip backoff delay
                html = await fetcher.fetch_page("https://example.com", max_retries=3)

        assert html == "<html>Success</html>"
        assert mock_page.goto.call_count == 3

    @pytest.mark.asyncio
    @patch('src.scraper.fetcher.async_playwright')
    async def test_fetch_page_fails_after_max_retries(self, mock_playwright):
        """Test that fetch_page raises FetchError after max retries."""
        mock_pw = AsyncMock()
        mock_browser = AsyncMock()
        mock_page = AsyncMock()

        mock_page.goto = AsyncMock(side_effect=Exception("Always fails"))
        mock_page.close = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw)

        async with HTMLFetcher() as fetcher:
            fetcher.rate_limiter = RateLimiter(min_delay=0.0, max_delay=0.0)

            with patch('asyncio.sleep', new=AsyncMock()):
                with pytest.raises(FetchError) as exc_info:
                    await fetcher.fetch_page("https://example.com", max_retries=2)

            assert "after 3 attempts" in str(exc_info.value)
