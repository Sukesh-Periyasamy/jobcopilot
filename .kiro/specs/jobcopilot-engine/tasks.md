# Implementation Plan: JobCopilot Engine

## Overview

Split-architecture job search automation system: FastAPI REST backend (Render Free), static frontend (GitHub Pages), MongoDB Atlas Free for persistence, and Render Cron Job for daily scraping. Implementation proceeds from backend foundation through data layer, scraper, API endpoints, frontend, tests, and deployment configuration.

## Tasks

- [x] 1. Backend foundation and project structure
  - [x] 1.1 Create backend project structure and dependencies
    - Create `backend/` directory with `app/`, `app/api/`, `app/config/`, `app/database/`, `app/models/`, `app/scraper/`, `app/services/`, `app/utils/` subdirectories
    - Add `__init__.py` files to all packages
    - Create `backend/requirements.txt` with: fastapi, uvicorn, pymongo, python-dotenv, pydantic, httpx, hypothesis, pytest, pytest-asyncio
    - Create `backend/.env.example` with all required environment variable templates (MONGODB_URI, DATABASE_NAME, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SEARCH_TERMS, LOCATIONS, JOB_SOURCES, SCHEDULE_TIME)
    - _Requirements: 9.1, 9.3_

  - [x] 1.2 Implement configuration loader (`backend/app/config/settings.py`)
    - Create `Settings` dataclass with all fields: mongodb_uri, database_name, telegram_bot_token, telegram_chat_id, search_terms, locations, job_sources, schedule_time
    - Implement `Settings.load()` classmethod that loads from `.env` via python-dotenv, falls back to environment variables
    - Parse comma-separated strings into lists for search_terms, locations, job_sources
    - Apply defaults: database_name="jobcopilot", schedule_time="08:00", search_terms/locations/job_sources per requirements 9.4
    - Raise descriptive error if MONGODB_URI is missing
    - Validate schedule_time matches HH:MM format (00:00–23:59), raise error if invalid
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [x] 1.3 Implement logger module (`backend/app/utils/logger.py`)
    - Configure root logger with RotatingFileHandler: `data/jobcopilot.log`, 10MB max, 5 backups
    - Add StreamHandler for console output
    - Format: ISO 8601 timestamp | LEVEL | module | message
    - Export `setup_logging()` function returning configured logger
    - _Requirements: 8.5, 8.6, 8.7_

  - [x] 1.4 Implement retry utility (`backend/app/utils/retry.py`)
    - Create `retry_with_backoff(fn, max_retries, initial_backoff)` function
    - Implement exponential backoff: delays of B, 2B, 4B, ..., 2^(attempt-1)×B seconds
    - Log warning on each retry attempt with attempt number and error
    - Raise final exception after all retries exhausted
    - _Requirements: 6.4, 7.2, 7.3_

