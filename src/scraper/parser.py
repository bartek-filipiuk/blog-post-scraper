"""HTML parser for extracting blog post content."""
from bs4 import BeautifulSoup
from typing import Optional, List, Dict
from datetime import datetime
from urllib.parse import urljoin, urlparse
import re

from src.config import get_logger

logger = get_logger(__name__)


def parse_blog_post(html: str, url: str) -> Dict[str, any]:
    """Parse blog post from HTML content.

    Args:
        html: HTML content
        url: Source URL (for resolving relative URLs)

    Returns:
        dict: Parsed blog post data with keys:
            - title: str
            - author: Optional[str]
            - published_date: Optional[datetime]
            - content: str
            - excerpt: Optional[str]
            - images: List[str]
    """
    soup = BeautifulSoup(html, 'lxml')

    # Extract title
    title = _extract_title(soup)

    # Extract author
    author = _extract_author(soup)

    # Extract date
    published_date = _extract_date(soup)

    # Extract content
    content = _extract_content(soup)

    # Generate excerpt
    excerpt = _generate_excerpt(content)

    # Extract images
    images = _extract_images(soup, url)

    logger.info("Blog post parsed", url=url, title=title[:50] if title else None)

    return {
        "title": title,
        "author": author,
        "published_date": published_date,
        "content": content,
        "excerpt": excerpt,
        "images": images
    }


def find_next_page_link(html: str, current_url: str) -> Optional[str]:
    """Find next page link in HTML.

    Args:
        html: HTML content
        current_url: Current page URL (for resolving relative URLs)

    Returns:
        Optional[str]: Absolute URL of next page, or None
    """
    soup = BeautifulSoup(html, 'lxml')

    # Common patterns for next page links
    next_patterns = [
        ('a', {'class': re.compile(r'next', re.I)}),
        ('a', {'rel': 'next'}),
        ('a', {'aria-label': re.compile(r'next', re.I)}),
        ('a', {'title': re.compile(r'next', re.I)}),
        ('a', {'text': re.compile(r'(next|→|»)', re.I)}),
    ]

    for tag, attrs in next_patterns:
        if 'text' in attrs:
            # Search by link text
            links = soup.find_all('a', string=attrs['text'])
            if links:
                href = links[0].get('href')
                if href:
                    return urljoin(current_url, href)
        else:
            link = soup.find(tag, attrs)
            if link:
                href = link.get('href')
                if href:
                    return urljoin(current_url, href)

    logger.debug("No next page link found", url=current_url)
    return None


def _extract_title(soup: BeautifulSoup) -> str:
    """Extract title from HTML."""
    # Try h1 first
    h1 = soup.find('h1')
    if h1:
        return h1.get_text(strip=True)

    # Try title tag
    title = soup.find('title')
    if title:
        return title.get_text(strip=True)

    # Try meta og:title
    og_title = soup.find('meta', property='og:title')
    if og_title:
        return og_title.get('content', '').strip()

    return "Untitled"


def _extract_author(soup: BeautifulSoup) -> Optional[str]:
    """Extract author from HTML."""
    # Try common author selectors
    author_selectors = [
        ('meta', {'name': 'author'}),
        ('span', {'class': re.compile(r'author', re.I)}),
        ('div', {'class': re.compile(r'author', re.I)}),
        ('a', {'rel': 'author'}),
        ('meta', {'property': 'article:author'}),
    ]

    for tag, attrs in author_selectors:
        element = soup.find(tag, attrs)
        if element:
            if tag == 'meta':
                content = element.get('content', '').strip()
                if content:
                    return content
            else:
                text = element.get_text(strip=True)
                if text:
                    return text

    return None


def _extract_date(soup: BeautifulSoup) -> Optional[datetime]:
    """Extract publication date from HTML."""
    # Try time tag first
    time_tag = soup.find('time')
    if time_tag:
        datetime_str = time_tag.get('datetime', '') or time_tag.get_text(strip=True)
        if datetime_str:
            try:
                return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            except:
                pass

    # Try meta tags
    meta_date = soup.find('meta', property='article:published_time')
    if meta_date:
        try:
            return datetime.fromisoformat(meta_date.get('content', '').replace('Z', '+00:00'))
        except:
            pass

    return None


def _extract_content(soup: BeautifulSoup) -> str:
    """Extract main content from HTML."""
    # Try article tag
    article = soup.find('article')
    if article:
        return article.get_text(strip=True, separator='\n')

    # Try common content containers
    content_selectors = [
        ('div', {'class': re.compile(r'content|post-body|entry-content', re.I)}),
        ('main', {}),
        ('div', {'id': re.compile(r'content|main', re.I)}),
    ]

    for tag, attrs in content_selectors:
        element = soup.find(tag, attrs)
        if element:
            return element.get_text(strip=True, separator='\n')

    # Fallback: get body text
    body = soup.find('body')
    if body:
        return body.get_text(strip=True, separator='\n')

    return ""


def _generate_excerpt(content: str, max_length: int = 200) -> Optional[str]:
    """Generate excerpt from content."""
    if not content:
        return None

    # Take first max_length characters
    if len(content) <= max_length:
        return content

    # Find last space before max_length
    excerpt = content[:max_length]
    last_space = excerpt.rfind(' ')
    if last_space > 0:
        excerpt = excerpt[:last_space]

    return excerpt + "..."


def _extract_images(soup: BeautifulSoup, base_url: str) -> List[str]:
    """Extract image URLs from HTML."""
    images = []

    # Find all img tags
    for img in soup.find_all('img'):
        src = img.get('src')
        if src:
            # Convert to absolute URL
            absolute_url = urljoin(base_url, src)
            images.append(absolute_url)

    return images
