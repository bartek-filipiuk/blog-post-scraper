# Documentation

## Available Guides

### 📘 [QUICK_START.md](QUICK_START.md)
**Start here!** - Installation, basic usage, and common commands.

Perfect for: First-time users who want to scrape a blog in 5 minutes.

### 📗 [USAGE.md](USAGE.md)
**Complete reference** - All API endpoints, examples, configuration, and troubleshooting.

Perfect for: Understanding all features and customization options.

---

## What This Scraper Does

Automatically scrapes blog posts from any blog website:

- **Pagination** - Follows "Next" links (up to 10 pages)
- **Multi-post extraction** - Gets all posts from listing pages
- **Rich metadata** - Title, author, date, content, images
- **JavaScript support** - Uses Playwright browser automation
- **Rate limiting** - Polite 2-5s delays between requests
- **SSRF protection** - Blocks dangerous URLs
- **Free & open-source** - No paid APIs required

---

## Quick Example

```bash
# Start server
python -m uvicorn src.main:app --host 127.0.0.1 --port 8001

# Scrape a blog
curl -X POST http://127.0.0.1:8001/api/jobs/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/blog/"}'

# Check results at http://127.0.0.1:8001/docs
```

---

## Architecture

```
┌─────────────┐
│  FastAPI    │  ← REST API endpoints
└─────┬───────┘
      │
┌─────▼────────┐
│  Background  │  ← Async job execution
│    Tasks     │
└─────┬────────┘
      │
┌─────▼────────┐
│   Scraper    │  ← Orchestrates fetch + parse
└─────┬────────┘
      │
  ┌───▼───┬──────────┐
  │       │          │
┌─▼─────┐ │  ┌───────▼──┐
│Fetcher│ │  │  Parser  │
│(Play- │ │  │(Beautiful│
│wright)│ │  │  Soup)   │
└───────┘ │  └──────────┘
          │
    ┌─────▼────┐
    │  SQLite  │  ← Local database
    └──────────┘
```

---

## Tech Stack

- Python 3.11+
- FastAPI (web framework)
- Playwright (browser automation)
- BeautifulSoup4 (HTML parsing)
- SQLAlchemy (database ORM)
- SQLite (database)

**Total cost:** $0

---

## Tested On

- ✅ HVAC blog - 50 posts
- ✅ Droptica AI blog - 14 posts
- ✅ WordPress sites
- ✅ Custom blog platforms

---

## Limits

- Max 10 pages per job (configurable)
- Max 3 concurrent jobs (configurable)
- 2-5s delay between pages (not configurable)
- Local SQLite database (upgrade to PostgreSQL for production)

---

## Next Steps

1. Read [QUICK_START.md](QUICK_START.md) to get started
2. Try scraping a blog
3. Check [USAGE.md](USAGE.md) for advanced features
4. Build your own UI (optional)
