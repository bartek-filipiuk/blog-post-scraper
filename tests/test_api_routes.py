"""Tests for API routes (jobs and posts endpoints)."""
import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    with TestClient(app) as test_client:
        yield test_client


# Health check tests
def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "blog-post-scraper"


# Job API tests
def test_create_job_valid_url(client):
    """Test creating job with valid URL."""
    response = client.post("/api/jobs/", json={"url": "https://example.com/blog"})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["blog_url"] == "https://example.com/blog"
    assert data["status"] == "pending"


def test_create_job_invalid_url(client):
    """Test creating job with invalid URL."""
    response = client.post("/api/jobs/", json={"url": "not-a-url"})
    assert response.status_code in [400, 422]  # 400 or 422 for validation errors


def test_create_job_localhost(client):
    """Test creating job with localhost URL (should fail)."""
    response = client.post("/api/jobs/", json={"url": "http://localhost/blog"})
    assert response.status_code in [400, 422]  # 400 or 422 for validation errors


def test_list_jobs(client):
    """Test listing jobs."""
    response = client.get("/api/jobs/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_job_invalid_id(client):
    """Test getting job with invalid UUID."""
    response = client.get("/api/jobs/not-a-uuid")
    assert response.status_code == 400


# Posts API tests
def test_list_posts(client):
    """Test listing posts."""
    response = client.get("/api/posts/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data


def test_list_posts_pagination(client):
    """Test posts pagination parameters."""
    response = client.get("/api/posts/?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 10
    assert data["offset"] == 0


def test_get_post_invalid_id(client):
    """Test getting post with invalid UUID."""
    response = client.get("/api/posts/not-a-uuid")
    assert response.status_code == 400


def test_export_posts(client):
    """Test exporting posts."""
    response = client.get("/api/posts/export/json")
    assert response.status_code == 200
    data = response.json()
    assert "posts" in data
    assert "total_posts" in data
    assert "exported_at" in data