- [x] 2. Data layer — models and database
  - [x] 2.1 Create data models (`backend/app/models/job.py`)
    - Define `JobRecord` dataclass with fields: title, company, location, source, job_url, description, job_type, salary, date_posted, search_term, created_at, updated_at
    - Define `ScrapeResult` dataclass with fields: jobs (list[JobRecord]), errors (list[str])
    - Define `BulkInsertResult` dataclass with fields: inserted_count, duplicates_skipped, new_jobs (list[JobRecord])
    - Define `ScrapeHistoryEntry` dataclass with fields: timestamp, jobs_found, duplicates_skipped, errors
    - Define `FilterCriteria` dataclass with optional fields: source, location, company, keyword, job_type, date_from, date_to, search_term
    - Define `PaginatedResult` dataclass with fields: jobs, total, page, page_size, total_pages
    - _Requirements: 1.5, 1.6, 2.7, 3.1–3.8_

  - [x] 2.2 Create Pydantic schemas (`backend/app/models/schemas.py`)
    - Define `JobResponse`, `PaginatedJobsResponse`, `StatsResponse`, `SaveJobRequest`, `ApplyJobRequest`, `WatchlistRequest` Pydantic models
    - Add field validation (company_name max 100 chars in WatchlistRequest)
    - _Requirements: 4.10, 4.12, 10.3_

  - [x] 2.3 Implement MongoDB connection singleton (`backend/app/database/connection.py`)
    - Create `get_database()` function that returns a MongoDB database client
    - Use pymongo MongoClient with connection pooling
    - Implement singleton pattern to reuse connection across requests
    - Use retry_with_backoff for initial connection (3 retries, 1s initial backoff)
    - _Requirements: 7.2, 10.1_

  - [x] 2.4 Implement repository module (`backend/app/database/repository.py`)
    - Create `JobsRepository` class with `__init__(settings)` that connects to MongoDB and ensures indexes exist
    - Implement `ensure_indexes()`: unique on job_url, ascending on date_posted, source, company
    - Implement `bulk_insert(records)`: ordered=False, skip duplicates, return BulkInsertResult
    - Implement `record_scrape_history(entry)`: write to scrape_history collection
    - Implement `get_jobs(filters, page, page_size)`: query with FilterCriteria, return PaginatedResult
    - Implement `get_recent_jobs(limit=10)`: order by date_posted desc
    - Implement `search_jobs(query, page, page_size)`: text search on title and description
    - Implement `get_jobs_by_company(company)`: return all jobs from company
    - Implement `save_job(job_data)` / `remove_saved_job(job_url)`: saved_jobs CRUD
    - Implement `add_applied_job(job_data, status)` / `update_application_status(job_url, status)`: applied_jobs CRUD
    - Implement `get_watchlist()` / `add_to_watchlist(company)` / `remove_from_watchlist(company)`: watchlist CRUD with max 50 entries, max 100 chars validation
    - Implement `get_stats()`: return total_jobs, jobs_today, jobs_this_week, saved_jobs, applied_jobs, companies_tracked
    - Seed default watchlist: Siemens Healthineers, GE HealthCare, Philips, Medtronic, Abbott, Dozee
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10, 10.1, 10.4_

  - [x] 2.5 Implement filter engine (`backend/app/services/filter_engine.py`)
    - Create `build_query(criteria: FilterCriteria) -> dict` function
    - Case-insensitive regex for substring matches: location, company, keyword
    - Case-insensitive exact match for enumerated values: source, job_type, search_term
    - Use `$or` on title and description for keyword filter
    - Use `$gte`/`$lte` for date_from/date_to range
    - Ignore None/empty fields, combine present criteria with AND logic
    - Return empty dict if no criteria specified
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10_

- [x] 3. Checkpoint — Verify data layer
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Scraper and notification services
  - [x] 4.1 Implement scraper service (`backend/app/scraper/scraper.py`)
    - Create `scrape_all(settings: Settings) -> ScrapeResult` function
    - Iterate over all search_term × location combinations across configured sources
    - Use ThreadPoolExecutor with max_workers=4 for concurrent scraping
    - Call JobSpy for each combination, requesting up to 15 results per source
    - Normalize each result row into a JobRecord (set missing optional fields to empty string)
    - Skip records missing title or job_url, log invalid records
    - Collect errors per failed source-term-location combination
    - Return ScrapeResult with all collected jobs and errors
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 7.1, 7.4, 7.5, 8.1, 10.2_

  - [x] 4.2 Implement Telegram notifier (`backend/app/services/notifier.py`)
    - Create `TelegramNotifier` class with `__init__(bot_token, chat_id)`
    - If token/chat_id missing, all sends become no-ops with warning log
    - Implement `notify_new_jobs(jobs)`: format summary message, split at 4096 chars, send via Bot API
    - Implement `notify_watchlist_match(job)`: send separate alert for watchlist company match
    - Implement `mark_notified(job_urls)`: track notified jobs in notifications collection
    - Use retry_with_backoff for API calls (3 retries, 1s initial backoff)
    - Format each job entry with: title, company, location, job_url
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 7.3, 8.3_

  - [x] 4.3 Implement daily scraper entry point (`backend/daily_scraper.py`)
    - Load settings, run scrape_all(), bulk insert to MongoDB
    - Record scrape history
    - Send Telegram notifications for new un-notified jobs
    - Send watchlist alerts for matching companies (case-insensitive)
    - Implement retry logic for full workflow (3 retries, 60s initial backoff)
    - Log start time, end time, and outcome
    - _Requirements: 6.1, 6.3, 6.4, 6.5, 8.4_

