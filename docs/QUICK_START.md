# Quick Start - Blog Scraper

## Installation & Setup

```bash
# 1. Install dependencies
cd /home/bartek/test-blog-scraper
pip install -r requirements.txt

# 2. Install Playwright browsers
playwright install chromium

# 3. Start server
python -m uvicorn src.main:app --host 127.0.0.1 --port 8001
```

---

## Basic Usage (3 Steps)

### 1. Create Scraping Job

```bash
curl -X POST http://127.0.0.1:8001/api/jobs/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.goodway.com/hvac-blog/"}'
```

**Returns:** Job ID (copy it!)

### 2. Check Status

```bash
curl http://127.0.0.1:8001/api/jobs/{JOB_ID}
```

**Wait for:** `"status": "completed"`

### 3. Get Results

```bash
curl "http://127.0.0.1:8001/api/posts/?limit=10"
```

---

## One-Liner Examples

**Scrape blog and wait for results:**
```bash
JOB=$(curl -s -X POST http://127.0.0.1:8001/api/jobs/ -H "Content-Type: application/json" -d '{"url": "https://example.com/blog/"}' | python -c "import sys,json; print(json.load(sys.stdin)['id'])") && \
sleep 30 && \
curl -s http://127.0.0.1:8001/api/jobs/$JOB | python -m json.tool
```

**Export all posts to file:**
```bash
curl "http://127.0.0.1:8001/api/posts/export/json" > scraped_posts.json
```

**Count total posts:**
```bash
curl -s "http://127.0.0.1:8001/api/posts/?limit=1" | python -c "import sys,json; print(f\"Total posts: {json.load(sys.stdin)['total']}\")"
```

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/jobs/` | Create new scraping job |
| GET | `/api/jobs/` | List all jobs |
| GET | `/api/jobs/{id}` | Get job status |
| GET | `/api/posts/` | List scraped posts |
| GET | `/api/posts/export/json` | Export all posts |
| GET | `/health` | Check server health |
| GET | `/docs` | Interactive API docs |

---

## What It Does

- ✅ Scrapes blog posts automatically
- ✅ Follows pagination links (up to 10 pages)
- ✅ Extracts: title, author, date, content, images
- ✅ Rate limits: 2-5s delays (polite scraping)
- ✅ Handles JavaScript-rendered pages
- ✅ 100% free (no paid APIs)

---

## How Long Does It Take?

- **1 page:** ~5-10 seconds
- **10 pages:** ~40-60 seconds
- **Goodway blog (51 posts):** ~60 seconds
- **Droptica blog (14 posts):** ~20 seconds

---

## Tested Blogs

✅ **Goodway HVAC** - 51 posts scraped successfully
✅ **Droptica AI** - 14 posts scraped successfully

Works with most WordPress, Ghost, Medium, and custom blog platforms.

---

## Need Help?

- **Full docs:** See `USAGE.md`
- **Interactive API:** Visit `http://127.0.0.1:8001/docs`
- **Logs:** Check terminal output for errors
