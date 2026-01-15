"""ScrapingJob database model."""
from sqlalchemy import Column, String, Text, DateTime, Integer, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

from src.database import Base


class JobStatus(str, enum.Enum):
    """Enumeration of possible scraping job statuses."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ScrapingJob(Base):
    """Model for tracking scraping jobs.

    Attributes:
        id: Unique identifier (UUID)
        blog_url: URL of the blog being scraped
        status: Current job status (pending/in_progress/completed/failed)
        pages_scraped: Number of pages scraped so far
        posts_found: Number of posts extracted
        error_message: Error details if job failed (optional)
        created_at: Timestamp when job was created
        completed_at: Timestamp when job finished (optional)
    """

    __tablename__ = "scraping_jobs"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # Job information
    blog_url = Column(String(2048), nullable=False, index=True)
    status = Column(
        Enum(JobStatus),
        default=JobStatus.PENDING,
        nullable=False,
        index=True
    )

    # Progress tracking
    pages_scraped = Column(Integer, default=0, nullable=False)
    posts_found = Column(Integer, default=0, nullable=False)

    # Error handling
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Composite indexes for common queries
    __table_args__ = (
        Index('ix_scraping_jobs_status_created_at', 'status', 'created_at'),
        Index('ix_scraping_jobs_blog_url_created_at', 'blog_url', 'created_at'),
    )

    def __repr__(self) -> str:
        """String representation of ScrapingJob."""
        return (
            f"<ScrapingJob(id={self.id}, blog_url='{self.blog_url}', "
            f"status={self.status.value}, pages={self.pages_scraped}, posts={self.posts_found})>"
        )

    def to_dict(self) -> dict:
        """Convert model to dictionary for JSON serialization.

        Returns:
            dict: Dictionary representation of the scraping job
        """
        return {
            "id": str(self.id),
            "blog_url": self.blog_url,
            "status": self.status.value,
            "pages_scraped": self.pages_scraped,
            "posts_found": self.posts_found,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

    def mark_in_progress(self) -> None:
        """Mark job as in progress."""
        self.status = JobStatus.IN_PROGRESS

    def mark_completed(self) -> None:
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error_message: str) -> None:
        """Mark job as failed with error message.

        Args:
            error_message: Description of the error
        """
        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