- [x] 5. FastAPI REST API endpoints
  - [x] 5.1 Create FastAPI application entry point (`backend/main.py`)
    - Initialize FastAPI app with title="JobCopilot API", version="1.0.0"
    - Add CORS middleware allowing origin `https://sukeshperiyasamy.github.io`
    - Register all API routers (health, jobs, watchlist, saved, applied, stats)
    - Implement CLI: `python main.py serve` → uvicorn, `python main.py scrape` → single cycle exit 0/1, no args → help exit 0, invalid → error + help exit 2
    - _Requirements: 11.1, 11.4, 11.5_

  - [x] 5.2 Implement health endpoint (`backend/app/api/health.py`)
    - GET `/health` → returns `{"status": "ok"}`
    - _Requirements: 4.13_

  - [x] 5.3 Implement jobs endpoints (`backend/app/api/jobs.py`)
    - GET `/jobs` with query params: page, page_size, source, location, company, keyword, job_type, date_from, date_to, search_term
    - GET `/jobs/recent` → top 10 most recently posted jobs
    - GET `/jobs/search?q=` → full-text search across title and description
    - GET `/jobs/company/{name}` → jobs from specific company
    - Use FilterCriteria and repository for all queries
    - Return PaginatedJobsResponse with pagination metadata
    - _Requirements: 3.1–3.10, 4.2, 4.3, 4.12, 10.3_

  - [x] 5.4 Implement watchlist endpoints (`backend/app/api/watchlist.py`)
    - GET `/watchlist` → list all watchlist companies
    - POST `/watchlist` → add company (validate max 50 entries, max 100 chars)
    - DELETE `/watchlist/{company}` → remove company
    - _Requirements: 4.10_

  - [x] 5.5 Implement saved jobs endpoints (`backend/app/api/saved.py`)
    - POST `/save-job` → save job to saved_jobs collection
    - DELETE `/save-job/{job_url}` → remove from saved jobs
    - GET `/saved-jobs` → list all saved jobs
    - _Requirements: 4.5, 4.6, 4.7_

  - [x] 5.6 Implement applied jobs endpoints (`backend/app/api/applied.py`)
    - POST `/apply-job` → mark job as applied with status (default "Interested")
    - PATCH `/apply-job/{job_url}` → update application status
    - GET `/applied-jobs` → list all applied jobs
    - _Requirements: 4.8, 4.9_

  - [x] 5.7 Implement stats endpoint (`backend/app/api/stats.py`)
    - GET `/stats` → return StatsResponse with total_jobs, jobs_today, jobs_this_week, saved_jobs, applied_jobs, companies_tracked
    - _Requirements: 4.1_

