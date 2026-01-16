"""Scraping orchestrator - coordinates fetching, parsing, and storage."""
import asyncio
from typing import List, Set, Dict
from datetime import datetime

from src.scraper.url_validator import validate_url_strict
from src.scraper.fetcher import HTMLFetcher
from src.scraper.parser import parse_blog_listing, find_next_page_link
from src.config import get_logger

logger = get_logger(__name__)


class ScrapingStats:
    """Statistics for a scraping job."""
    def __init__(self):
        self.pages_scraped = 0
        self.posts_found = 0
        self.errors = []

    def to_dict(self) -> Dict:
        return {
            "pages_scraped": self.pages_scraped,
            "posts_found": self.posts_found,
            "errors": self.errors
        }


async def scrape_blog(
    blog_url: str,
    max_pages: int = 10
) -> tuple[List[Dict], ScrapingStats]:
    """Scrape blog posts from a blog URL with pagination.

    Args:
        blog_url: Starting URL of the blog
        max_pages: Maximum number of pages to scrape

    Returns:
        tuple: (list of parsed posts, scraping stats)
    """
    # Validate URL
    validate_url_strict(blog_url)

    logger.info("Starting blog scrape", blog_url=blog_url, max_pages=max_pages)

    stats = ScrapingStats()
    posts = []
    visited_urls: Set[str] = set()
    current_url = blog_url

    async with HTMLFetcher() as fetcher:
        for page_num in range(max_pages):
            # Check if already visited (prevent loops)
            if current_url in visited_urls:
                logger.warning("URL already visited, stopping", url=current_url)
                break

            visited_urls.add(current_url)

            try:
                logger.info(f"Scraping page {page_num + 1}/{max_pages}", url=current_url)

                # Fetch HTML
                html = await fetcher.fetch_page(current_url)
                stats.pages_scraped += 1

                # Parse blog posts from page (may return multiple posts)
                page_posts = parse_blog_listing(html, current_url)
                for post_data in page_posts:
                    post_data["blog_url"] = blog_url
                    post_data["scraped_at"] = datetime.utcnow()
                    posts.append(post_data)
                    stats.posts_found += 1

                logger.info(f"Found {len(page_posts)} posts on page {page_num + 1}")

                # Find next page
                next_url = find_next_page_link(html, current_url)
                if not next_url:
                    logger.info("No more pages found")
                    break

                current_url = next_url

            except Exception as e:
                error_msg = f"Error scraping {current_url}: {str(e)}"
                logger.error("Scraping error", url=current_url, error=str(e))
                stats.errors.append(error_msg)
                break

    logger.info(
        "Blog scrape complete",
        blog_url=blog_url,
        pages=stats.pages_scraped,
        posts=stats.posts_found
    )

    return posts, stats
