"""Unit tests for Pydantic schemas."""
import pytest
from pydantic import ValidationError
from datetime import datetime
from uuid import uuid4

from src.schemas import (
    URLInput,
    BlogPostCreate,
    BlogPostResponse,
    ScrapingJobCreate,
    ScrapingJobResponse,
)


class TestURLInput:
    """Tests for URLInput schema validation."""

    def test_valid_http_url(self):
        """Test that valid HTTP URL is accepted."""
        url_input = URLInput(url="http://example.com/blog")
        assert url_input.url == "http://example.com/blog"
        assert url_input.max_pages == 10  # default

    def test_valid_https_url(self):
        """Test that valid HTTPS URL is accepted."""
        url_input = URLInput(url="https://example.com/blog", max_pages=5)
        assert url_input.url == "https://example.com/blog"
        assert url_input.max_pages == 5

    def test_url_with_path(self):
        """Test URL with path is accepted."""
        url_input = URLInput(url="https://blog.example.com/posts/2024")
        assert url_input.url == "https://blog.example.com/posts/2024"

    def test_url_with_query_params(self):
        """Test URL with query parameters is accepted."""
        url_input = URLInput(url="https://example.com/blog?page=1&category=tech")
        assert "page=1" in url_input.url

    def test_reject_file_scheme(self):
        """Test that file:// URLs are rejected (SSRF prevention)."""
        with pytest.raises(ValidationError) as exc_info:
            URLInput(url="file:///etc/passwd")
        assert "Invalid URL" in str(exc_info.value)

    def test_reject_javascript_scheme(self):
        """Test that javascript: URLs are rejected (XSS prevention)."""
        with pytest.raises(ValidationError) as exc_info:
            URLInput(url="javascript:alert('xss')")
        assert "Invalid URL" in str(exc_info.value)

    def test_reject_data_scheme(self):
        """Test that data: URLs are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            URLInput(url="data:text/html,<h1>Test</h1>")
        assert "Invalid URL" in str(exc_info.value)

    def test_reject_localhost(self):
        """Test that localhost URLs are rejected (SSRF prevention)."""
        with pytest.raises(ValidationError) as exc_info:
            URLInput(url="http://localhost:8000/blog")
        assert "localhost" in str(exc_info.value).lower()

    def test_reject_127_0_0_1(self):
        """Test that 127.0.0.1 URLs are rejected (SSRF prevention)."""
        with pytest.raises(ValidationError) as exc_info:
            URLInput(url="http://127.0.0.1:8000/blog")
        assert "localhost" in str(exc_info.value).lower()

    def test_reject_ftp_scheme(self):
        """Test that ftp:// URLs are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            URLInput(url="ftp://ftp.example.com/file.txt")
        assert "Invalid URL" in str(exc_info.value)

    def test_url_too_short(self):
        """Test that very short URLs are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            URLInput(url="http://a")
        assert "at least 10 characters" in str(exc_info.value)

    def test_url_too_long(self):
        """Test that very long URLs are rejected."""
        long_url = "https://example.com/" + "a" * 3000
        with pytest.raises(ValidationError) as exc_info:
            URLInput(url=long_url)
        assert "at most 2048 characters" in str(exc_info.value)

    def test_max_pages_bounds(self):
        """Test max_pages validation bounds."""
        # Valid range
        url_input = URLInput(url="https://example.com/blog", max_pages=1)
        assert url_input.max_pages == 1

        url_input = URLInput(url="https://example.com/blog", max_pages=100)
        assert url_input.max_pages == 100

        # Out of bounds
        with pytest.raises(ValidationError):
            URLInput(url="https://example.com/blog", max_pages=0)

        with pytest.raises(ValidationError):
            URLInput(url="https://example.com/blog", max_pages=101)


class TestBlogPostCreate:
    """Tests for BlogPostCreate schema."""

    def test_valid_blog_post_full(self):
        """Test creating blog post with all fields."""
        post = BlogPostCreate(
            blog_url="https://example.com/blog",
            title="Test Post",
            author="John Doe",
            published_date=datetime(2026, 1, 15),
            content="Full content here",
            excerpt="Short excerpt",
            images=["https://example.com/image.jpg"]
        )
        assert post.title == "Test Post"
        assert post.author == "John Doe"
        assert len(post.images) == 1

    def test_valid_blog_post_minimal(self):
        """Test creating blog post with only required fields."""
        post = BlogPostCreate(
            blog_url="https://example.com/blog",
            title="Test Post",
            content="Full content here"
        )
        assert post.title == "Test Post"
        assert post.author is None
        assert post.published_date is None
        assert post.excerpt is None
        assert post.images == []

    def test_missing_required_fields(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            BlogPostCreate(blog_url="https://example.com/blog")
        assert "title" in str(exc_info.value)
        assert "content" in str(exc_info.value)


class TestBlogPostResponse:
    """Tests for BlogPostResponse schema."""

    def test_valid_response(self):
        """Test creating valid response."""
        response = BlogPostResponse(
            id=uuid4(),
            blog_url="https://example.com/blog",
            title="Test Post",
            author="John Doe",
            published_date=datetime(2026, 1, 15),
            content="Full content",
            excerpt="Excerpt",
            images=["https://example.com/img.jpg"],
            scraped_at=datetime.utcnow()
        )
        assert response.title == "Test Post"
        assert isinstance(response.scraped_at, datetime)


class TestScrapingJobCreate:
    """Tests for ScrapingJobCreate schema."""

    def test_valid_job_create(self):
        """Test creating valid scraping job."""
        job = ScrapingJobCreate(
            blog_url="https://example.com/blog",
            max_pages=5
        )
        assert job.blog_url == "https://example.com/blog"
        assert job.max_pages == 5

    def test_default_max_pages(self):
        """Test default max_pages value."""
        job = ScrapingJobCreate(blog_url="https://example.com/blog")
        assert job.max_pages == 10


class TestScrapingJobResponse:
    """Tests for ScrapingJobResponse schema."""

    def test_valid_job_response(self):
        """Test creating valid job response."""
        response = ScrapingJobResponse(
            id=uuid4(),
            blog_url="https://example.com/blog",
            status="completed",
            pages_scraped=5,
            posts_found=25,
            error_message=None,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        assert response.status == "completed"
        assert response.pages_scraped == 5
        assert response.posts_found == 25

    def test_job_with_error(self):
        """Test job response with error message."""
        response = ScrapingJobResponse(
            id=uuid4(),
            blog_url="https://example.com/blog",
            status="failed",
            pages_scraped=2,
            posts_found=5,
            error_message="Connection timeout",
            created_at=datetime.utcnow(),
            completed_at=None
        )
        assert response.status == "failed"
        assert response.error_message == "Connection timeout"
        assert response.completed_at is None
