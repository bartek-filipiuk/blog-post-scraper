"""Tests for HTML parser."""
import pytest
from datetime import datetime
from src.scraper.parser import parse_blog_post, find_next_page_link

def test_parse_blog_post_basic():
    """Test basic blog post parsing."""
    html = """
    <html><body>
    <h1>Test Title</h1>
    <span class="author">John Doe</span>
    <article>This is the content of the blog post.</article>
    </body></html>
    """
    result = parse_blog_post(html, "https://example.com/post")
    assert result["title"] == "Test Title"
    assert result["author"] == "John Doe"
    assert "content" in result["content"]

def test_find_next_page_link():
    """Test finding next page link."""
    html = '<html><body><a href="/page2" class="next">Next</a></body></html>'
    next_url = find_next_page_link(html, "https://example.com/page1")
    assert next_url == "https://example.com/page2"

def test_find_next_page_link_none():
    """Test when no next link exists."""
    html = '<html><body><p>No navigation</p></body></html>'
    next_url = find_next_page_link(html, "https://example.com/page1")
    assert next_url is None
