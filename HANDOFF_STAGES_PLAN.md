# Handoff Stages Plan: Blog Post Scraper

## Overview
- **Total Stages:** 6
- **Estimated Completion:** 12-16 hours
- **Approach:** Horizontal (layered) - MVP web app with clear separation of concerns
- **Tier:** STANDARD (includes performance testing, no extensive security validation)

---

## Stage 1: Project Setup & Environment (Complexity: 6)

**Goal:** Initialize project structure, dependencies, and Docker environment

**Complexity Breakdown:**
- Files: 2pts (6-10 files: requirements.txt, Dockerfile, .gitignore, README, config.py, main.py)
- Integration: 1pt (0-1 external: Playwright install)
- Logic: 1pt (trivial boilerplate)
- Domain: 0pts (no business logic)
- Boilerplate: 2pts (moderate setup code)
- **Total: 6**

### Task 1.1: Initialize Project Structure
- [ ] Create project directory structure:
  - `src/scraper/` - Core scraping logic
  - `src/api/` - FastAPI endpoints
  - `src/models/` - Database models
  - `src/static/` - HTML/CSS/JS files
  - `tests/` - Test directory
- [ ] Create `requirements.txt` with dependencies: fastapi, uvicorn, playwright, beautifulsoup4, httpx, sqlalchemy, pydantic, pytest, structlog
- [ ] Create `.gitignore` for Python (venv, __pycache__, *.pyc, .env, *.db)
- [ ] Create `README.md` with project description
- [ ] Git commit: "Task 1.1: Initialize project structure"

### Task 1.2: Docker Configuration
- [ ] Create `Dockerfile` with Python 3.11-slim base
- [ ] Install Playwright browsers: `playwright install --with-deps chromium`
- [ ] Add COPY commands for requirements and source code
- [ ] Set WORKDIR to `/app`
- [ ] Add CMD to run Uvicorn server
- [ ] Create `.dockerignore` file
- [ ] Test Docker build: `docker build -t blog-scraper:latest .`
- [ ] Git commit: "Task 1.2: Add Docker configuration"

### Task 1.3: Configuration & Environment
- [ ] Create `src/config.py` with settings (database URL, scraping config)
- [ ] Add environment variable support with defaults
- [ ] Create `.env.example` file
- [ ] Add logging configuration (structlog setup)
- [ ] Git commit: "Task 1.3: Configure environment and logging"

**Acceptance Criteria:**
Links to PRD: Foundation for all user stories

**Stage 1 Complete When:**
- All tasks checked off
- `docker build` succeeds without errors
- `requirements.txt` installs all dependencies
- Project structure follows best practices

---

## Stage 2: Database & Models (Complexity: 7)

**Goal:** Set up SQLite database with SQLAlchemy models

**Complexity Breakdown:**
- Files: 2pts (3-5 files: models.py, database.py, schemas.py)
- Integration: 2pts (2 integrations: SQLAlchemy, Pydantic)
- Logic: 2pts (basic ORM logic)
- Domain: 1pt (simple domain: scraped posts, jobs)
- Boilerplate: 0pts
- **Total: 7**

### Task 2.1: Database Setup
- [ ] Create `src/database.py` with SQLAlchemy engine and session factory
- [ ] Configure SQLite database URL: `sqlite:///./blog_scraper.db`
- [ ] Add async session support
- [ ] Create database initialization function
- [ ] Add alembic for migrations (optional for MVP, comment for future)
- [ ] Git commit: "Task 2.1: Setup database connection"

### Task 2.2: Data Models
- [ ] Create `src/models/blog_post.py` with BlogPost model:
  - id (UUID primary key)
  - blog_url (String)
  - title (String)
  - author (String, nullable)
  - published_date (DateTime, nullable)
  - content (Text)
  - excerpt (String, nullable)
  - images (JSON array)
  - scraped_at (DateTime)
- [ ] Create `src/models/scraping_job.py` with ScrapingJob model:
  - id (UUID primary key)
  - blog_url (String)
  - status (Enum: pending, in_progress, completed, failed)
  - pages_scraped (Integer)
  - posts_found (Integer)
  - error_message (Text, nullable)
  - created_at (DateTime)
  - completed_at (DateTime, nullable)
- [ ] Add indexes: blog_url, created_at, status
- [ ] Git commit: "Task 2.2: Define database models"

### Task 2.3: Pydantic Schemas
- [ ] Create `src/schemas.py` with Pydantic schemas:
  - `BlogPostCreate`, `BlogPostResponse`
  - `ScrapingJobCreate`, `ScrapingJobResponse`
  - `URLInput` with validation
