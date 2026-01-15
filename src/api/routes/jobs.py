"""Job management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from src.database import get_db
from src.models import ScrapingJob, JobStatus
from src.schemas import ScrapingJobCreate, ScrapingJobResponse, URLInput
from src.scraper.url_validator import validate_url_strict, URLValidationError
from src.config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/", response_model=ScrapingJobResponse)
async def create_job(
    job_input: URLInput,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Create new scraping job."""
    try:
        # Validate URL
        validate_url_strict(job_input.url)
    except URLValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create job
    job = ScrapingJob(
        id=uuid.uuid4(),
        blog_url=job_input.url,
        status=JobStatus.PENDING
    )

    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Schedule background task (simplified for MVP)
    logger.info("Job created", job_id=str(job.id), url=job_input.url)

    return job


@router.get("/", response_model=List[ScrapingJobResponse])
async def list_jobs(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List all scraping jobs."""
    result = await db.execute(
        select(ScrapingJob)
        .order_by(ScrapingJob.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    jobs = result.scalars().all()
    return jobs


@router.get("/{job_id}", response_model=ScrapingJobResponse)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get job details."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID")

    result = await db.execute(
        select(ScrapingJob).where(ScrapingJob.id == job_uuid)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job
