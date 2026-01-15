"""Blog posts API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
import uuid
from datetime import datetime

from src.database import get_db
from src.models import BlogPost
from src.schemas import BlogPostResponse, PaginatedBlogPostsResponse, ExportResponse
from src.config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.get("/", response_model=PaginatedBlogPostsResponse)
async def list_posts(
    blog_url: str = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List scraped blog posts."""
    query = select(BlogPost).order_by(BlogPost.scraped_at.desc())

    if blog_url:
        query = query.where(BlogPost.blog_url == blog_url)

    # Get total count
    count_query = select(func.count()).select_from(BlogPost)
    if blog_url:
        count_query = count_query.where(BlogPost.blog_url == blog_url)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    result = await db.execute(query.limit(limit).offset(offset))
    posts = result.scalars().all()

    return {
        "items": posts,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/{post_id}", response_model=BlogPostResponse)
async def get_post(post_id: str, db: AsyncSession = Depends(get_db)):
    """Get single post details."""
    try:
        post_uuid = uuid.UUID(post_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid post ID")

    result = await db.execute(
        select(BlogPost).where(BlogPost.id == post_uuid)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return post


@router.get("/export/json", response_model=ExportResponse)
async def export_posts(db: AsyncSession = Depends(get_db)):
    """Export all posts as JSON."""
    result = await db.execute(
        select(BlogPost).order_by(BlogPost.scraped_at.desc())
    )
    posts = result.scalars().all()

    return {
        "posts": posts,
        "exported_at": datetime.utcnow(),
        "total_posts": len(posts)
    }
