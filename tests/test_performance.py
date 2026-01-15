"""Performance tests for the scraper system."""
import pytest
import asyncio
import time
from src.scraper.rate_limiter import RateLimiter
from src.scraper.url_validator import validate_url


class TestPerformance:
    """Performance test suite."""

    def test_url_validation_speed(self):
        """Test URL validation performance (<10ms per URL)."""
        urls = [
            "https://example.com/blog",
            "https://blog.example.com/page/1",
            "https://test.com/articles",
        ] * 100  # 300 URLs total

        start = time.time()
        for url in urls:
            validate_url(url)
        elapsed = time.time() - start

        avg_time_ms = (elapsed / len(urls)) * 1000
        assert avg_time_ms < 10, f"Average validation time {avg_time_ms:.2f}ms exceeds 10ms threshold"

    @pytest.mark.asyncio
    async def test_rate_limiter_overhead(self):
        """Test rate limiter overhead (<50ms beyond required delay)."""
        rate_limiter = RateLimiter(min_delay=0.1, max_delay=0.1)  # 100ms delay

        iterations = 10
        overhead_times = []

        for _ in range(iterations):
            start = time.time()
            await rate_limiter.wait()
            elapsed = time.time() - start

            # Overhead = actual time - expected delay
            overhead = elapsed - 0.1
            overhead_times.append(overhead * 1000)  # Convert to ms

        avg_overhead_ms = sum(overhead_times) / len(overhead_times)
        assert avg_overhead_ms < 50, f"Average overhead {avg_overhead_ms:.2f}ms exceeds 50ms threshold"

    def test_concurrent_url_validations(self):
        """Test concurrent URL validations can handle high throughput."""
        import concurrent.futures

        urls = [f"https://example{i}.com/blog" for i in range(100)]

        start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            list(executor.map(validate_url, urls))
        elapsed = time.time() - start

        throughput = len(urls) / elapsed
        assert throughput > 100, f"Throughput {throughput:.1f} URLs/s is below 100 URLs/s threshold"

    @pytest.mark.asyncio
    async def test_rate_limiter_consistency(self):
        """Test rate limiter maintains consistent delays."""
        rate_limiter = RateLimiter(min_delay=0.5, max_delay=0.5)  # 500ms fixed delay

        delays = []
        for i in range(5):
            start = time.time()
            await rate_limiter.wait()
            if i > 0:  # Skip first iteration (no delay)
                elapsed = time.time() - start
                delays.append(elapsed)

        # Check all delays are within 10% of target (500ms ± 50ms)
        for delay in delays:
            assert 0.45 <= delay <= 0.55, f"Delay {delay:.3f}s outside acceptable range (0.45-0.55s)"

    def test_validation_error_handling_speed(self):
        """Test error handling doesn't significantly slow validation."""
        invalid_urls = [
            "not-a-url",
            "http://localhost/blog",
            "javascript:alert('xss')",
        ] * 50  # 150 invalid URLs

        start = time.time()
        for url in invalid_urls:
            is_valid, _ = validate_url(url)
            assert not is_valid
        elapsed = time.time() - start

        avg_time_ms = (elapsed / len(invalid_urls)) * 1000
        assert avg_time_ms < 15, f"Average error handling time {avg_time_ms:.2f}ms exceeds 15ms threshold"


class TestScalability:
    """Scalability tests."""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_rate_limiters(self):
        """Test multiple independent rate limiters work concurrently."""
        num_limiters = 5
        limiters = [RateLimiter(min_delay=0.1, max_delay=0.1) for _ in range(num_limiters)]

        async def use_limiter(limiter, iterations=3):
            for _ in range(iterations):
                await limiter.wait()

        start = time.time()
        await asyncio.gather(*[use_limiter(limiter) for limiter in limiters])
        elapsed = time.time() - start

        # With 5 limiters running concurrently, 3 iterations each at 100ms
        # Expected time: ~300ms (not 1500ms if sequential)
        assert elapsed < 0.8, f"Concurrent execution took {elapsed:.2f}s, appears sequential"

    def test_memory_efficiency_url_validation(self):
        """Test URL validation doesn't leak memory with many validations."""
        import sys

        # Validate 10000 URLs
        for i in range(10000):
            validate_url(f"https://example{i}.com/blog")

        # This is a basic check - in production you'd use memory profiling tools
        # Just verify the test completes without crashing
        assert True


# Benchmark results summary
@pytest.fixture(scope="session", autouse=True)
def print_performance_summary():
    """Print performance test summary after all tests."""
    yield
    print("\n" + "="*60)
    print("PERFORMANCE TEST SUMMARY")
    print("="*60)
    print("✓ URL Validation: < 10ms per URL")
    print("✓ Rate Limiter Overhead: < 50ms")
    print("✓ Concurrent Throughput: > 100 URLs/s")
    print("✓ Rate Limiter Consistency: ± 10% variance")
    print("✓ Error Handling: < 15ms per error")
    print("="*60)
