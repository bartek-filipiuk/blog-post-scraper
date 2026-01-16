# Scaling Analysis: Scraping 146 Pages (730 Posts)

## Executive Summary

**Current System:** Designed for **10 pages max**
**Target:** 146 pages × 5 posts/page = **730 posts**
**Verdict:** ⚠️ **Will NOT work without modifications**

---

## Critical Problems

### 🔴 PROBLEM 1: Hardcoded 10-Page Limit

**Location:** `src/api/background_tasks.py:44`

```python
posts, stats = await scrape_blog(job.blog_url, max_pages=10)
```

**Impact:** Even if you set `max_pages=146` in config, the background task **ignores it** and only scrapes 10 pages.

**Why it exists:** Line 44 hardcodes `max_pages=10` instead of reading from settings.

**Fix Required:**
```python
posts, stats = await scrape_blog(job.blog_url, max_pages=settings.max_pages_default)
```

---

### 🔴 PROBLEM 2: Config Validation Limits max_pages to 100

**Location:** `src/config.py:19-24`

```python
max_pages_default: int = Field(
    default=10,
    ge=1,
    le=100,  # ← BLOCKS values > 100
    description="Default maximum pages to scrape per job"
)
```

**Impact:** Even if you fix Problem 1, you can't set `max_pages=146` because config validation fails.

**Error you'd get:**
```
validation error for Settings
max_pages_default
  Input should be less than or equal to 100
```

**Fix Required:**
```python
le=200,  # Change from 100 to 200
```

---

### 🟠 PROBLEM 3: Memory Explosion

**Location:** `src/scraper/scraper.py:48`

```python
posts = []  # All posts stored in memory
```

**What happens with 146 pages:**

1. **730 dict objects** in `posts` list
2. Each dict contains:
   - `title` (avg 50 chars)
   - `content` (avg 5,000 chars)
   - `excerpt` (200 chars)
   - `images` (list of 5 URLs, 100 chars each)
   - `author` (30 chars)
   - metadata (~100 chars)

**Memory calculation:**
- Per post: ~5,500 chars × 2 bytes (Unicode) = **11 KB**
- 730 posts × 11 KB = **8 MB** just for post content
- Plus BeautifulSoup objects (5-10 MB HTML per page cached)
- Plus Playwright browser memory (50-100 MB)
- **Total: ~100-150 MB peak memory**

**Verdict:** Memory usage is acceptable for 146 pages (still under 200 MB).

---

### 🔴 PROBLEM 4: Database Transaction Lockup

**Location:** `src/api/background_tasks.py:47-56`

```python
# Save posts to database
for post_data in posts:  # ← 730 iterations
    post = BlogPost(**post_data)
    db.add(post)  # ← Queued in memory

# ... (730 INSERT statements pending)

await db.commit()  # ← ALL 730 commits at once
```

