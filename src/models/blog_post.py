"""BlogPost database model."""
from sqlalchemy import Column, String, Text, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from src.database import Base


class BlogPost(Base):
    """Model for storing scraped blog posts.

    Attributes:
        id: Unique identifier (UUID)
        blog_url: URL of the blog where post was found
        title: Post title
        author: Post author (optional)
        published_date: Publication date (optional)
        content: Full post content (HTML or text)
        excerpt: Short excerpt/summary (optional)
        images: Array of image URLs found in post
        scraped_at: Timestamp when post was scraped
    """

    __tablename__ = "blog_posts"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # Blog and post information
    blog_url = Column(String(2048), nullable=False, index=True)
    post_url = Column(String(2048), nullable=True)  # Individual post URL for full content
    title = Column(String(1024), nullable=False)
    author = Column(String(256), nullable=True)
    published_date = Column(DateTime, nullable=True)

    # Content
    content = Column(Text, nullable=False)
    excerpt = Column(String(512), nullable=True)
    images = Column(JSON, default=list, nullable=False)

    # Metadata
    scraped_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Composite indexes for common queries
    __table_args__ = (
        Index('ix_blog_posts_blog_url_scraped_at', 'blog_url', 'scraped_at'),
        Index('ix_blog_posts_published_date', 'published_date'),
    )

    def __repr__(self) -> str:
        """String representation of BlogPost."""
        return f"<BlogPost(id={self.id}, title='{self.title[:50]}...', blog_url='{self.blog_url}')>"

    def to_dict(self) -> dict:
        """Convert model to dictionary for JSON serialization.

        Returns:
            dict: Dictionary representation of the blog post
        """
        return {
            "id": str(self.id),
            "blog_url": self.blog_url,
            "post_url": self.post_url,
            "title": self.title,
            "author": self.author,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "content": self.content,
            "excerpt": self.excerpt,
            "images": self.images,
            "scraped_at": self.scraped_at.isoformat()
        }