- [x] 6. Checkpoint — Verify backend API
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Frontend — Static site (GitHub Pages)
  - [x] 7.1 Create frontend structure and shared assets
    - Create `frontend/` directory with `css/`, `js/`, `assets/` subdirectories
    - Create `frontend/css/style.css` with dark mode glassmorphism design system: CSS variables for theming, frosted glass cards, subtle borders, backdrop blur, responsive mobile-first layout, loading skeletons, empty states
    - Create `frontend/js/components.js` with reusable UI components: job cards, data tables, skeleton loaders, status badges, fresh job badges (🟢 Posted Today, 🟡 Posted This Week, ⚪ Older), pagination controls, toast notifications
    - _Requirements: 4.1, 4.12_

  - [x] 7.2 Create API abstraction layer (`frontend/js/api.js`)
    - Define `API_BASE` constant pointing to Render backend URL
    - Implement all API functions: getJobs, getRecentJobs, searchJobs, getStats, getWatchlist, addToWatchlist, removeFromWatchlist, saveJob, removeSavedJob, applyJob, updateApplicationStatus, getSavedJobs, getAppliedJobs, getHealth
    - Handle errors gracefully, return structured responses
    - _Requirements: 4.13_

  - [x] 7.3 Create Dashboard page (`frontend/index.html` + `frontend/js/dashboard.js`)
    - Build HTML page with navigation, metric cards (Total Jobs, Today's Jobs, This Week, Saved, Applied)
    - Implement dashboard.js: fetch stats from API, render metric cards, fetch and display recent jobs table (top 10)
    - Add loading skeletons while data loads
    - _Requirements: 4.1, 4.2_

  - [x] 7.4 Create Jobs Feed page (`frontend/jobs.html` + `frontend/js/jobs.js`)
    - Build HTML page with filter controls (source, location, company, keyword, job type, date range) and paginated jobs table
    - Implement jobs.js: fetch paginated jobs with filters, render table with columns (Title, Company, Location, Source, Date Posted, Apply, Save), pagination controls
    - Add fresh job badges based on date_posted
    - Implement Apply button (opens job_url in new tab) and Save button
    - _Requirements: 4.3, 4.4, 4.5, 4.12_

  - [x] 7.5 Create Saved Jobs page (`frontend/saved.html` + `frontend/js/saved.js`)
    - Build HTML page listing saved jobs with Remove button
    - Implement saved.js: fetch saved jobs, render table (Title, Company, Location, Date Saved, Remove), handle remove action
    - _Requirements: 4.7_

  - [x] 7.6 Create Watchlist page (`frontend/watchlist.html` + `frontend/js/watchlist.js`)
    - Build HTML page with add company form and watchlist table
    - Implement watchlist.js: fetch watchlist, render company list, add/remove companies
    - Show default companies: Siemens Healthineers, GE HealthCare, Philips, Medtronic, Abbott, Dozee
    - Validate max 50 entries, max 100 chars per name on client side
    - _Requirements: 4.10_

  - [x] 7.7 Create Settings page (`frontend/settings.html`)
    - Build HTML page for configuring search terms, locations, sources
    - Display current configuration (read-only for now, backend manages settings via env vars)
    - _Requirements: 4.11_

- [x] 8. Checkpoint — Verify frontend renders correctly
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Property-based tests and integration tests
  - [ ]* 9.1 Write property test for scraper combination coverage
    - **Property 1: Scraper combination coverage**
    - Use Hypothesis to generate arbitrary lists of search terms and locations
    - Assert scraper invokes JobSpy exactly `len(search_terms) × len(locations)` times
    - **Validates: Requirements 1.1**

  - [ ]* 9.2 Write property test for normalization correctness
    - **Property 2: Normalization correctness**
    - Use Hypothesis to generate valid JobSpy result rows with various missing fields
    - Assert all required fields present as strings, missing optional fields default to empty string, records missing title/job_url excluded
    - **Validates: Requirements 1.5, 1.6, 7.5**

  - [ ]* 9.3 Write property test for source failure resilience
    - **Property 3: Source failure resilience**
    - Use Hypothesis to generate sets of sources with random subset failing
    - Assert results from non-failing sources preserved, error list has one entry per failure
    - **Validates: Requirements 1.7, 7.1**

  - [ ]* 9.4 Write property test for deduplication counting
    - **Property 4: Deduplication counting**
    - Use Hypothesis to generate lists of JobRecords with duplicate job_urls
    - Assert duplicates_skipped equals total minus unique inserted
    - **Validates: Requirements 2.3**

  - [ ]* 9.5 Write property test for scrape history accuracy
    - **Property 5: Scrape history accuracy**
    - Use Hypothesis to generate scrape results with varying jobs, duplicates, errors
    - Assert recorded history matches actual counts
    - **Validates: Requirements 2.7**

  - [ ]* 9.6 Write property test for filter query building — single criterion
    - **Property 6: Filter query building — single criterion**
    - Use Hypothesis to generate individual filter criteria
    - Assert correct MongoDB query structure: regex for substrings, exact match for enums, $or for keyword, $gte/$lte for dates
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

  - [ ]* 9.7 Write property test for filter composition with AND logic
    - **Property 7: Filter composition with AND logic**
    - Use Hypothesis to generate FilterCriteria with random subset of fields set
    - Assert query has exactly K conditions for K non-null fields, None/empty fields absent
    - **Validates: Requirements 3.8, 3.10**

  - [ ]* 9.8 Write property test for watchlist validation
    - **Property 8: Watchlist validation**
    - Use Hypothesis to generate company names of various lengths and watchlist sizes
    - Assert acceptance iff 1 ≤ len(name) ≤ 100 AND watchlist size < 50
    - **Validates: Requirements 4.10**

  - [ ]* 9.9 Write property test for pagination calculation
    - **Property 9: Pagination calculation**
    - Use Hypothesis to generate total counts N and page sizes P
    - Assert total_pages == ceil(N/P), each page (except last) has exactly P records
    - **Validates: Requirements 4.12, 10.3**

  - [ ]* 9.10 Write property test for message formatting with size limit
    - **Property 10: Message formatting with size limit**
    - Use Hypothesis to generate lists of JobRecords with varying title/company/url lengths
    - Assert each message ≤ 4096 chars, every job appears in exactly one message, no job split across messages
    - **Validates: Requirements 5.2**

  - [ ]* 9.11 Write property test for notification filtering
    - **Property 11: Notification filtering**
    - Use Hypothesis to generate jobs with notified/un-notified status and watchlist
    - Assert only un-notified jobs in summary, separate alert for watchlist matches
    - **Validates: Requirements 5.3, 5.4**

  - [ ]* 9.12 Write property test for schedule time validation
    - **Property 12: Schedule time validation**
    - Use Hypothesis to generate arbitrary strings
    - Assert acceptance iff matches HH:MM with HH in [00,23] and MM in [00,59]
    - **Validates: Requirements 6.2, 9.6**

  - [ ]* 9.13 Write property test for retry with exponential backoff
    - **Property 13: Retry with exponential backoff**
    - Use Hypothesis to generate max_retries R and initial_backoff B
    - Assert exactly min(F, R) retries with correct delay sequence
    - **Validates: Requirements 6.4, 7.2, 7.3**

  - [ ]* 9.14 Write property test for settings loading with defaults
    - **Property 14: Settings loading with defaults**
    - Use Hypothesis to generate subsets of config keys
    - Assert provided values used, absent keys get defaults, missing MONGODB_URI raises error
    - **Validates: Requirements 9.1, 9.3**

  - [ ]* 9.15 Write property test for CLI argument handling
    - **Property 15: CLI argument handling**
    - Use Hypothesis to generate strings not in {"serve", "scrape"}
    - Assert exit code 2 and error message contains invalid argument
    - **Validates: Requirements 11.5**

  - [ ]* 9.16 Write API integration tests (`backend/tests/test_api.py`)
    - Use FastAPI TestClient to test all endpoints
    - Test GET /health returns 200 with status ok
    - Test GET /jobs with various filter combinations
    - Test GET /jobs/recent returns max 10 jobs
    - Test POST/DELETE /watchlist CRUD operations
    - Test POST/DELETE /save-job operations
    - Test POST/PATCH /apply-job operations
    - Test GET /stats returns correct structure
    - Test 422 responses for invalid request bodies
    - _Requirements: 4.1–4.12_

- [x] 10. Deployment configuration and final wiring
  - [x] 10.1 Create Render deployment configuration
    - Create `backend/render.yaml` or document Render setup: web service for FastAPI, cron job for daily_scraper.py at 08:00 AM IST
    - Ensure `backend/main.py` starts with `uvicorn` for Render's web service
    - Document environment variables to set in Render dashboard
    - _Requirements: 6.1_

  - [x] 10.2 Create GitHub Pages deployment setup
    - Ensure `frontend/` is ready for GitHub Pages deployment (static files, no build step)
    - Update API_BASE in `frontend/js/api.js` to point to Render backend URL
    - Add `.gitignore` entries for `.env`, `data/`, `__pycache__/`
    - _Requirements: 4.1_

  - [x] 10.3 Create project README with setup instructions
    - Document local development setup (backend + frontend)
    - Document deployment steps for Render and GitHub Pages
    - Document environment variables and their defaults
    - Include architecture diagram reference
    - _Requirements: 9.1, 9.3_

- [x] 11. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document using Hypothesis
- Unit tests validate specific examples and edge cases
- Backend uses Python (FastAPI + pymongo), frontend uses vanilla JavaScript
- No Streamlit, no APScheduler — replaced by Render Cron Job and static frontend
- Default watchlist companies: Siemens Healthineers, GE HealthCare, Philips, Medtronic, Abbott, Dozee

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "1.4"] },
    { "id": 2, "tasks": ["2.1", "2.2"] },
    { "id": 3, "tasks": ["2.3"] },
    { "id": 4, "tasks": ["2.4", "2.5"] },
    { "id": 5, "tasks": ["4.1", "4.2"] },
    { "id": 6, "tasks": ["4.3"] },
    { "id": 7, "tasks": ["5.1"] },
    { "id": 8, "tasks": ["5.2", "5.3", "5.4", "5.5", "5.6", "5.7"] },
    { "id": 9, "tasks": ["7.1", "7.2"] },
    { "id": 10, "tasks": ["7.3", "7.4", "7.5", "7.6", "7.7"] },
    { "id": 11, "tasks": ["9.1", "9.2", "9.3", "9.4", "9.5", "9.6", "9.7", "9.8", "9.9", "9.10", "9.11", "9.12", "9.13", "9.14", "9.15", "9.16"] },
    { "id": 12, "tasks": ["10.1", "10.2", "10.3"] }
  ]
}
```