- [ ] Add URL validation regex (http/https only)
- [ ] Add example values for API docs
- [ ] Write unit tests for schema validation
- [ ] Git commit: "Task 2.3: Add Pydantic schemas with validation"

**Acceptance Criteria:**
Links to PRD: US-05 (view results), US-06 (export JSON)

**Stage 2 Complete When:**
- All models defined
- Database file created on first run
- Tests pass for schemas
- Can insert/query test data

---

## Stage 3: Core Scraping Engine (Complexity: 12)

**Goal:** Implement web scraping with Playwright and BeautifulSoup

**Complexity Breakdown:**
- Files: 3pts (6-10 files: scraper.py, parser.py, fetcher.py, rate_limiter.py, url_validator.py)
- Integration: 3pts (3-4: Playwright, BeautifulSoup, httpx, async)
- Logic: 4pts (complex: pagination, parsing, error handling)
- Domain: 2pts (moderate: blog post extraction logic)
- Boilerplate: 0pts
- **Total: 12**

### Task 3.1: URL Validator
- [ ] Create `src/scraper/url_validator.py`
- [ ] Implement `validate_url(url: str)` function:
  - Reject file://, javascript:, data://, localhost
  - Only allow http:// and https://
  - Check URL format with urllib.parse
- [ ] Add tests for valid/invalid URLs
- [ ] Git commit: "Task 3.1: Implement URL validator (SEC-01)"

### Task 3.2: Rate Limiter
- [ ] Create `src/scraper/rate_limiter.py`
- [ ] Implement `RateLimiter` class with async delay method
- [ ] Random delay between 2-5 seconds (configurable)
- [ ] Add last_request_time tracking
- [ ] Write tests for delay timing
- [ ] Git commit: "Task 3.2: Implement rate limiter for human-like behavior"

### Task 3.3: HTML Fetcher
- [ ] Create `src/scraper/fetcher.py`
- [ ] Implement `fetch_page(url)` using Playwright:
  - Launch headless browser
  - Navigate to URL with timeout (30s)
  - Wait for network idle
  - Return page HTML
  - Handle errors gracefully
- [ ] Add retry logic (3 attempts with exponential backoff)
- [ ] Integrate rate limiter (delay before each request)
- [ ] Add user agent rotation (3-5 common user agents)
- [ ] Write integration tests with mock HTML
- [ ] Git commit: "Task 3.3: Implement HTML fetcher with Playwright"

### Task 3.4: HTML Parser
- [ ] Create `src/scraper/parser.py`
- [ ] Implement `parse_blog_post(html, url)` using BeautifulSoup:
  - Extract title (try h1, .title, article h1)
  - Extract author (try .author, .byline, meta[name="author"])
  - Extract date (try time, .date, meta[property="article:published_time"])
  - Extract content (try article, .content, .post-content)
  - Extract excerpt (first 200 chars of content)
  - Extract images (all img src in content)
  - Handle missing fields gracefully (return None)
- [ ] Implement `find_next_page_link(html)`:
  - Look for "next", "→", page numbers
  - Return absolute URL or None
- [ ] Write tests with sample HTML fixtures
- [ ] Git commit: "Task 3.4: Implement HTML parser with BeautifulSoup"

### Task 3.5: Scraping Orchestrator
- [ ] Create `src/scraper/scraper.py`
- [ ] Implement `scrape_blog(blog_url, max_pages=10)` function:
  - Validate URL
  - Track visited URLs (prevent loops)
  - For each page up to max_pages:
    - Fetch page with rate limiting
    - Parse blog posts
    - Save to database
    - Find next page link
    - Break if no more pages
  - Return scraping statistics (pages, posts, errors)
- [ ] Add error handling with detailed logging
- [ ] Return ScrapingJob object with status
- [ ] Write integration test: scrape 3 pages
- [ ] Git commit: "Task 3.5: Implement scraping orchestrator"

**Acceptance Criteria:**
Links to PRD: US-01, US-02 (pagination), US-03 (rate limiting), US-04 (URL validation)

**Stage 3 Complete When:**
- All tasks checked off
- Can scrape a test blog successfully
- Tests passing (coverage >80%)
- Rate limiting verified (2-5s delays)

---

## Stage 4: FastAPI Backend & API Endpoints (Complexity: 10)

**Goal:** Create REST API with FastAPI for web UI

**Complexity Breakdown:**
- Files: 2pts (3-5 files: main.py, routes/jobs.py, routes/posts.py)
- Integration: 2pts (2: FastAPI, async database)
- Logic: 3pts (moderate: CRUD operations, job management)
- Domain: 2pts (moderate: API business logic)
- Boilerplate: 1pt (minimal FastAPI boilerplate)
- **Total: 10**

