# Blog Post Scraper

> ⚠️ **EXPERIMENTAL PROJECT - NOT FOR PRODUCTION USE**
>
> This is an experimental project for **personal local use only**. Built for research and learning purposes. May contain bugs, security vulnerabilities, or unexpected behavior. **Do not deploy to production environments. Use at your own risk for educational purposes only.**

---

A web scraping system for extracting blog posts with pagination support, rate limiting, and comprehensive security features.

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

## How It Works

The scraper uses a **two-phase approach** to extract full blog post content:

**Phase 1: Collect Post URLs**
1. **API Request** - Submit blog URL via REST API (FastAPI endpoint)
2. **Browser Automation** - Playwright launches headless Chromium, navigates to URL, waits for JavaScript
3. **Listing Page Parsing** - BeautifulSoup extracts post URLs and metadata from listing pages
4. **Pagination** - Automatically detects "Next" links and follows them (up to 10 pages)

**Phase 2: Fetch Full Content**
5. **Individual Post Fetching** - Visits each post URL to extract complete article content
6. **Content Merging** - Combines listing metadata with full post content
7. **Storage** - Saves posts to SQLite database via SQLAlchemy async ORM

**Key Features**: Two-phase scraping (full content, not just teasers), rate limiting (2-5s random delays), retry logic (4 attempts with exponential backoff), SSRF prevention (blocks localhost/private IPs).

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

### Complete Workflow Example

```bash
# 1. Start the server
python -m uvicorn src.main:app --host 127.0.0.1 --port 8001

# 2. Create scraping job
curl -X POST http://127.0.0.1:8001/api/jobs/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/blog/"}'

# Response: {"id": "550e8400-...", "status": "pending", ...}

# 3. Check job status (wait ~60 seconds for completion)
curl http://127.0.0.1:8001/api/jobs/550e8400-...

# 4. Get scraped posts
curl "http://127.0.0.1:8001/api/posts/?limit=10"

# 5. Export all posts to JSON file
curl "http://127.0.0.1:8001/api/posts/export/json" > posts.json
```

### UI Usage

**Primary interface**: API (use examples above)

**Interactive API docs**: http://127.0.0.1:8001/docs (Swagger UI - recommended for exploration)

**Basic web UI**: http://127.0.0.1:8001/static/index.html (if available, limited functionality)

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

## Documentation

For detailed usage instructions, examples, and API reference:

📚 **[View Full Documentation →](docs/README.md)**

- [Quick Start Guide](docs/QUICK_START.md) - Get started in 5 minutes
- [Complete Usage Guide](docs/USAGE.md) - All features and examples
- [API Reference](http://localhost:8001/docs) - Interactive Swagger docs

## Recent Test Results

✅ **HVAC Blog** - 50 posts with full content from 10 pages
✅ **Tech Blog** - 14 posts from 3 pages

## License

Educational and non-commercial use only.

---

Built with Python and FastAPI