**What happens:**
1. Loop creates **730 BlogPost objects** in memory
2. `db.add()` queues them (doesn't write yet)
3. Single `commit()` executes **730 INSERT statements**
4. SQLite **LOCKS the database** for entire transaction
5. Transaction takes **5-15 seconds** to complete

**Problems:**
- ❌ Database locked for 5-15 seconds
- ❌ Other jobs blocked from writing
- ❌ If commit fails, **all 730 posts lost**
- ❌ No progress updates (user sees 0 posts until end)

**SQLite specifics (from `src/database.py:24`):**
```python
poolclass=StaticPool  # Single connection only
```
- SQLite allows **only ONE writer at a time**
- All concurrent jobs will queue waiting for the lock

---

### 🟡 PROBLEM 5: Execution Time Explosion

**Time breakdown for 146 pages:**

1. **Rate limiting:** 146 pages × 3.5s avg delay = **511 seconds (8.5 min)**
2. **Page fetching:** 146 pages × 2s (Playwright) = **292 seconds (4.9 min)**
3. **Parsing:** 146 pages × 0.2s = **29 seconds**
4. **Database commit:** 730 INSERTs = **5-15 seconds**

**Total time: ~14-18 minutes**

**Current timeout:** `request_timeout = 30` seconds **per page** (OK)

**BUT:** No **job timeout** - job could run indefinitely if pages are slow.

---

### 🟡 PROBLEM 6: Visited URL Set Growth

**Location:** `src/scraper/scraper.py:49`

```python
visited_urls: Set[str] = set()  # Grows with each page
```

**Impact:**
- 146 URLs × ~100 bytes each = **14.6 KB**
- Negligible memory impact

**Verdict:** Not a problem.

---

### 🟠 PROBLEM 7: Playwright Browser Memory Leak

**Location:** `src/scraper/fetcher.py:134-161`

```python
async with HTMLFetcher() as fetcher:
    for page_num in range(max_pages):  # 146 iterations
        page = await self.browser.new_page()
        # ... fetch ...
        await page.close()  # ← Closed, but browser keeps running
```

**What happens:**
1. Playwright browser stays open for **entire job** (14-18 minutes)
2. Each page creates/closes a tab
3. Chromium **may not fully release memory** between pages
4. After 146 pages: **Memory creep** (50 MB → 150-200 MB)

**Possible outcomes:**
- ✅ Likely OK - Playwright is designed for this
- ⚠️ Possible slow memory growth
- ❌ Rare: Browser crash after ~500+ pages

**Verdict:** Probably fine for 146 pages, watch memory.

---

### 🟡 PROBLEM 8: Error Breaks Entire Job

**Location:** `src/scraper/scraper.py:86-90`

```python
except Exception as e:
    error_msg = f"Error scraping {current_url}: {str(e)}"
    logger.error("Scraping error", url=current_url, error=str(e))
    stats.errors.append(error_msg)
    break  # ← Exits loop immediately
```

**Impact:**
- If **page 73** fails, you lose all progress
- No retry for failed pages
- No checkpoint/resume capability

**Example failure scenario:**
```
Page 1-72: ✅ 360 posts scraped
Page 73: ❌ Timeout after 30s
Result: Job fails, 360 posts committed BUT...
  ... if commit happens at END, you lose ALL 360 posts!
```

**Verdict:** High risk for long-running jobs.

---

### 🟠 PROBLEM 9: No Progress Updates

**Location:** `src/api/background_tasks.py:52-53`

```python
job.pages_scraped = stats.pages_scraped  # ← Updated ONCE at end
job.posts_found = stats.posts_found
```

**Impact:**
- User sees `pages_scraped: 0` for 14-18 minutes
- No way to know if job is stuck or progressing
- Can't estimate completion time

**Better approach:** Update every 10 pages.

---

### 🔴 PROBLEM 10: SQLite Write Conflicts

**Scenario:** 3 concurrent jobs, each scraping 146 pages

**What happens:**

```
Job A: Scraping pages 1-146 (14 min)
  ↓ (minute 14) Commits 730 posts
  ↓ SQLite LOCKS database (5-10 seconds)
    ↓
    Job B: Waiting to commit 730 posts... ⏳
    Job C: Waiting to commit 730 posts... ⏳
```

**SQLite behavior:**
- Only **ONE writer** at a time
- Other jobs get `database is locked` error
- Must retry with exponential backoff
- Could add **30-60 seconds** of waiting

**From `src/database.py:24`:**
```python
poolclass=StaticPool  # No connection pooling
connect_args={"check_same_thread": False}  # Allows concurrent reads
```

**Verdict:** High contention with concurrent jobs.

---

## Time Impact Calculation

### Single Job (146 pages)

```
Rate limiting:  511s  (8.5 min)  ← 2-5s delays × 146
Page fetching:  292s  (4.9 min)  ← Playwright × 146
Parsing:         29s              ← BeautifulSoup × 146
DB commit:       10s              ← 730 INSERTs
-----------------------------------------
TOTAL:          842s  (14 min)
```

### With 3 Concurrent Jobs

```
Job A: 14 min (no contention)
Job B: 14 min + 10s wait (DB locked by Job A)
Job C: 14 min + 20s wait (DB locked by Jobs A & B)
```

---

## Resource Impact

### Memory Usage (Per Job)

```
Posts in memory:     8 MB   (730 posts)
Visited URLs:       15 KB   (146 URLs)
BeautifulSoup:      10 MB   (current page parsing)
Playwright:        150 MB   (browser + accumulated tabs)
Python overhead:    20 MB
---------------------------------
TOTAL:            ~188 MB per job
```

**With 3 concurrent jobs:** ~564 MB total

**Verdict:** ✅ Acceptable on systems with 2GB+ RAM

---

### Disk Usage

**Per 730 posts:**

```
SQLite database file growth:
  - 730 rows × 6 KB avg = 4.4 MB
  - Indexes: ~500 KB
  - Journal/WAL: ~1 MB (temporary)
  ----------------------------
  TOTAL: ~6 MB per job
```

**Verdict:** ✅ No disk issues

---

### Network Bandwidth

**Per 146 pages:**

```
HTML downloads: 146 pages × 100 KB avg = 14.6 MB
Images metadata: (not downloaded, just URLs)
-------------------------------------------
TOTAL: ~15 MB per job
```

**Verdict:** ✅ Negligible bandwidth

---

## Failure Scenarios

### Scenario 1: Page 73 Times Out

**Current behavior:**
```
Pages 1-72:  ✅ 360 posts scraped (in memory)
Page 73:     ❌ Timeout after 30s
Result:      break loop
             return posts (360 posts)
             db.commit() ← Succeeds
Final:       Job marked "completed" with 360/730 posts
```

**Verdict:** ⚠️ Partial success (loses pages 74-146)

---

### Scenario 2: Database Commit Fails

**Current behavior:**
```
Pages 1-146: ✅ 730 posts scraped (in memory)
DB commit:   ❌ "database is locked" error
Result:      Exception caught in background_tasks.py:65
             job.mark_failed(str(e))
Final:       Job marked "failed", ALL 730 posts LOST
```

**Verdict:** ❌ Critical - 14 minutes of work lost

---

### Scenario 3: Browser Crashes at Page 100

**Current behavior:**
```
Pages 1-99:  ✅ 495 posts scraped
Page 100:    ❌ Playwright error: "Browser crashed"
Result:      Exception in fetcher.py
             Caught in scraper.py:86
             break loop
             return posts (495 posts)
             db.commit() ← Succeeds
Final:       Job marked "completed" with 495/730 posts
```

**Verdict:** ⚠️ Partial success

---

### Scenario 4: Out of Memory

**Current behavior:**
```
Pages 1-120: ✅ 600 posts scraped (150 MB memory)
Page 121:    ❌ MemoryError or system OOM killer
Result:      Job process killed
Final:       Job stuck in "in_progress" forever
             No posts saved (commit never reached)
```

**Verdict:** ❌ Catastrophic failure, no recovery

---

## Comparison: 10 Pages vs 146 Pages

| Metric | 10 Pages | 146 Pages | Change |
|--------|----------|-----------|--------|
| **Posts** | 50 | 730 | 14.6× |
| **Time** | 60s | 842s (14 min) | 14× |
| **Memory** | 50 MB | 188 MB | 3.8× |
| **Risk** | Low | High | ⚠️ |
| **Failure Recovery** | Good | Poor | ❌ |
| **DB Lock Time** | 0.3s | 10s | 33× |

---

## Recommended Fixes

### Priority 1: Make It Work (Must-Have)

**FIX 1.1: Remove hardcoded max_pages limit**

`src/api/background_tasks.py:44`
```python
# Before:
posts, stats = await scrape_blog(job.blog_url, max_pages=10)

# After:
posts, stats = await scrape_blog(
    job.blog_url,
    max_pages=settings.max_pages_default
)
```

**FIX 1.2: Increase config validation limit**

`src/config.py:22`
```python
# Before:
le=100,

# After:
le=200,  # Allow up to 200 pages
```

**FIX 1.3: Add chunked database commits**

`src/api/background_tasks.py:46-56`
```python
# Before: Single commit at end
for post_data in posts:
    post = BlogPost(**post_data)
    db.add(post)
await db.commit()

# After: Commit every 50 posts
CHUNK_SIZE = 50
for i, post_data in enumerate(posts, 1):
    post = BlogPost(**post_data)
    db.add(post)

    if i % CHUNK_SIZE == 0:
        await db.commit()  # Commit chunk
        logger.info(f"Committed {i}/{len(posts)} posts")

# Final commit for remaining posts
if len(posts) % CHUNK_SIZE != 0:
    await db.commit()
```

**Benefits:**
- ✅ Database locked for 1s instead of 10s
- ✅ Progress saved incrementally
- ✅ If job fails at page 100, you still have 50-100 posts saved
- ✅ Reduces memory pressure

---

### Priority 2: Make It Reliable (Should-Have)

**FIX 2.1: Add progress updates**

`src/scraper/scraper.py:66-76`
```python
# Add callback parameter
async def scrape_blog(
    blog_url: str,
    max_pages: int = 10,
    progress_callback=None  # NEW
):
    # ... existing code ...

    stats.pages_scraped += 1

    # NEW: Call progress callback
    if progress_callback:
        await progress_callback(stats.pages_scraped, stats.posts_found)
```

`src/api/background_tasks.py`
```python
async def update_progress(pages, posts):
    job.pages_scraped = pages
    job.posts_found = posts
    await db.commit()

posts, stats = await scrape_blog(
    job.blog_url,
    max_pages=settings.max_pages_default,
    progress_callback=update_progress
)
```

**Benefits:**
- ✅ User sees live progress
- ✅ Can detect stuck jobs
- ✅ Better UX

**FIX 2.2: Add job timeout**

`src/config.py`
```python
job_timeout: int = Field(
    default=3600,  # 1 hour max per job
    description="Maximum job execution time (seconds)"
)
```

`src/api/background_tasks.py`
```python
async with asyncio.timeout(settings.job_timeout):
    posts, stats = await scrape_blog(...)
```

**Benefits:**
- ✅ Prevents zombie jobs
- ✅ Frees up semaphore slots

---

### Priority 3: Make It Production-Ready (Nice-to-Have)

**FIX 3.1: Switch to PostgreSQL**

`src/database.py`
```python
# PostgreSQL supports true concurrent writes
# No more "database is locked" errors
# Connection pooling for better concurrency
```

**FIX 3.2: Add Redis queue for background jobs**

- Use Celery or RQ for job queue
- Better retry logic
- Job prioritization
- Distributed workers

**FIX 3.3: Add checkpoint/resume**

```python
# Save checkpoint every 10 pages
checkpoint = {
    "last_url": current_url,
    "pages_scraped": stats.pages_scraped,
    "posts_count": len(posts)
}
# If job fails, resume from checkpoint
```

---

## Testing Strategy

### Test 1: Single 146-Page Job

```bash
# 1. Apply Priority 1 fixes
# 2. Set max_pages to 146
export MAX_PAGES_DEFAULT=146

# 3. Run scraping job
curl -X POST http://127.0.0.1:8001/api/jobs/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/blog/"}'

# 4. Monitor progress
watch -n 5 'curl -s http://127.0.0.1:8001/api/jobs/{JOB_ID} | jq'

# 5. Expected results:
# - Duration: 12-16 minutes
# - Posts: ~730
# - Memory: < 200 MB
# - Status: completed
```

### Test 2: Concurrent Jobs

```bash
# Start 3 jobs simultaneously
for i in {1..3}; do
  curl -X POST http://127.0.0.1:8001/api/jobs/ \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com/blog/"}' &
done

# Monitor database locks
sqlite3 blog_scraper.db "PRAGMA busy_timeout;"
```

---

## Summary

**Can it scrape 146 pages?**
- ❌ **NO** - Not without fixes
- ⚠️ **MAYBE** - With Priority 1 fixes (will be slow and risky)
- ✅ **YES** - With Priority 1 + 2 fixes (production-ready)

**Critical blockers:**
1. 🔴 Hardcoded `max_pages=10`
2. 🔴 Config validation `le=100`
3. 🔴 Single database commit (10s lock)

**Risk assessment:**
- **Low risk:** Memory usage, disk space, bandwidth
- **Medium risk:** Browser memory leaks, execution time
- **High risk:** Database commit failures, concurrent write conflicts

**Bottom line:**
Apply Priority 1 fixes → Test with 50 pages first → Then try 146 pages.
