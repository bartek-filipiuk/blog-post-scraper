"""Tests for database models."""
import pytest
from datetime import datetime
import uuid

from src.models import ScrapingJob, BlogPost, JobStatus


def test_scraping_job_creation():
    """Test creating a scraping job."""
    job = ScrapingJob(
        id=uuid.uuid4(),
        blog_url="https://example.com/blog",
        status=JobStatus.PENDING
    )

    assert job.blog_url == "https://example.com/blog"
    assert job.status == JobStatus.PENDING
    assert job.pages_scraped is None
    assert job.posts_found is None
    assert job.error_message is None


def test_scraping_job_mark_in_progress():
    """Test marking job as in progress."""
    job = ScrapingJob(
        id=uuid.uuid4(),
        blog_url="https://example.com/blog",
        status=JobStatus.PENDING
    )

    job.mark_in_progress()

    assert job.status == JobStatus.IN_PROGRESS
    # Note: started_at timestamp would be set by mark_in_progress() method


def test_scraping_job_mark_completed():
    """Test marking job as completed."""
    job = ScrapingJob(
        id=uuid.uuid4(),
        blog_url="https://example.com/blog",
        status=JobStatus.IN_PROGRESS
    )

    job.mark_completed()

    assert job.status == JobStatus.COMPLETED
    assert job.completed_at is not None


def test_scraping_job_mark_failed():
    """Test marking job as failed."""
    job = ScrapingJob(
        id=uuid.uuid4(),
        blog_url="https://example.com/blog",
        status=JobStatus.IN_PROGRESS
    )

    error_msg = "Connection timeout"
    job.mark_failed(error_msg)

    assert job.status == JobStatus.FAILED
    assert job.completed_at is not None
    assert job.error_message == error_msg


def test_blog_post_creation():
    """Test creating a blog post."""
    post = BlogPost(
        id=uuid.uuid4(),
        blog_url="https://example.com/blog",
        title="Test Post",
        author="John Doe",
        published_date=datetime(2025, 1, 1),
        content="Full post content here",
        excerpt="Short excerpt",
        images=["https://example.com/image.jpg"],
        scraped_at=datetime.utcnow()
    )

    assert post.title == "Test Post"
    assert post.author == "John Doe"
    assert post.blog_url == "https://example.com/blog"
    assert post.content == "Full post content here"
    assert len(post.images) == 1


def test_blog_post_minimal():
    """Test creating blog post with minimal required fields."""
    post = BlogPost(
        id=uuid.uuid4(),
        blog_url="https://example.com/blog",
        title="Minimal Post",
        content="Some content",
        scraped_at=datetime.utcnow()
    )

    assert post.title == "Minimal Post"
    assert post.author is None
    assert post.content == "Some content"
    assert post.excerpt is None
    assert post.images is None or post.images == []  # Can be None or empty list


def test_job_status_enum():
    """Test JobStatus enum values."""
    assert JobStatus.PENDING.value == "pending"
    assert JobStatus.IN_PROGRESS.value == "in_progress"
    assert JobStatus.COMPLETED.value == "completed"
    assert JobStatus.FAILED.value == "failed"
