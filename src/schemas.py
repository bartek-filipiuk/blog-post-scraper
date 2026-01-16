"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional
import re
from uuid import UUID


class URLInput(BaseModel):
    """Schema for URL input validation.

    Validates that URLs use http/https schemes only.
    Prevents SSRF attacks by rejecting file://, javascript:, etc.
    """

    url: str = Field(
        ...,
        min_length=10,
        max_length=2048,
        description="Blog URL to scrape (http:// or https:// only)",
        json_schema_extra={
            "example": "https://example.com/blog"
        }
    )
    max_pages: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of pages to scrape",
        json_schema_extra={
            "example": 10
        }
    )

    @field_validator('url')
    @classmethod
    def validate_url_scheme(cls, v: str) -> str:
        """Validate URL uses http/https scheme only.

        Args:
            v: URL string to validate

        Returns:
            str: Validated URL

        Raises:
            ValueError: If URL uses invalid scheme or blocked hostname
        """
        # Check scheme
        url_pattern = re.compile(
            r'^https?://'  # Must start with http:// or https://
            r'(?!localhost|127\.0\.0\.1|0\.0\.0\.0|::1)'  # Block localhost
            r'[a-zA-Z0-9]'  # Must have valid domain start
        )

        if not url_pattern.match(v.lower()):
            raise ValueError(
                "Invalid URL. Must use http:// or https:// scheme and cannot target localhost"
            )

        # Additional security checks
        blocked_patterns = [
            'file://',
            'javascript:',
            'data:',
            'ftp://',
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            '::1'
        ]

        v_lower = v.lower()
        for pattern in blocked_patterns:
            if pattern in v_lower:
                raise ValueError(f"URL contains blocked pattern: {pattern}")

        return v


class BlogPostCreate(BaseModel):
    """Schema for creating a blog post."""

    blog_url: str = Field(..., max_length=2048)
    post_url: Optional[str] = Field(None, max_length=2048)
    title: str = Field(..., max_length=1024)
    author: Optional[str] = Field(None, max_length=256)
    published_date: Optional[datetime] = None
    content: str
    excerpt: Optional[str] = Field(None, max_length=512)
    images: list[str] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "blog_url": "https://example.com/blog",
                "post_url": "https://example.com/blog/my-post",
                "title": "10 Tips for Python Development",
                "author": "Jane Doe",
                "published_date": "2026-01-15T10:00:00Z",
                "content": "Full blog post content here...",
                "excerpt": "Learn the top 10 tips for Python development...",
                "images": ["https://example.com/image1.jpg"]
            }
        }
    )


class BlogPostResponse(BaseModel):
    """Schema for blog post API responses."""

    id: UUID
    blog_url: str
    post_url: Optional[str]
    title: str
    author: Optional[str]
    published_date: Optional[datetime]
    content: str
    excerpt: Optional[str]
    images: list[str]
    scraped_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "blog_url": "https://example.com/blog",
                "post_url": "https://example.com/blog/my-post",
                "title": "10 Tips for Python Development",
                "author": "Jane Doe",
                "published_date": "2026-01-15T10:00:00Z",
                "content": "Full blog post content here...",
                "excerpt": "Learn the top 10 tips for Python development...",
                "images": ["https://example.com/image1.jpg"],
                "scraped_at": "2026-01-15T12:30:00Z"
            }
        }
    )


class ScrapingJobCreate(BaseModel):
    """Schema for creating a scraping job."""

    blog_url: str = Field(..., max_length=2048)
    max_pages: int = Field(default=10, ge=1, le=100)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "blog_url": "https://example.com/blog",
                "max_pages": 10
            }
        }
    )


class ScrapingJobResponse(BaseModel):
    """Schema for scraping job API responses."""

    id: UUID
    blog_url: str
    status: str
    pages_scraped: int
    posts_found: int
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "660e8400-e29b-41d4-a716-446655440001",
                "blog_url": "https://example.com/blog",
                "status": "completed",
                "pages_scraped": 5,
                "posts_found": 25,
                "error_message": None,
                "created_at": "2026-01-15T12:00:00Z",
                "completed_at": "2026-01-15T12:05:00Z"
            }
        }
    )


class PaginatedBlogPostsResponse(BaseModel):
    """Schema for paginated blog posts response."""

    items: list[BlogPostResponse]
    total: int
    limit: int
    offset: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 100,
                "limit": 50,
                "offset": 0
            }
        }
    )


class ExportResponse(BaseModel):
    """Schema for export response."""

    posts: list[BlogPostResponse]
    exported_at: datetime
    total_posts: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "posts": [],
                "exported_at": "2026-01-15T12:30:00Z",
                "total_posts": 50
            }
        }
    )
