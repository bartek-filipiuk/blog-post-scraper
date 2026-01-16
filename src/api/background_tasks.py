"""Background task execution for scraping jobs."""
import asyncio
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ScrapingJob, BlogPost, JobStatus
from src.scraper.scraper import scrape_blog
from src.database import AsyncSessionLocal
from src.config import get_logger, settings

logger = get_logger(__name__)

# Simple semaphore for limiting concurrent jobs
_job_semaphore = asyncio.Semaphore(settings.max_concurrent_jobs)


async def run_scraping_job(job_id: str) -> None:
    """Execute scraping job in background.

    Args:
        job_id: UUID string of the scraping job
    """
    async with _job_semaphore:
        logger.info("Starting scraping job", job_id=job_id)

        async with AsyncSessionLocal() as db:
            job = None
            try:
                # Convert job_id string to UUID
                job_uuid = uuid.UUID(job_id)

                # Get job
                job = await db.get(ScrapingJob, job_uuid)
                if not job:
                    logger.error("Job not found", job_id=job_id)
                    return

                # Mark as in progress
                job.mark_in_progress()
                await db.commit()

                # Run scraping
                posts, stats = await scrape_blog(job.blog_url, max_pages=10)

                # Save posts to database
                for post_data in posts:
                    post = BlogPost(**post_data)
                    db.add(post)

                # Update job
                job.pages_scraped = stats.pages_scraped
                job.posts_found = stats.posts_found
                job.mark_completed()

                await db.commit()

                logger.info(
                    "Scraping job completed",
                    job_id=job_id,
                    pages=stats.pages_scraped,
                    posts=stats.posts_found
                )

            except Exception as e:
                logger.error("Scraping job failed", job_id=job_id, error=str(e))

                # Mark job as failed
                if job:
                    job.mark_failed(str(e))
                    await db.commit()
