"""Tests for scraping orchestrator."""
import pytest
from src.scraper.scraper import ScrapingStats

def test_scraping_stats():
    """Test scraping stats object."""
    stats = ScrapingStats()
    assert stats.pages_scraped == 0
    assert stats.posts_found == 0
    assert len(stats.errors) == 0
    
    stats.pages_scraped = 5
    stats.posts_found = 25
    stats.errors.append("test error")
    
    data = stats.to_dict()
    assert data["pages_scraped"] == 5
    assert data["posts_found"] == 25
    assert len(data["errors"]) == 1
