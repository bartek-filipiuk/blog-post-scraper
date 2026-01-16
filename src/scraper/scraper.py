"""Scraping orchestrator - coordinates fetching, parsing, and storage."""
import asyncio
from typing import List, Set, Dict
from datetime import datetime

from src.scraper.url_validator import validate_url_strict
from src.scraper.fetcher import HTMLFetcher
from src.scraper.parser import parse_blog_listing, parse_blog_post, find_next_page_link
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
    max_pages: int = 10,
    fetch_full_content: bool = True
) -> tuple[List[Dict], ScrapingStats]:
    """Scrape blog posts from a blog URL with pagination.

    Two-phase scraping:
    1. Phase 1: Collect post URLs from listing pages
    2. Phase 2: Fetch full content from each individual post URL

    Args:
        blog_url: Starting URL of the blog
        max_pages: Maximum number of listing pages to scrape
        fetch_full_content: If True, fetch individual post pages for full content

    Returns:
        tuple: (list of parsed posts, scraping stats)
    """
    # Validate URL
    validate_url_strict(blog_url)

    logger.info("Starting blog scrape", blog_url=blog_url, max_pages=max_pages, fetch_full_content=fetch_full_content)

    stats = ScrapingStats()
    posts = []
    posts_to_fetch = []  # Posts that have URLs for full content fetching
    visited_urls: Set[str] = set()
    current_url = blog_url

    async with HTMLFetcher() as fetcher:
        # ========== PHASE 1: Collect post URLs from listing pages ==========
        logger.info("Phase 1: Collecting posts from listing pages")

        for page_num in range(max_pages):
            # Check if already visited (prevent loops)
            if current_url in visited_urls:
                logger.warning("URL already visited, stopping", url=current_url)
                break

            visited_urls.add(current_url)

            try:
                logger.info(f"Scraping listing page {page_num + 1}/{max_pages}", url=current_url)

                # Fetch HTML
                html = await fetcher.fetch_page(current_url)
                stats.pages_scraped += 1

                # Parse blog posts from page (may return multiple posts with post_url)
                page_posts = parse_blog_listing(html, current_url)
                for post_data in page_posts:
                    post_data["blog_url"] = blog_url
                    post_data["scraped_at"] = datetime.utcnow()

                    # If post has URL and we want full content, queue for Phase 2
                    if fetch_full_content and post_data.get("post_url"):
                        posts_to_fetch.append(post_data)
                    else:
                        # No URL or full content not requested - use teaser content
                        posts.append(post_data)
                        stats.posts_found += 1

                logger.info(f"Found {len(page_posts)} posts on listing page {page_num + 1}")

                # Find next page
                next_url = find_next_page_link(html, current_url)
                if not next_url:
                    logger.info("No more listing pages found")
                    break

                current_url = next_url

            except Exception as e:
                error_msg = f"Error scraping listing {current_url}: {str(e)}"
                logger.error("Listing scraping error", url=current_url, error=str(e))
                stats.errors.append(error_msg)
                break

        # ========== PHASE 2: Fetch full content for each post URL ==========
        if fetch_full_content and posts_to_fetch:
            logger.info(f"Phase 2: Fetching full content for {len(posts_to_fetch)} posts")

            for i, post_data in enumerate(posts_to_fetch, 1):
                post_url = post_data["post_url"]

                # Skip if already visited (deduplication)
                if post_url in visited_urls:
                    logger.debug(f"Post URL already visited, skipping", url=post_url)
                    posts.append(post_data)  # Keep teaser content
                    stats.posts_found += 1
                    continue

                visited_urls.add(post_url)

                try:
                    logger.info(f"Fetching post {i}/{len(posts_to_fetch)}", url=post_url)

                    # Fetch individual post page
                    post_html = await fetcher.fetch_page(post_url)

                    # Parse full content from individual post page
                    full_content = parse_blog_post(post_html, post_url)

                    # Merge full content with listing metadata
                    post_data["content"] = full_content.get("content") or post_data.get("content", "")
                    post_data["images"] = full_content.get("images") or post_data.get("images", [])
                    post_data["author"] = full_content.get("author") or post_data.get("author")
                    post_data["published_date"] = full_content.get("published_date") or post_data.get("published_date")

                    # Regenerate excerpt from full content
                    if post_data["content"]:
                        content_text = post_data["content"]
                        if len(content_text) > 200:
                            excerpt = content_text[:200]
                            last_space = excerpt.rfind(' ')
                            if last_space > 0:
                                excerpt = excerpt[:last_space]
                            post_data["excerpt"] = excerpt + "..."
                        else:
                            post_data["excerpt"] = content_text

                    posts.append(post_data)
                    stats.posts_found += 1

                except Exception as e:
                    error_msg = f"Error fetching post {post_url}: {str(e)}"
                    logger.warning("Post fetch error, keeping teaser content", url=post_url, error=str(e))
                    stats.errors.append(error_msg)
                    # Keep teaser content as fallback
                    posts.append(post_data)
                    stats.posts_found += 1

    logger.info(
        "Blog scrape complete",
        blog_url=blog_url,
        listing_pages=stats.pages_scraped,
        posts=stats.posts_found,
        full_content_fetched=len(posts_to_fetch) if fetch_full_content else 0
    )

    return posts, stats
