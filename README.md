# Blog Post Scraper

A production-ready web scraping system for extracting blog posts with pagination support, rate limiting, and comprehensive security features.

## Features

- **Intelligent Scraping**: Automatically follows pagination links to scrape multiple pages
- **Human-like Behavior**: Rate limiting (2-5s delays) prevents IP bans and mimics human browsing
- **Security First**: SSRF prevention, URL validation, output sanitization
- **Modern UI**: Bootstrap-based web interface for job management and results viewing
- **RESTful API**: FastAPI backend with async support
- **Export Functionality**: Export scraped posts to JSON format
- **Comprehensive Testing**: 106 tests covering functionality and performance

## Tech Stack

- **Python 3.11+**: Modern async/await patterns
- **FastAPI**: High-performance async web framework
- **Playwright**: Browser automation for JavaScript-heavy sites
- **SQLAlchemy**: Async ORM with SQLite database
- **BeautifulSoup**: HTML parsing and content extraction
- **Pydantic**: Data validation and settings management
- **structlog**: Structured logging for debugging

## Quick Start

### Prerequisites

- Python 3.11 or higher
- pip package manager
- 2GB+ RAM recommended

### Installation

1. Clone the repository
2. Create virtual environment: python -m venv venv
3. Activate: source venv/bin/activate
4. Install dependencies: pip install -r requirements.txt
5. Install Playwright: playwright install chromium
6. Start server: uvicorn src.main:app --reload

### Access

- Web UI: http://localhost:8000/static/index.html
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## API Usage

### Create Job
```bash
curl -X POST http://localhost:8000/api/jobs/ -H "Content-Type: application/json" -d '{"url": "https://example.com/blog"}'
```

### List Jobs
```bash
curl http://localhost:8000/api/jobs/
```

### List Posts
```bash
curl http://localhost:8000/api/posts/
```

### Export JSON
```bash
curl http://localhost:8000/api/posts/export/json > posts.json
```

## Configuration

Set via environment variables or .env file:

- DATABASE_URL=sqlite:///./blog_scraper.db
- LOG_LEVEL=INFO
- MIN_DELAY=2.0
- MAX_DELAY=5.0
- MAX_CONCURRENT_JOBS=3

## Testing

```bash
pytest                           # Run all tests
pytest --cov=src                # With coverage
pytest tests/test_performance.py  # Performance tests only
```

Test Coverage: 106 tests total
- URL Validation: 33 tests
- Rate Limiter: 14 tests
- Fetcher: 10 tests
- API Routes: 11 tests
- Models: 7 tests
- Performance: 7 tests
- Others: 24 tests

## Security

- SSRF prevention (blocks localhost, private IPs)
- URL validation (blocks dangerous schemes)
- Rate limiting (prevents abuse)
- Input validation (Pydantic schemas)
- SQL injection prevention
- XSS prevention

## Performance Benchmarks

- URL Validation: < 10ms per URL
- Rate Limiter Overhead: < 50ms
- Concurrent Throughput: > 100 URLs/s
- Error Handling: < 15ms per error

## Architecture

- src/api/: FastAPI routes and background tasks
- src/models/: SQLAlchemy database models
- src/scraper/: Core scraping logic
- src/static/: Web UI (HTML/CSS/JS)
- tests/: Comprehensive test suite

## Troubleshooting

**Playwright not found**: playwright install chromium
**Module errors**: pip install -r requirements.txt
**Database locked**: Delete blog_scraper.db and restart
**Slow scraping**: Adjust MIN_DELAY and MAX_DELAY

Enable debug logging: LOG_LEVEL=DEBUG

## License

Educational and non-commercial use only.

---

Built with Python and FastAPI
