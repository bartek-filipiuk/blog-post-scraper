"""HTML parser for extracting blog post content."""
from bs4 import BeautifulSoup
from typing import Optional, List, Dict
from datetime import datetime
from urllib.parse import urljoin, urlparse
import re

from src.config import get_logger

logger = get_logger(__name__)


def parse_blog_listing(html: str, url: str) -> List[Dict[str, any]]:
    """Parse multiple blog posts from a listing page.

    Args:
        html: HTML content
        url: Source URL (for resolving relative URLs)

    Returns:
        list: List of parsed blog post data dicts
    """
    soup = BeautifulSoup(html, 'lxml')
    posts = []

    # Try to find article containers (common blog listing patterns)
    article_containers = soup.find_all('article')

    # If no article tags, try common blog post container patterns
    if not article_containers:
        article_containers = soup.find_all('div', class_=re.compile(r'post|entry|article', re.I))

    # If still nothing, try to find multiple h2/h3 tags (common for blog listings)
    if not article_containers:
        # Look for heading tags that might be post titles
        headings = soup.find_all(['h2', 'h3'])
        for heading in headings:
            # Find the parent container (usually a div or article)
            container = heading.find_parent(['div', 'article', 'section'])
            if container and container not in article_containers:
                article_containers.append(container)

    # If we found multiple containers, extract from each
    if len(article_containers) > 1:
        logger.info(f"Found {len(article_containers)} article containers on page", url=url)
        for container in article_containers:
            post = _extract_post_from_container(container, url)
            if post['title']:  # Only add if we got a title
                posts.append(post)
    else:
        # Single post page or no containers found - extract from whole page
        post = parse_blog_post(html, url)
        posts.append(post)

    logger.info(f"Parsed {len(posts)} posts from page", url=url)
    return posts


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

    # Try attribute-based patterns first (fast)
    next_patterns = [
        ('a', {'class': re.compile(r'next', re.I)}),
        ('a', {'rel': 'next'}),
        ('a', {'aria-label': re.compile(r'next', re.I)}),
        ('a', {'title': re.compile(r'next', re.I)}),
    ]

    for tag, attrs in next_patterns:
        link = soup.find(tag, attrs)
        if link:
            href = link.get('href')
            if href:
                return urljoin(current_url, href)

    # Fallback: Text-based search (get_text() works with nested HTML)
    for link in soup.find_all('a'):
        text = link.get_text(strip=True)
        if re.search(r'\b(next|→|»)\b', text, re.I):
            href = link.get('href')
            if href and not href.startswith('#'):  # Skip anchor links
                return urljoin(current_url, href)

    logger.debug("No next page link found", url=current_url)
    return None


def _extract_post_from_container(container: BeautifulSoup, base_url: str) -> Dict[str, any]:
    """Extract post data from a single container element.

    Args:
        container: BeautifulSoup element containing a single post
        base_url: Base URL for resolving relative URLs

    Returns:
        dict: Parsed blog post data
    """
    # Extract title and post URL from container
    title = ""
    post_url = None
    title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
    if title_elem:
        # If title has a link, get both the link text and URL
        link = title_elem.find('a')
        if link:
            title = link.get_text(strip=True)
            href = link.get('href')
            if href:
                post_url = urljoin(base_url, href)
        else:
            title = title_elem.get_text(strip=True)

    # If no post URL from title, try "Read more" or similar links
    if not post_url:
        read_more_patterns = [
            re.compile(r'read\s*more', re.I),
            re.compile(r'continue\s*reading', re.I),
            re.compile(r'full\s*(article|post|story)', re.I),
            re.compile(r'learn\s*more', re.I),
        ]
        for pattern in read_more_patterns:
            read_more = container.find('a', string=pattern)
            if not read_more:
                # Try finding link with matching text content
                for link in container.find_all('a', href=True):
                    if pattern.search(link.get_text(strip=True)):
                        read_more = link
                        break
            if read_more:
                href = read_more.get('href')
                if href:
                    post_url = urljoin(base_url, href)
                    break

    # If still no URL, try the first link in the container that looks like a post URL
    if not post_url:
        for link in container.find_all('a', href=True):
            href = link.get('href')
            if href and not href.startswith('#'):
                # Avoid pagination, category, or tag links
                href_lower = href.lower()
                if not any(skip in href_lower for skip in ['/page/', '/category/', '/tag/', '/author/', '?page=']):
                    post_url = urljoin(base_url, href)
                    break

    # Extract author from container
    author = None
    author_elem = container.find(['span', 'div', 'a'], class_=re.compile(r'author', re.I))
    if author_elem:
        author = author_elem.get_text(strip=True)

    # Extract date from container
    published_date = None
    time_elem = container.find('time')
    if time_elem:
        datetime_str = time_elem.get('datetime', '') or time_elem.get_text(strip=True)
        if datetime_str:
            try:
                published_date = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            except:
                pass

    # Extract content/excerpt from container
    content = ""
    # Try to find excerpt/summary first
    excerpt_elem = container.find(['div', 'p'], class_=re.compile(r'excerpt|summary|description', re.I))
    if excerpt_elem:
        content = excerpt_elem.get_text(strip=True, separator='\n')
    else:
        # Get all paragraph text
        paragraphs = container.find_all('p')
        if paragraphs:
            content = '\n'.join(p.get_text(strip=True) for p in paragraphs)
        else:
            content = container.get_text(strip=True, separator='\n')

    # Generate excerpt
    excerpt = _generate_excerpt(content)

    # Extract images from container
    images = []
    for img in container.find_all('img'):
        src = img.get('src')
        if src:
            absolute_url = urljoin(base_url, src)
            images.append(absolute_url)

    return {
        "title": title,
        "post_url": post_url,
        "author": author,
        "published_date": published_date,
        "content": content,
        "excerpt": excerpt,
        "images": images
    }


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
