# Blog Scraper - Usage Guide

## Quick Start

### 1. Start the Server

```bash
cd /home/bartek/test-blog-scraper
python -m uvicorn src.main:app --host 127.0.0.1 --port 8001
```

Server will be available at: `http://127.0.0.1:8001`

---

## API Usage

### Create Scraping Job

**Endpoint:** `POST /api/jobs/`

```bash
curl -X POST http://127.0.0.1:8001/api/jobs/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/blog/"}'
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "blog_url": "https://example.com/blog/",
  "status": "pending",
  "pages_scraped": 0,
  "posts_found": 0,
  "created_at": "2026-01-15T20:00:00"
}
```

**What happens:**
- Job is created and immediately starts scraping in the background
- Scraper fetches up to 10 pages following "Next" links
- Extracts all posts from each page (typically 5-10 posts per page)
- Rate limits: 2-5 second delays between pages (human-like behavior)

---

### Check Job Status

**Endpoint:** `GET /api/jobs/{job_id}`

```bash
curl http://127.0.0.1:8001/api/jobs/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "blog_url": "https://example.com/blog/",
  "status": "completed",
  "pages_scraped": 10,
  "posts_found": 47,
  "error_message": null,
  "completed_at": "2026-01-15T20:01:30"
}
```

**Job Status:**
- `pending` - Job created, not started yet
- `in_progress` - Currently scraping
- `completed` - Finished successfully
- `failed` - Error occurred (check `error_message`)

---

### List All Jobs

**Endpoint:** `GET /api/jobs/`

```bash
curl "http://127.0.0.1:8001/api/jobs/?limit=10&offset=0"
```

---

### Get Scraped Posts

**Endpoint:** `GET /api/posts/`

```bash
# Get first 10 posts
curl "http://127.0.0.1:8001/api/posts/?limit=10&offset=0"
```

**Response:**
```json
{
  "items": [
    {
      "id": "...",
      "blog_url": "https://example.com/blog/",
      "title": "How to Build a Web Scraper",
      "author": "John Doe",
      "published_date": "2026-01-15T10:00:00",
      "content": "Full article content here...",
      "excerpt": "First 200 characters...",
      "images": [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg"
      ],
      "scraped_at": "2026-01-15T20:00:15"
    }
  ],
  "total": 47,
  "limit": 10,
  "offset": 0
}
```

**Pagination:**
- Use `limit` and `offset` to paginate results
- Example: `?limit=10&offset=20` (skip first 20, get next 10)

---

### Export Posts to JSON

**Endpoint:** `GET /api/posts/export/json`

```bash
curl "http://127.0.0.1:8001/api/posts/export/json" > scraped_posts.json
```

Returns all scraped posts with metadata in JSON format.

---

## UI Usage

**Status:** UI not implemented yet

The system currently provides API-only access. Recommended tools:
- **Postman** - For interactive API testing
- **curl** - For command-line usage
- **Swagger UI** - Built-in at `http://127.0.0.1:8001/docs`

---

## Interactive API Docs

FastAPI provides automatic interactive documentation:

**Swagger UI:** `http://127.0.0.1:8001/docs`
- Try out endpoints directly in the browser
- See request/response schemas
- No authentication required

**ReDoc:** `http://127.0.0.1:8001/redoc`
- Alternative documentation format
- Better for reading/reference

---

## How It Works

### Scraping Process

1. **Browser Automation** - Uses Playwright (headless Chrome) to fetch pages
2. **JavaScript Execution** - Waits for dynamic content to load
3. **HTML Parsing** - BeautifulSoup extracts posts from article containers
4. **Pagination** - Automatically follows "Next" links (up to 10 pages)
5. **Multi-Post Extraction** - Finds all posts on listing pages (not just first one)
6. **Rate Limiting** - Random 2-5s delays to avoid IP bans
7. **Storage** - Saves to local SQLite database

### What Gets Extracted

From each post:
- ✅ Title
- ✅ Author (if available)
- ✅ Publication date (if available)
- ✅ Full content text
- ✅ Excerpt (first 200 chars)
- ✅ All images with URLs
- ✅ Source URL

### Security Features

- **SSRF Prevention** - Blocks localhost, private IPs, dangerous protocols
- **URL Validation** - Only allows http/https schemes
- **Error Handling** - 3-layer retry logic with exponential backoff

---

## Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# Server settings
HOST=127.0.0.1
PORT=8001

# Scraping limits
MAX_CONCURRENT_JOBS=3
MAX_PAGES_PER_JOB=10

# Database
DATABASE_URL=sqlite:///./blog_scraper.db
```

### Max Concurrent Jobs

Default: 3 simultaneous scraping jobs

To change: Update `MAX_CONCURRENT_JOBS` in `.env` or `src/config.py`

---

## Examples

### Scrape HVAC Blog

```bash
# 1. Create job
JOB_ID=$(curl -s -X POST http://127.0.0.1:8001/api/jobs/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/blog/"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo "Job created: $JOB_ID"

# 2. Wait for completion (check every 5 seconds)
while true; do
  STATUS=$(curl -s http://127.0.0.1:8001/api/jobs/$JOB_ID \
    | python -c "import sys, json; print(json.load(sys.stdin)['status'])")

  echo "Status: $STATUS"

  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi

  sleep 5
done

# 3. Get results
curl -s http://127.0.0.1:8001/api/jobs/$JOB_ID | python -m json.tool
```

**Expected Result:**
- ~50 posts scraped
- ~10 pages traversed
- Completes in ~60 seconds

---

## Troubleshooting

### Job Stuck in "pending" Status

**Cause:** Background task might not be triggered

**Fix:** Restart the server:
```bash
# Stop server (Ctrl+C)
# Start again
python -m uvicorn src.main:app --host 127.0.0.1 --port 8001
```

### "Address already in use" Error

**Cause:** Port 8001 is occupied

**Fix:**
```bash
# Kill process on port 8001
lsof -ti:8001 | xargs kill -9

# Or use different port
python -m uvicorn src.main:app --host 127.0.0.1 --port 9000
```

### No Posts Found

**Possible causes:**
- Blog has unusual HTML structure
- JavaScript-heavy site (Playwright should handle this)
- Invalid pagination links

**Debug:**
- Check job `error_message` field
- Look at server logs
- Try scraping manually: `curl https://example.com/blog/`

### Rate Limiting by Target Site

**Symptoms:** Slow scraping, 429 errors

**Fix:** System already implements 2-5s delays. If still blocked:
- Reduce `MAX_CONCURRENT_JOBS` to 1
- Wait longer between scraping same site

---

## Tech Stack

- **Python 3.11+** - Core language
- **FastAPI** - Web framework
- **Playwright** - Browser automation (headless Chrome)
- **BeautifulSoup4** - HTML parsing
- **SQLAlchemy** - Database ORM
- **SQLite** - Local database
- **Pydantic** - Data validation
- **structlog** - Structured logging

**Cost:** $0 - All free and open-source

---

## Limits

- **Max Pages:** 10 pages per job (configurable)
- **Max Concurrent Jobs:** 3 (configurable)
- **Rate Limiting:** 2-5 second delays (not configurable)
- **Timeout:** 30 seconds per page fetch
- **Retries:** 4 attempts per page (with exponential backoff)

---

## Next Steps

1. **Test on your blog:** Try scraping your target blog
2. **Check the data:** Verify extracted posts have good quality
3. **Export results:** Use `/api/posts/export/json` endpoint
4. **Build UI:** (Optional) Create frontend for job management
5. **Production deployment:** Add PostgreSQL, Redis, monitoring

For questions or issues, check the main README.md