### Task 4.1: FastAPI Setup
- [ ] Create `src/main.py` with FastAPI app initialization
- [ ] Add CORS middleware (allow localhost for development)
- [ ] Add exception handlers (404, 500, validation errors)
- [ ] Configure static files serving (/static)
- [ ] Add startup event: create database tables
- [ ] Add health check endpoint: `GET /health`
- [ ] Git commit: "Task 4.1: Initialize FastAPI application"

### Task 4.2: Job Management Endpoints
- [ ] Create `src/api/routes/jobs.py`
- [ ] POST `/api/jobs` - Create new scraping job:
  - Validate URL input
  - Create ScrapingJob in database (status: pending)
  - Trigger async scraping task
  - Return job ID
- [ ] GET `/api/jobs` - List all jobs (paginated, limit=50)
- [ ] GET `/api/jobs/{job_id}` - Get job details
- [ ] DELETE `/api/jobs/{job_id}` - Delete job and associated posts
- [ ] Add OpenAPI documentation with examples
- [ ] Write API tests with httpx
- [ ] Git commit: "Task 4.2: Implement job management API"

### Task 4.3: Results Endpoints
- [ ] Create `src/api/routes/posts.py`
- [ ] GET `/api/posts` - List scraped posts (paginated):
  - Query params: blog_url, limit, offset
  - Return posts with metadata
- [ ] GET `/api/posts/{post_id}` - Get single post details
- [ ] GET `/api/posts/export` - Export all posts as JSON:
  - Return downloadable JSON file
  - Include all post fields
- [ ] Add tests for all endpoints
- [ ] Git commit: "Task 4.3: Implement results API"

### Task 4.4: Async Job Execution
- [ ] Create `src/api/background_tasks.py`
- [ ] Implement `run_scraping_job(job_id)` as FastAPI background task:
  - Update job status to in_progress
  - Call scraper.scrape_blog()
  - Save posts to database
  - Update job status to completed/failed
  - Log errors if any
- [ ] Limit concurrent jobs to 3 (PERF-03)
- [ ] Add job queue if needed (simple list for MVP)
- [ ] Git commit: "Task 4.4: Implement async job execution"

**Acceptance Criteria:**
Links to PRD: US-01 (start job), US-05 (view results), US-06 (export JSON)

**Stage 4 Complete When:**
- All API endpoints working
- Background jobs execute successfully
- Tests passing
- API docs generated automatically

---

## Stage 5: Web UI (Complexity: 9)

**Goal:** Build simple web UI with Bootstrap

**Complexity Breakdown:**
- Files: 3pts (6-10 files: HTML templates, CSS, JS)
- Integration: 1pt (0-1: Bootstrap CDN)
- Logic: 3pts (moderate: JS for API calls, DOM manipulation)
- Domain: 1pt (simple: form submission, table display)
- Boilerplate: 1pt (minimal HTML/CSS)
- **Total: 9**

### Task 5.1: Home Page - Job Submission
- [ ] Create `src/static/index.html`:
  - Bootstrap navbar
  - Form with URL input and "Start Scraping" button
  - Max pages slider (1-20, default 10)
  - Job status section (shows active jobs)
- [ ] Create `src/static/css/styles.css` for custom styles
- [ ] Create `src/static/js/app.js`:
  - Handle form submission (POST /api/jobs)
  - Display success/error messages
  - Update job status section dynamically
- [ ] Add URL validation on client side (regex)
- [ ] Add loading spinner during submission
- [ ] Git commit: "Task 5.1: Create home page UI"

### Task 5.2: Results Page - View Scraped Posts
- [ ] Create `src/static/results.html`:
  - Bootstrap table or cards for posts
  - Columns: Title, Author, Date, Blog URL, Actions
  - Pagination controls (prev/next)
  - Filter by blog URL dropdown
  - "Export JSON" button
- [ ] Create `src/static/js/results.js`:
  - Fetch posts from API (GET /api/posts)
  - Render posts in table/cards
  - Handle pagination
  - Implement filter
  - Handle export button (download JSON)
- [ ] Add loading state while fetching
- [ ] Git commit: "Task 5.2: Create results page UI"

### Task 5.3: Jobs Page - Monitor Scraping Jobs
- [ ] Create `src/static/jobs.html`:
  - Bootstrap table for jobs
  - Columns: Blog URL, Status, Pages, Posts, Created, Actions
  - Auto-refresh every 5s for active jobs
  - Delete button for each job
- [ ] Create `src/static/js/jobs.js`:
  - Fetch jobs from API (GET /api/jobs)
  - Render jobs table
  - Auto-refresh active jobs
  - Handle delete action
  - Color-code status (green=completed, yellow=in_progress, red=failed)
- [ ] Git commit: "Task 5.3: Create jobs monitoring page"

**Acceptance Criteria:**
Links to PRD: US-01 (submit URL), US-05 (view results), US-06 (export)

**Stage 5 Complete When:**
- All 3 pages working
- Can submit jobs via UI
- Can view results in UI
- Can export JSON
- UI is responsive (mobile-friendly)

---

## Stage 6: Testing, Documentation & Finalization (Complexity: 8)

**Goal:** Comprehensive testing, documentation, and deployment prep

**Complexity Breakdown:**
- Files: 2pts (3-5 files: tests, README, docs)
- Integration: 1pt (0-1: pytest-benchmark)
- Logic: 2pts (basic: test scenarios)
- Domain: 1pt (simple: test cases)
- Boilerplate: 2pts (moderate: documentation)
- **Total: 8**

### Task 6.1: Unit & Integration Tests
- [ ] Write unit tests for URL validator (10+ test cases)
- [ ] Write unit tests for HTML parser (20+ test cases with fixtures)
- [ ] Write integration tests for scraper with mock HTML
- [ ] Write API tests for all endpoints (30+ test cases)
- [ ] Achieve >80% test coverage
- [ ] Run: `pytest --cov=src tests/`
- [ ] Git commit: "Task 6.1: Add comprehensive test suite"

### Task 6.2: Performance Testing
- [ ] Create `tests/test_performance.py` with pytest-benchmark
- [ ] Benchmark scraping speed (PERF-02: <5s per page)
- [ ] Benchmark API response times (PERF-01: <500ms)
- [ ] Test concurrent jobs (PERF-03: 3 jobs)
- [ ] Measure resource usage (PERF-05: <1GB RAM)
- [ ] Document performance results in README
- [ ] Git commit: "Task 6.2: Add performance benchmarks"

### Task 6.3: README & Documentation
- [ ] Update README.md with:
  - Project description and features
  - Installation instructions (Docker + local)
  - Usage examples (how to run, access UI)
  - API documentation link
  - Configuration options (.env vars)
  - Testing instructions
  - Troubleshooting guide
  - Screenshots of UI (optional for MVP)
- [ ] Create `DEPLOYMENT.md` with Docker instructions
- [ ] Add inline code comments for complex logic
- [ ] Git commit: "Task 6.3: Complete documentation"

### Task 6.4: Final Integration Testing
- [ ] Run full Docker build: `docker build -t blog-scraper:latest .`
- [ ] Run container: `docker run -p 8000:8000 blog-scraper:latest`
- [ ] Test all user stories end-to-end:
  - US-01: Submit blog URL via UI ✓
  - US-02: Verify pagination works ✓
  - US-03: Verify 2-5s delays between requests ✓
  - US-04: Verify malicious URLs rejected ✓
  - US-05: View results in UI ✓
  - US-06: Export JSON works ✓
- [ ] Verify performance requirements:
  - PERF-01: API <500ms ✓
  - PERF-02: Scraping <5s/page ✓
  - PERF-03: 3 concurrent jobs ✓
  - PERF-05: <1GB RAM ✓
- [ ] Fix any bugs found
- [ ] Git commit: "Task 6.4: Final integration testing and bug fixes"

**Acceptance Criteria:**
Links to PRD: ALL user stories (US-01 through US-06), ALL performance requirements (PERF-01 through PERF-05)

**Stage 6 Complete When:**
- All tests passing (>80% coverage)
- Performance benchmarks meet targets
- Documentation complete
- Docker build succeeds
- End-to-end test passes
- All 6 user stories verified

---

## Completion Checklist

- [ ] All 6 stages complete
- [ ] All tests passing (pytest)
- [ ] Docker build succeeds
- [ ] README is comprehensive
- [ ] Performance benchmarks meet targets (PERF-01 through PERF-05)
- [ ] All 6 user stories verified (US-01 through US-06)
- [ ] Security requirements met (URL validation, input sanitization)
- [ ] Web UI is functional and responsive
- [ ] Export JSON works correctly
- [ ] Rate limiting verified (2-5s delays)

**Estimated Total Time:** 12-16 hours
**Total Checkboxes:** 98
**Project Ready for:** MVP deployment and user testing

---

**Document Version:** 1.0
**Last Updated:** 2026-01-15
**Status:** Draft - Ready for Review
**Generated by:** Tech-Lead Agent v1.0
