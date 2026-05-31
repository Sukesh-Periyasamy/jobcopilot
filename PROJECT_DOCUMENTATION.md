# JobCopilot — Complete Project Documentation

> **Personal Job Search Automation System**
> Built for Sukesh Periyasamy | M.Tech Medical Technology, IIT Jodhpur
> Version: v1.4 (Career Radar + Smart Search)
> Last Updated: 2025

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture](#2-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Complete Folder Structure](#4-complete-folder-structure)
5. [API Documentation](#5-api-documentation)
6. [Career Radar Scoring Engine](#6-career-radar-scoring-engine)
7. [Database Schema](#7-database-schema)
8. [Smart Search Engine](#8-smart-search-engine)
9. [Regional Radar (South India Fresher)](#9-regional-radar-south-india-fresher)
10. [Environment Variables](#10-environment-variables)
11. [Installation & Local Development Guide](#11-installation--local-development-guide)
12. [Deployment Guide](#12-deployment-guide)
13. [Testing](#13-testing)
14. [Current Status & Future Roadmap](#14-current-status--future-roadmap)

---

## 1. Executive Summary

### Overview

JobCopilot is a fully automated, zero-cost personal job search system designed specifically for an IIT Jodhpur M.Tech Medical Technology student seeking India-based MedTech, Biomedical, Research, and Healthcare AI roles. The system operates autonomously — scraping jobs daily from 9+ sources, scoring them against a personalized career profile, and delivering actionable recommendations via a web dashboard and Telegram notifications.

### Key Capabilities

| Capability | Description |
|---|---|
| **Multi-Source Scraping** | 557+ jobs scraped daily from LinkedIn, Indeed, Naukri, Google, Greenhouse, Lever, Ashby, Workday, SuccessFactors |
| **Career Radar** | Personalized scoring engine tuned for Biomedical/MedTech/Research roles with 345 career matches |
| **Smart Search** | Multi-keyword weighted search with synonym expansion and faceted filters |
| **Regional Radar** | South India fresher-focused job feed with district-level granularity |
| **Research Radar** | Dedicated feed for JRF/SRF/Project Associate positions from Indian institutions |
| **Watchlist Alerts** | Real-time notifications when tracked companies post new jobs |
| **Daily Targets** | Top 20 application targets computed daily (India + Fresh + High Score) |
| **Analytics Dashboard** | 7 interactive charts showing hiring trends, source distribution, and more |
| **Export** | CSV and XLSX export of filtered job data |
| **Telegram Bot** | Daily intelligence summary + Career Radar top 10 + Watchlist alerts |

### Target Profile

- **Name:** Sukesh Periyasamy
- **Education:** M.Tech Medical Technology, IIT Jodhpur
- **Research Focus:** SERS-based biosensors, diagnostics, point-of-care devices
- **Target Roles:** Biomedical Engineer, Medical Device Engineer, Research Associate, Healthcare AI, Clinical Research, R&D Engineer
- **Target Locations:** India (Bangalore, Chennai, Coimbatore, Hyderabad, Pune, Mumbai, Delhi, Remote)
- **Career Stage:** Early career / Fresher (0-2 years experience)

### Deployment & Cost

| Component | Service | Cost |
|---|---|---|
| Frontend | GitHub Pages (docs/ folder) | ₹0/month |
| Backend API | Render Web Service (Free tier) | ₹0/month |
| Database | MongoDB Atlas (Free tier, 512MB) | ₹0/month |
| Scraper Scheduler | GitHub Actions (2000 min/month free) | ₹0/month |
| Notifications | Telegram Bot API | ₹0/month |
| **Total** | | **₹0/month** |

### Live URLs

- **Frontend:** `https://sukesh-periyasamy.github.io/jobcopilot/`
- **Backend API:** `https://jobcopilot-uydv.onrender.com`
- **Health Check:** `https://jobcopilot-uydv.onrender.com/health`

---

## 2. Architecture

### 2.1 System Architecture

```mermaid
graph TB
    subgraph "Frontend (GitHub Pages)"
        FE[Static HTML/CSS/JS]
        FE_PAGES[13 HTML Pages]
        FE_CHARTS[Chart.js Analytics]
    end

    subgraph "Backend (Render)"
        API[FastAPI Server]
        ROUTERS[16 API Routers]
        SERVICES[13 Service Modules]
        SCRAPERS[4 Scrapers]
    end

    subgraph "Database (MongoDB Atlas)"
        DB[(MongoDB Atlas Free)]
        JOBS[jobs collection]
        SAVED[saved_jobs]
        APPLIED[applied_jobs]
        WATCHLIST[company_watchlist]
        HISTORY[scrape_history]
        PREFS[preferences]
        NOTIF[notifications]
    end

    subgraph "Automation (GitHub Actions)"
        CRON_SCRAPE[Daily Scraper 08:00 IST]
        CRON_EMAIL[Daily Email 08:05 IST]
    end

    subgraph "Notifications"
        TELEGRAM[Telegram Bot API]
        EMAIL[SMTP Email]
    end

    subgraph "Data Sources"
        LINKEDIN[LinkedIn]
        INDEED[Indeed]
        NAUKRI[Naukri]
        GOOGLE[Google Jobs]
        GREENHOUSE[Greenhouse ATS]
        LEVER[Lever ATS]
        ASHBY[Ashby ATS]
        WORKDAY[Workday ATS]
        SAP[SuccessFactors ATS]
        RESEARCH[Research Institutions]
    end

    FE -->|REST API calls| API
    API --> ROUTERS
    ROUTERS --> SERVICES
    SERVICES --> DB
    SCRAPERS --> DB

    CRON_SCRAPE -->|Triggers| SCRAPERS
    SCRAPERS -->|JobSpy| LINKEDIN
    SCRAPERS -->|JobSpy| INDEED
    SCRAPERS -->|JobSpy| NAUKRI
    SCRAPERS -->|JobSpy| GOOGLE
    SCRAPERS -->|JobHive| GREENHOUSE
    SCRAPERS -->|JobHive| LEVER
    SCRAPERS -->|JobHive| ASHBY
    SCRAPERS -->|JobHive| WORKDAY
    SCRAPERS -->|JobHive| SAP
    SCRAPERS -->|Custom| RESEARCH

    SERVICES -->|Alerts| TELEGRAM
    CRON_EMAIL -->|Summary| EMAIL
```

### 2.2 Data Flow Architecture

```mermaid
flowchart LR
    subgraph "1. SCRAPE"
        S1[JobSpy Scraper]
        S2[JobHive Scraper]
        S3[Research Scraper]
        S4[LinkedIn Scraper]
    end

    subgraph "2. STORE"
        DEDUP[Deduplication via unique index]
        BULK[Bulk Insert ordered=False]
        HIST[Record Scrape History]
    end

    subgraph "3. SCORE"
        RADAR[Career Radar Engine]
        SEARCH[Smart Search Engine]
        REGIONAL[Regional Radar]
        COLLECTIONS[Collection Engine]
    end

    subgraph "4. DISPLAY"
        DASH[Dashboard]
        CAREER[Career Radar Page]
        JOBS_PAGE[Jobs Page]
        ANALYTICS[Analytics Charts]
    end

    subgraph "5. NOTIFY"
        TG[Telegram Summary]
        WL[Watchlist Alerts]
        INTEL[Intelligence Report]
    end

    S1 --> DEDUP
    S2 --> DEDUP
    S3 --> DEDUP
    S4 --> DEDUP
    DEDUP --> BULK
    BULK --> HIST

    BULK --> RADAR
    BULK --> SEARCH
    BULK --> REGIONAL
    BULK --> COLLECTIONS

    RADAR --> CAREER
    SEARCH --> JOBS_PAGE
    REGIONAL --> DASH
    COLLECTIONS --> ANALYTICS

    BULK --> TG
    BULK --> WL
    BULK --> INTEL
```

### 2.3 Deployment Architecture

```mermaid
graph TB
    subgraph "GitHub Repository"
        REPO[sukesh-periyasamy/jobcopilot]
        DOCS[docs/ folder]
        BACKEND[backend/ folder]
        WORKFLOWS[.github/workflows/]
    end

    subgraph "GitHub Pages"
        GP[Static Site Hosting]
        GP_URL["sukesh-periyasamy.github.io/jobcopilot"]
    end

    subgraph "Render Cloud"
        RENDER_WEB[Web Service - FastAPI]
        RENDER_CRON[Cron Job - Daily Scraper]
        RENDER_URL["jobcopilot-uydv.onrender.com"]
    end

    subgraph "MongoDB Atlas"
        ATLAS[Free Tier Cluster]
        ATLAS_DB[jobcopilot database]
        ATLAS_SIZE["512MB Storage"]
    end

    subgraph "GitHub Actions"
        GA_SCRAPE[daily-scraper.yml]
        GA_EMAIL[daily-email.yml]
        GA_PYPI[publish-to-pypi.yml]
    end

    subgraph "External APIs"
        TG_API[Telegram Bot API]
        SMTP_API[SMTP Server]
    end

    DOCS -->|Auto-deploy| GP
    BACKEND -->|Deploy| RENDER_WEB
    BACKEND -->|Deploy| RENDER_CRON
    WORKFLOWS -->|Schedule| GA_SCRAPE
    WORKFLOWS -->|Schedule| GA_EMAIL

    RENDER_WEB -->|Read/Write| ATLAS
    RENDER_CRON -->|Write| ATLAS
    GA_SCRAPE -->|Write| ATLAS

    RENDER_CRON -->|Notify| TG_API
    GA_EMAIL -->|Send| SMTP_API

    GP -->|API Calls| RENDER_WEB
```

### 2.4 Request Flow

```mermaid
sequenceDiagram
    participant User as User Browser
    participant FE as GitHub Pages
    participant API as FastAPI (Render)
    participant DB as MongoDB Atlas

    User->>FE: Open career-radar.html
    FE->>API: GET /career-radar/top
    API->>DB: Find all jobs
    DB-->>API: 557+ job documents
    API->>API: Score each job (Career Radar Engine)
    API->>DB: Get watchlist companies
    DB-->>API: 13 companies
    API->>DB: Get applied/saved URLs
    DB-->>API: Exclusion set
    API->>API: Filter (score>=25, days<=14, not applied)
    API-->>FE: JSON {high_priority: [...], stats: {...}}
    FE->>FE: Render job cards with scores
    FE-->>User: Display Career Radar page
```

### 2.5 Daily Scrape Workflow

```mermaid
sequenceDiagram
    participant GA as GitHub Actions
    participant PY as Python 3.11
    participant JOBSPY as JobSpy Library
    participant JOBHIVE as JobHive Library
    participant RESEARCH as Research Scraper
    participant DB as MongoDB Atlas
    participant TG as Telegram Bot

    GA->>PY: Trigger at 08:00 IST (cron: 30 2 * * *)
    PY->>JOBSPY: scrape_all(settings)
    JOBSPY->>JOBSPY: LinkedIn + Indeed + Naukri + Google
    JOBSPY-->>PY: ScrapeResult (jobs=[], errors=[])
    PY->>JOBHIVE: scrape_jobhive(settings)
    JOBHIVE->>JOBHIVE: Greenhouse + Lever + Ashby + Workday + SAP
    JOBHIVE-->>PY: ScrapeResult (jobs=[], errors=[])
    PY->>RESEARCH: scrape_research_institutions()
    RESEARCH-->>PY: ScrapeResult (jobs=[], errors=[])
    PY->>PY: Merge all results
    PY->>DB: bulk_insert(merged_jobs) [ordered=False]
    DB-->>PY: BulkInsertResult (inserted, duplicates)
    PY->>DB: record_scrape_history(entry)
    PY->>TG: notify_new_jobs(new_jobs)
    PY->>TG: notify_watchlist_match(matching_jobs)
    PY->>TG: send_intelligence_summary(jobs, watchlist)
    PY->>TG: Career Radar Top 10 summary
```

---

## 3. Technology Stack

### 3.1 Backend

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.11.11 | Core runtime (pinned in runtime.txt) |
| FastAPI | Latest | REST API framework |
| Uvicorn | Latest | ASGI server |
| PyMongo | Latest | MongoDB driver |
| Pydantic | Latest | Request/response validation |
| python-dotenv | Latest | Environment variable loading |
| httpx | Latest | Async HTTP client |
| requests | Latest | HTTP client for scrapers |
| jobhive-py | Latest | ATS platform scraper (Greenhouse, Lever, Ashby, Workday, SAP) |
| python-jobspy | Latest | Job board scraper (LinkedIn, Indeed, Naukri, Google) |
| openpyxl | Latest | Excel export (.xlsx) |
| pyarrow | >=18.0.0 | Parquet/Arrow support for pandas |
| pandas | Latest | Data manipulation for exports |

### 3.2 Frontend

| Technology | Version | Purpose |
|---|---|---|
| HTML5 | - | Page structure |
| CSS3 | - | Light theme styling |
| Vanilla JavaScript | ES6+ | DOM manipulation, API calls |
| Chart.js | CDN | Analytics charts (7 chart types) |
| Fetch API | Native | REST API communication |

### 3.3 Database

| Technology | Tier | Purpose |
|---|---|---|
| MongoDB Atlas | Free (M0) | Document database |
| Storage | 512MB | Job records + metadata |
| Connections | 500 max | Connection pooling |
| Regions | AWS Mumbai | Low latency for India |

### 3.4 Infrastructure

| Service | Purpose | Cost |
|---|---|---|
| GitHub Pages | Static frontend hosting | Free |
| Render | Backend API + Cron jobs | Free tier |
| MongoDB Atlas | Database | Free tier (512MB) |
| GitHub Actions | CI/CD + Scheduled scraping | 2000 min/month free |
| Telegram Bot API | Push notifications | Free |

### 3.5 Testing

| Technology | Purpose |
|---|---|
| pytest | Test runner |
| pytest-asyncio | Async test support |
| Hypothesis | Property-based testing |
| unittest.mock | Mocking MongoDB and external APIs |

### 3.6 Development Tools

| Tool | Purpose |
|---|---|
| pre-commit | Git hooks for code quality |
| VS Code | Primary IDE |
| Git | Version control |
| pip | Package management |

---

## 4. Complete Folder Structure

```
jobcopilot/
├── .github/
│   ├── CODEOWNERS
│   └── workflows/
│       ├── daily-scraper.yml          # Cron: 08:00 IST daily scrape
│       ├── daily-email.yml            # Cron: 08:05 IST email summary
│       └── publish-to-pypi.yml        # PyPI package publishing
│
├── backend/
│   ├── .env                           # Local environment variables (gitignored)
│   ├── .env.example                   # Template for environment setup
│   ├── main.py                        # FastAPI app + CLI entry point
│   ├── daily_scraper.py               # Cron job entry point (scrape-store-notify)
│   ├── requirements.txt               # Python dependencies
│   ├── runtime.txt                    # Python version pin (3.11.11)
│   ├── Procfile                       # Render deployment command
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   │
│   │   ├── api/                       # 16 FastAPI Router modules
│   │   │   ├── analytics.py           # GET /analytics
│   │   │   ├── applied.py            # POST/PATCH/GET /apply-job, /applied-jobs
│   │   │   ├── career_radar.py       # 8 Career Radar endpoints
│   │   │   ├── collections.py        # GET /collections, /collections/{name}
│   │   │   ├── export.py             # GET /export/csv, /export/xlsx
│   │   │   ├── health.py             # GET /health
│   │   │   ├── internships.py        # GET /internships
│   │   │   ├── jobs.py               # GET /jobs, /jobs/recent, /jobs/search, /jobs/smart-search
│   │   │   ├── linkedin.py           # 8 LinkedIn endpoints + /scraper/status
│   │   │   ├── opportunities.py      # GET /opportunities
│   │   │   ├── preferences.py        # POST/GET/DELETE /preferences/*
│   │   │   ├── regional.py           # 14 Regional/Fresher endpoints
│   │   │   ├── research.py           # GET /research, /research/recent
│   │   │   ├── saved.py              # POST/DELETE/GET /save-job, /saved-jobs
│   │   │   ├── stats.py              # GET /stats
│   │   │   └── watchlist.py          # GET/POST/PATCH/DELETE /watchlist
│   │   │
│   │   ├── config/
│   │   │   ├── settings.py           # Settings loader (env vars + defaults)
│   │   │   └── linkedin_queries.json  # LinkedIn search query templates
│   │   │
│   │   ├── database/
│   │   │   ├── connection.py          # MongoDB singleton with retry
│   │   │   └── repository.py         # All CRUD operations (JobsRepository)
│   │   │
│   │   ├── models/
│   │   │   ├── job.py                # Dataclasses (JobRecord, ScrapeResult, etc.)
│   │   │   └── schemas.py            # Pydantic request/response models
│   │   │
│   │   ├── scraper/
│   │   │   ├── scraper.py            # JobSpy scraper (LinkedIn, Indeed, Naukri, Google)
│   │   │   ├── jobhive_scraper.py    # JobHive ATS scraper (5 platforms)
│   │   │   ├── research_scraper.py   # Research institution scraper
│   │   │   └── linkedin_scraper.py   # LinkedIn-specific scraper (deprecated)
│   │   │
│   │   ├── services/
│   │   │   ├── career_radar.py       # Career Radar scoring engine
│   │   │   ├── smart_search.py       # Smart Search with synonyms + weights
│   │   │   ├── regional_radar.py     # South India fresher radar
│   │   │   ├── collection_engine.py  # Collection classification
│   │   │   ├── constants.py          # Collections, keywords, institutions
│   │   │   ├── filter_engine.py      # MongoDB query builder
│   │   │   ├── export_service.py     # CSV/XLSX export
│   │   │   ├── notifier.py           # Telegram notifications
│   │   │   ├── intelligence_summary.py # Daily intelligence report
│   │   │   ├── job_enrichment.py     # Skill extraction + categorization
│   │   │   ├── analytics_service.py  # Analytics aggregations
│   │   │   ├── opportunity_feed.py   # Opportunity feed builder
│   │   │   └── internship_service.py # Internship filtering
│   │   │
│   │   └── utils/
│   │       ├── logger.py             # Structured logging setup
│   │       └── retry.py              # Exponential backoff retry decorator
│   │
│   └── tests/                         # 21 test files, 346+ tests
│       ├── __init__.py
│       ├── conftest.py               # Shared fixtures
│       ├── test_collection_engine.py
│       ├── test_collections_api.py
│       ├── test_connection.py
│       ├── test_daily_scraper.py
│       ├── test_export_api.py
│       ├── test_export_service.py
│       ├── test_filter_engine.py
│       ├── test_intelligence_summary.py
│       ├── test_jobhive_scraper.py
│       ├── test_logger.py
│       ├── test_main.py
│       ├── test_notifier.py
│       ├── test_preferences_api.py
│       ├── test_repository.py
│       ├── test_retry.py
│       ├── test_schemas.py
│       ├── test_scraper.py
│       ├── test_settings.py
│       └── test_watchlist_api.py
│
├── docs/                              # Frontend (GitHub Pages)
│   ├── index.html                    # Dashboard (pinned sections + metrics)
│   ├── jobs.html                     # Universal smart search with facets
│   ├── career-radar.html            # Personalized scored job matches
│   ├── analytics.html               # Chart.js analytics (7 charts)
│   ├── internships.html             # Internship listings
│   ├── saved.html                   # Saved jobs management
│   ├── watchlist.html               # Company watchlist
│   ├── settings.html                # User settings
│   ├── india-feed.html              # India-focused career radar
│   ├── linkedin.html                # LinkedIn-specific views
│   ├── pipeline.html                # Application pipeline/Kanban
│   ├── regional.html                # Regional radar (South India)
│   ├── today.html                   # Today's fresh jobs
│   ├── css/
│   │   └── style.css                # Light theme CSS
│   ├── js/
│   │   └── app.js                   # Main JavaScript (API calls, rendering)
│   └── assets/
│       └── (icons, images)
│
├── .gitignore
├── .pre-commit-config.yaml
├── DONE.txt                          # Project status tracker
└── PROJECT_DOCUMENTATION.md          # This file
```

---

## 5. API Documentation

### Base URL

- **Production:** `https://jobcopilot-uydv.onrender.com`
- **Local:** `http://localhost:8000`

### Authentication

None required. This is a personal project with CORS set to allow all origins.

### Response Format

All endpoints return JSON. Error responses follow the format:
```json
{
  "detail": "Error description"
}
```

---

### 5.1 Health & Status

#### `GET /health`

Health check endpoint for monitoring and Render's health check configuration.

**Response:**
```json
{
  "status": "healthy",
  "service": "JobCopilot API",
  "version": "1.0.0"
}
```

**Status Codes:** `200 OK`

---

### 5.2 Jobs (Core)

#### `GET /jobs`

Get paginated job listings with optional filters.

**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number (1-indexed) |
| `page_size` | int | 50 | Items per page (1-100) |
| `source` | string | null | Filter by source |
| `location` | string | null | Filter by location |
| `company` | string | null | Filter by company |
| `keyword` | string | null | Filter by keyword in title/description |
| `job_type` | string | null | Filter by job type |
| `date_from` | string | null | Filter from date (YYYY-MM-DD) |
| `date_to` | string | null | Filter to date (YYYY-MM-DD) |
| `search_term` | string | null | Filter by original search term |
| `source_type` | string | null | Filter by source type (jobspy/jobhive) |
| `source_platform` | string | null | Filter by platform (linkedin/indeed/greenhouse/etc.) |

**Response:**
```json
{
  "jobs": [
    {
      "title": "Biomedical Engineer",
      "company": "Philips",
      "location": "Bangalore, India",
      "source": "LinkedIn",
      "source_type": "jobspy",
      "source_platform": "linkedin",
      "job_url": "https://...",
      "description": "...",
      "job_type": "Full-time",
      "salary": "",
      "date_posted": "2025-01-15",
      "search_term": "Biomedical Engineer",
      "created_at": "2025-01-15T08:00:00Z",
      "updated_at": "2025-01-15T08:00:00Z"
    }
  ],
  "total": 557,
  "page": 1,
  "page_size": 50,
  "total_pages": 12
}
```

---

#### `GET /jobs/recent`

Get the 10 most recently posted jobs.

**Response:** Array of `JobResponse` objects.

---

#### `GET /jobs/search`

Full-text search across job title and description using MongoDB text index.

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `q` | string | Yes | Search query |
| `page` | int | No | Page number (default: 1) |
| `page_size` | int | No | Items per page (default: 50) |

**Response:** `PaginatedJobsResponse`

---

#### `GET /jobs/smart-search`

Advanced search with weighted scoring, synonym expansion, and faceted filters.

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `q` | string | Yes | Search query (supports multi-keyword) |
| `page` | int | No | Page number (default: 1) |
| `page_size` | int | No | Items per page (default: 50) |

**Response:**
```json
{
  "results": [
    {
      "title": "Research Associate",
      "company": "Abbott",
      "location": "Bangalore",
      "job_url": "https://...",
      "date_posted": "2025-01-15",
      "source_platform": "greenhouse",
      "description": "First 200 chars...",
      "search_score": 45,
      "score_breakdown": ["+10 title:research", "+8 company:abbott", "+12 collection:Research Engineering"]
    }
  ],
  "total": 23,
  "page": 1,
  "page_size": 50,
  "query": "Abbott Research Associate",
  "expanded_terms": ["abbott", "research associate", "scientist", "project associate", "jrf"],
  "facets": {
    "top_companies": [{"name": "Abbott", "count": 15}],
    "top_locations": [{"name": "Bangalore", "count": 8}],
    "top_platforms": [{"name": "greenhouse", "count": 12}],
    "top_collections": [{"name": "Research Engineering", "count": 18}]
  },
  "suggestions": []
}
```

---

#### `GET /jobs/company/{name}`

Get all jobs from a specific company (case-insensitive match).

**Path Parameters:**
- `name` (string): Company name

**Response:** Array of `JobResponse` objects.

---

#### `GET /companies/{name}/insights`

Get intelligence about a specific company.

**Response:**
```json
{
  "company": "Philips",
  "total_jobs": 42,
  "india_jobs": 18,
  "research_jobs": 5,
  "medtech_jobs": 28,
  "internships": 3,
  "latest_posting": "2025-01-15",
  "days_since_latest": "2 days ago",
  "recent_jobs": [...]
}
```

---

### 5.3 Stats

#### `GET /stats`

Dashboard summary metrics.

**Response:**
```json
{
  "total_jobs": 557,
  "jobs_today": 12,
  "jobs_this_week": 87,
  "saved_jobs": 15,
  "applied_jobs": 8,
  "companies_tracked": 13
}
```

---

### 5.4 Watchlist

#### `GET /watchlist`

Get all companies in the watchlist.

**Response:**
```json
[
  {
    "company_name": "Philips",
    "ats_platform": "workday",
    "tier": "tier1"
  },
  {
    "company_name": "Abbott",
    "ats_platform": "workday",
    "tier": "tier2"
  }
]
```

---

#### `GET /watchlist/ats-info`

Get watchlist companies grouped by ATS platform.

**Response:**
```json
[
  {
    "platform": "workday",
    "companies": ["Philips", "GE HealthCare", "Medtronic", "Abbott"]
  },
  {
    "platform": "greenhouse",
    "companies": ["Niramai"]
  },
  {
    "platform": "lever",
    "companies": ["Dozee"]
  }
]
```

---

#### `POST /watchlist`

Add a company to the watchlist.

**Request Body:**
```json
{
  "company_name": "Stryker",
  "ats_platform": "workday"
}
```

**Validation:**
- `company_name`: 1-100 characters, required
- `ats_platform`: Optional, must be one of: workday, greenhouse, lever, ashby, successfactors
- Maximum 50 watchlist entries

**Response:** `201 Created` or `409 Conflict` (duplicate)

---

#### `PATCH /watchlist/{company}`

Update a watchlist company's tier.

**Path Parameters:**
- `company` (string): Company name

**Request Body:**
```json
{
  "tier": "tier1"
}
```

**Valid tiers:** tier1, tier2, tier3

---

#### `DELETE /watchlist/{company}`

Remove a company from the watchlist.

**Path Parameters:**
- `company` (string): Company name

**Response:** `200 OK` or `404 Not Found`

---

### 5.5 Saved Jobs

#### `POST /save-job`

Save a job for later review.

**Request Body:**
```json
{
  "job_url": "https://...",
  "title": "Biomedical Engineer",
  "company": "Philips",
  "location": "Bangalore",
  "source": "LinkedIn",
  "date_posted": "2025-01-15"
}
```

**Response:** `201 Created` or `409 Conflict` (already saved)

---

#### `DELETE /save-job/{job_url}`

Remove a saved job.

**Path Parameters:**
- `job_url` (string, URL-encoded): Job URL

**Response:** `200 OK` or `404 Not Found`

---

#### `GET /saved-jobs`

Get all saved jobs, ordered by date_saved descending.

**Response:** Array of saved job objects with `date_saved` field.

---

### 5.6 Applied Jobs

#### `POST /apply-job`

Mark a job as applied with initial status.

**Request Body:**
```json
{
  "job_url": "https://...",
  "title": "Research Associate",
  "company": "Abbott",
  "location": "Bangalore",
  "status": "Applied"
}
```

**Valid statuses:** Interested, Applied, Interview, Offer, Rejected

---

#### `PATCH /apply-job/{job_url}`

Update application status.

**Path Parameters:**
- `job_url` (string, URL-encoded): Job URL

**Request Body:**
```json
{
  "status": "Interview"
}
```

---

#### `GET /applied-jobs`

Get all applied jobs, ordered by date_applied descending.

**Response:**
```json
[
  {
    "job_url": "https://...",
    "title": "Research Associate",
    "company": "Abbott",
    "location": "Bangalore",
    "status": "Interview",
    "date_applied": "2025-01-10T08:00:00Z",
    "updated_at": "2025-01-12T10:30:00Z"
  }
]
```

---

### 5.7 Export

#### `GET /export/csv`

Export jobs as CSV file with optional filters.

**Query Parameters:** Same as `GET /jobs` (all filter parameters)

**Response:** CSV file download (Content-Type: text/csv)

**Limit:** Maximum 10,000 records per export.

---

#### `GET /export/xlsx`

Export jobs as Excel file with optional filters.

**Query Parameters:** Same as `GET /jobs` (all filter parameters)

**Response:** XLSX file download (Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)

**Limit:** Maximum 10,000 records per export.

---

### 5.8 Collections

#### `GET /collections`

Get all defined collections with job counts.

**Response:**
```json
[
  {"name": "Medical Technology", "job_count": 45},
  {"name": "Biomedical Engineering", "job_count": 38},
  {"name": "Healthcare AI", "job_count": 22},
  {"name": "Medical Devices", "job_count": 67},
  {"name": "Research Engineering", "job_count": 31},
  {"name": "Embedded Systems", "job_count": 19},
  {"name": "IoT", "job_count": 14},
  {"name": "Python Development", "job_count": 89},
  {"name": "Product Management", "job_count": 12},
  {"name": "Healthcare Technology", "job_count": 28},
  {"name": "Diagnostics and Biosensors", "job_count": 15}
]
```

---

#### `GET /collections/{name}`

Get detailed collection info including keywords and job count.

**Path Parameters:**
- `name` (string): Collection name

**Response:**
```json
{
  "name": "Diagnostics and Biosensors",
  "keywords": ["diagnostics", "biosensor", "biosensing", "point-of-care", "lateral flow", "PCR", "immunoassay", "raman", "sers", "spectroscopy", "microfluidics", "biomarker", "sepsis", "wearable sensor"],
  "job_count": 15
}
```

---

#### `GET /collections/{name}/jobs`

Get all jobs belonging to a specific collection.

**Path Parameters:**
- `name` (string): Collection name

**Response:** Array of job objects matching the collection's keywords.

---

### 5.9 Research

#### `GET /research`

Get research positions (JRF, SRF, Project Associate, Research Scientist, etc.)

**Response:** Array of research job objects.

---

#### `GET /research/recent`

Get recently posted research positions.

**Response:** Array of recent research job objects.

---

### 5.10 Internships

#### `GET /internships`

Get internship listings filtered by internship keywords.

**Keywords matched:** Internship, Trainee, Graduate Engineer, Research Intern, Project Associate, Project Assistant, JRF, SRF, RA, Summer Internship, Industrial Trainee, Associate Engineer, Graduate Trainee, Young Professional, Project Engineer

**Response:** Array of internship job objects.

---

### 5.11 Opportunities

#### `GET /opportunities`

Get the categorized opportunity feed.

**Response:**
```json
{
  "top_companies": [...],
  "new_companies": [...],
  "remote_jobs": [...],
  "internships": [...],
  "research_roles": [...],
  "healthcare_roles": [...]
}
```

---

### 5.12 Analytics

#### `GET /analytics`

Get comprehensive analytics metrics for the dashboard.

**Response:**
```json
{
  "jobs_per_day": [{"date": "2025-01-15", "count": 12}],
  "jobs_per_company": [{"company": "Philips", "count": 42}],
  "jobs_per_source": [{"source": "LinkedIn", "count": 200}],
  "jobs_per_platform": [{"platform": "greenhouse", "count": 150}],
  "jobs_per_location": [{"location": "Bangalore", "count": 120}],
  "jobs_per_collection": [{"collection": "Medical Devices", "count": 67}],
  "top_hiring_companies": [{"company": "Philips", "count": 42}],
  "top_locations": [{"location": "Bangalore", "count": 120}],
  "top_ats_platforms": [{"platform": "greenhouse", "count": 150}],
  "internship_vs_fulltime": {"internships": 45, "fulltime": 512},
  "research_vs_industry": {"research": 108, "industry": 449}
}
```

---

### 5.13 Preferences

#### `POST /preferences/pinned-collections`

Pin a collection to the dashboard. Maximum 5 pinned collections.

**Request Body:**
```json
{
  "name": "Medical Devices"
}
```

**Response:** `200 OK` or `400 Bad Request` (limit reached)

---

#### `DELETE /preferences/pinned-collections/{name}`

Unpin a collection from the dashboard.

**Path Parameters:**
- `name` (string): Collection name

---

#### `POST /preferences/pinned-companies`

Pin a company to the dashboard. Maximum 10 pinned companies.

**Request Body:**
```json
{
  "name": "Philips"
}
```

---

#### `DELETE /preferences/pinned-companies/{name}`

Unpin a company from the dashboard.

---

#### `GET /preferences/dashboard`

Get the personal dashboard with pinned preferences.

**Response:**
```json
{
  "pinned_company_jobs": [...],
  "pinned_collection_jobs": [...],
  "new_research_opportunities": [...]
}
```

---

### 5.14 Career Radar

#### `GET /career-radar`

Get the full personalized career radar with scored and ranked jobs.

**Response:**
```json
{
  "top_matches": [
    {
      "title": "Biomedical Engineer",
      "company": "Philips",
      "location": "Bangalore, India",
      "job_url": "https://...",
      "date_posted": "2025-01-15",
      "source_platform": "workday",
      "score": 87,
      "status": "🔥 Apply Immediately",
      "collections": ["Biomedical Engineering", "Medical Devices"],
      "why": ["Biomedical Engineer role", "Biomedical Engineering match", "India location", "Fresher-friendly", "Posted recently"]
    }
  ],
  "research_matches": [...],
  "internships": [...],
  "watchlist_matches": [...],
  "remote_matches": [...],
  "stats": {
    "total_scored": 557,
    "matches_found": 345
  }
}
```

---

#### `GET /career-radar/top`

High-priority actionable matches only.

**Filters:** score >= 25, posted <= 14 days, not already applied/saved.

**Response:**
```json
{
  "high_priority": [...],
  "stats": {
    "total_scored": 557,
    "matches_found": 345,
    "high_priority_count": 17
  }
}
```

---

#### `GET /career-radar/action-list`

Daily application queue (broader window).

**Filters:** score >= 25, posted <= 30 days, not already applied/saved.

**Response:**
```json
{
  "action_list": [...],
  "stats": {
    "total_scored": 557,
    "matches_found": 345,
    "action_list_count": 42
  }
}
```

---

#### `GET /career-radar/india`

India-focused career radar matches.

**Filters:** Jobs in Indian cities (Bangalore, Chennai, Hyderabad, Pune, Mumbai, Delhi, Noida, Gurugram, Kolkata, Ahmedabad, Kochi, Thiruvananthapuram).

**Response:**
```json
{
  "india_matches": [...],
  "stats": {
    "total_scored": 557,
    "india_count": 25
  }
}
```

---

#### `GET /career-radar/fresh`

Fresh high-scoring jobs for immediate action.

**Filters:** posted <= 3 days, score >= 20, excludes applied/saved.

**Response:**
```json
{
  "fresh_matches": [...],
  "stats": {
    "total_scored": 557,
    "fresh_count": 8
  }
}
```

---

#### `GET /career-radar/apply-now`

Top 10 jobs to apply to right now.

**Rules:** India only, posted <= 14 days, score >= 70, not applied.

**Response:**
```json
{
  "apply_now": [...],
  "stats": {
    "total_scored": 557,
    "apply_now_count": 5
  }
}
```

---

#### `GET /career-radar/profile/biomedical`

Career radar scored with biomedical research profile weights.

**Tuned for:** SERS, biosensors, diagnostics, medical devices research.

**Response:**
```json
{
  "top_matches": [...],
  "stats": {
    "total_scored": 557,
    "matches_found": 280
  }
}
```

---

#### `GET /research-radar`

Research fellowship opportunities from Indian institutions.

**Filters:** JRF, SRF, Project Associate, Research Associate, Research Scientist, Research Fellow, Post-Doctoral, Postdoc, RA, Young Professional.

**Response:**
```json
{
  "all_fellowships": [...],
  "jrf_srf": [...],
  "project_associate": [...],
  "research_associate": [...],
  "stats": {
    "total_fellowship_jobs": 108,
    "scored_matches": 100
  }
}
```

---

#### `GET /watchlist-alerts`

New jobs from watchlist companies posted in the last 7 days.

**Response:**
```json
{
  "alerts": [
    {
      "company": "Philips",
      "tier": "tier1",
      "new_jobs_count": 5,
      "jobs": [
        {
          "title": "Biomedical Engineer",
          "location": "Bangalore",
          "date_posted": "2025-01-15",
          "job_url": "https://..."
        }
      ]
    }
  ],
  "total_companies_hiring": 4,
  "total_new_jobs": 12
}
```

---

### 5.15 Regional Radar

#### `GET /regional/tamilnadu`

Jobs in Tamil Nadu with fresher scoring and district breakdown.

**Locations searched:** Chennai, Coimbatore, Salem, Erode, Madurai, Trichy, Hosur, Vellore, Thanjavur, Tirunelveli, Kanchipuram, Pondicherry, Tamil Nadu.

**Response:**
```json
{
  "region": "Tamil Nadu",
  "jobs": [
    {
      "title": "Graduate Engineer Trainee",
      "company": "Siemens Healthineers",
      "location": "Chennai, Tamil Nadu",
      "job_url": "https://...",
      "date_posted": "2025-01-15",
      "source_platform": "workday",
      "fresher_score": 35
    }
  ],
  "districts": [
    {"name": "Chennai", "count": 15},
    {"name": "Coimbatore", "count": 8}
  ],
  "stats": {
    "total_jobs": 45,
    "fresher_friendly": 28
  }
}
```

---

#### `GET /regional/bangalore`

Jobs in Bangalore/Karnataka with fresher scoring.

**Locations searched:** Bangalore, Bengaluru, Mysuru, Mysore, Mangalore, Mangaluru, Hubli, Belgaum, Belagavi, Karnataka.

---

#### `GET /regional/freshers`

Fresher-friendly jobs across all of South India (fresher_score >= 10).

---

#### `GET /regional/research`

Research positions in South India from institutions like IIT Madras, IISc, NIMHANS, C-CAMP, CSIR-CLRI, SCTIMST, Anna University, VIT, SRM, BITS Pilani, IIT Hyderabad, IIIT Hyderabad, CMC Vellore.

---

#### `GET /regional/internships`

Internships in South India.

---

#### `GET /regional/core-engineering`

Core engineering jobs in South India.

**Keywords:** biomedical, medical device, embedded, firmware, electronics, mechanical, instrumentation, vlsi, signal processing, control systems, robotics, manufacturing, quality, production.

---

#### `GET /regional/district/{district}`

Jobs in a specific district/city with fresher scoring.

**Path Parameters:**
- `district` (string): District or city name (e.g., "coimbatore", "chennai")

---

#### `GET /freshers/bangalore`

Fresher jobs specifically in Bangalore (fresher_score >= 10).

---

#### `GET /freshers/tamilnadu`

Fresher jobs specifically in Tamil Nadu (fresher_score >= 10).

---

#### `GET /freshers/medical-tech`

Fresher medical technology jobs in India.

**Collections matched:** Medical Technology, Medical Devices, Biomedical Engineering, Diagnostics and Biosensors, Healthcare AI.

---

#### `GET /freshers/research`

Fresher research positions (JRF/SRF/RA) in India.

**Keywords:** jrf, srf, project associate, project assistant, research associate, research assistant, research fellow, young professional.

---

#### `GET /freshers/today`

Fresh fresher jobs posted in the last 72 hours, India only.

**Rules:** posted <= 3 days, India location, fresher_score >= 15, not applied.

---

#### `GET /daily-targets`

Top 20 daily application targets — the single most useful endpoint.

**Rules:**
- India only (or Remote)
- Posted <= 7 days
- Career Radar score >= 25
- Fresher friendly (no senior penalty)
- Not already applied or saved

**Response:**
```json
{
  "daily_targets": [
    {
      "title": "Research Associate - Biosensors",
      "company": "IISc",
      "location": "Bangalore",
      "job_url": "https://...",
      "date_posted": "2025-01-15",
      "source_platform": "research_scraper",
      "career_score": 52,
      "fresher_score": 35,
      "combined_score": 87,
      "collections": ["Research Engineering", "Diagnostics and Biosensors"]
    }
  ],
  "stats": {
    "india_recent_jobs": 120,
    "qualified_targets": 35,
    "returned": 20,
    "period": "last 7 days",
    "min_career_score": 25
  }
}
```

---

#### `GET /medtech-freshers`

Medical technology fresher opportunities in India, categorized by role type.

**Categories:**
- Research Associate
- Clinical Research
- Biomedical Engineer
- Medical Device Engineer
- Healthcare AI
- Diagnostics & Biosensors

**Response:**
```json
{
  "categories": {
    "Research Associate": [...],
    "Clinical Research": [...],
    "Biomedical Engineer": [...],
    "Medical Device Engineer": [...],
    "Healthcare AI": [...],
    "Diagnostics & Biosensors": [...]
  },
  "stats": {
    "total_jobs": 85,
    "categories_count": 6
  }
}
```

---

### 5.16 LinkedIn

#### `GET /linkedin/jobs`

Jobs sourced from LinkedIn with optional filters.

**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `keyword` | string | null | Filter by keyword in title |
| `location` | string | null | Filter by location |
| `page` | int | 1 | Page number |
| `page_size` | int | 50 | Items per page (1-100) |

**Response:**
```json
{
  "jobs": [
    {
      "title": "Biomedical Engineer",
      "company": "Philips",
      "location": "Bangalore",
      "job_url": "https://...",
      "date_posted": "2025-01-15",
      "source_platform": "linkedin",
      "salary": "",
      "job_type": "Full-time",
      "skills": ["Python", "Medical Devices", "Signal Processing"],
      "description_preview": "First 200 characters..."
    }
  ],
  "total": 200,
  "page": 1,
  "page_size": 50,
  "source": "linkedin"
}
```

---

#### `GET /linkedin/medtech`

LinkedIn MedTech jobs — Biomedical, Clinical, Research, Devices.

**Keywords matched:** biomedical, medical device, clinical research, research associate, project associate, healthcare ai, quality engineer, regulatory affairs, diagnostics, biosensor, validation engineer, r&d engineer.

---

#### `GET /linkedin/company/{company}`

Hiring analytics for a specific company from LinkedIn data.

**Response:**
```json
{
  "company": "Philips",
  "total_jobs": 42,
  "india_jobs": 18,
  "fresher_jobs": 8,
  "research_roles": 5,
  "medtech_roles": 28,
  "recent_jobs_7d": 6,
  "latest_jobs": [...]
}
```

---

#### `GET /linkedin/hiring-now`

Companies actively hiring this week (last 7 days).

**Response:**
```json
{
  "companies_hiring": [
    {
      "company": "Philips",
      "new_jobs": 6,
      "latest_posting": "2025-01-15",
      "is_medtech": true
    }
  ],
  "total_companies": 20,
  "period": "last 7 days"
}
```

---

#### `GET /linkedin/hiring-trends`

Hiring surge data — companies with increasing job postings (this week vs last week).

**Response:**
```json
{
  "surging_companies": [
    {
      "company": "Abbott",
      "jobs_this_week": 8,
      "jobs_last_week": 3,
      "change_percent": 167,
      "trend": "up",
      "is_medtech": true
    }
  ],
  "medtech_surging": [...],
  "all_trends": [...],
  "stats": {
    "companies_hiring_this_week": 45,
    "companies_hiring_last_week": 38,
    "total_jobs_this_week": 120
  }
}
```

---

#### `GET /linkedin/skills/{job_url}`

Extract and return skills for a specific job.

**Path Parameters:**
- `job_url` (string): Full job URL (path parameter)

**Response:**
```json
{
  "title": "Biomedical Engineer",
  "company": "Philips",
  "skills": ["Python", "MATLAB", "Medical Devices", "ISO 13485"],
  "category": "Medical Devices"
}
```

---

#### `GET /linkedin/categories`

Job count by category across all LinkedIn jobs.

**Response:**
```json
{
  "categories": [
    {"name": "Medical Devices", "count": 45},
    {"name": "Research", "count": 32},
    {"name": "Software Engineering", "count": 28}
  ],
  "total": 200
}
```

---

#### `GET /scraper/status`

Latest scraper run status and job source breakdown.

**Response:**
```json
{
  "total_jobs": 557,
  "by_source": {
    "linkedin": 200,
    "jobhive": 250,
    "research": 50,
    "other": 57
  },
  "last_run": {
    "jobs_found": 45,
    "duplicates_skipped": 30,
    "timestamp": "2025-01-15T02:30:00Z"
  }
}
```

---

### 5.17 Complete Endpoint Summary Table

| # | Method | Endpoint | Router | Description |
|---|---|---|---|---|
| 1 | GET | `/health` | health | Health check |
| 2 | GET | `/jobs` | jobs | Paginated jobs with filters |
| 3 | GET | `/jobs/recent` | jobs | Top 10 recent jobs |
| 4 | GET | `/jobs/search` | jobs | Full-text search |
| 5 | GET | `/jobs/smart-search` | jobs | Weighted smart search |
| 6 | GET | `/jobs/company/{name}` | jobs | Jobs by company |
| 7 | GET | `/companies/{name}/insights` | jobs | Company intelligence |
| 8 | GET | `/stats` | stats | Dashboard metrics |
| 9 | GET | `/watchlist` | watchlist | All watchlist companies |
| 10 | GET | `/watchlist/ats-info` | watchlist | Companies by ATS platform |
| 11 | POST | `/watchlist` | watchlist | Add to watchlist |
| 12 | PATCH | `/watchlist/{company}` | watchlist | Update tier |
| 13 | DELETE | `/watchlist/{company}` | watchlist | Remove from watchlist |
| 14 | POST | `/save-job` | saved | Save a job |
| 15 | DELETE | `/save-job/{job_url}` | saved | Remove saved job |
| 16 | GET | `/saved-jobs` | saved | All saved jobs |
| 17 | POST | `/apply-job` | applied | Mark as applied |
| 18 | PATCH | `/apply-job/{job_url}` | applied | Update status |
| 19 | GET | `/applied-jobs` | applied | All applied jobs |
| 20 | GET | `/export/csv` | export | CSV export |
| 21 | GET | `/export/xlsx` | export | Excel export |
| 22 | GET | `/collections` | collections | All collections |
| 23 | GET | `/collections/{name}` | collections | Collection detail |
| 24 | GET | `/collections/{name}/jobs` | collections | Collection jobs |
| 25 | GET | `/research` | research | Research positions |
| 26 | GET | `/research/recent` | research | Recent research |
| 27 | GET | `/internships` | internships | Internship listings |
| 28 | GET | `/opportunities` | opportunities | Opportunity feed |
| 29 | GET | `/analytics` | analytics | Analytics metrics |
| 30 | POST | `/preferences/pinned-collections` | preferences | Pin collection |
| 31 | DELETE | `/preferences/pinned-collections/{name}` | preferences | Unpin collection |
| 32 | POST | `/preferences/pinned-companies` | preferences | Pin company |
| 33 | DELETE | `/preferences/pinned-companies/{name}` | preferences | Unpin company |
| 34 | GET | `/preferences/dashboard` | preferences | Personal dashboard |
| 35 | GET | `/career-radar` | career_radar | Full career radar |
| 36 | GET | `/career-radar/top` | career_radar | High-priority matches |
| 37 | GET | `/career-radar/action-list` | career_radar | Daily action queue |
| 38 | GET | `/career-radar/india` | career_radar | India feed |
| 39 | GET | `/career-radar/fresh` | career_radar | Fresh matches (3 days) |
| 40 | GET | `/career-radar/apply-now` | career_radar | Top 10 apply now |
| 41 | GET | `/career-radar/profile/biomedical` | career_radar | Biomedical profile |
| 42 | GET | `/research-radar` | career_radar | Research fellowships |
| 43 | GET | `/watchlist-alerts` | career_radar | Watchlist new jobs |
| 44 | GET | `/regional/tamilnadu` | regional | Tamil Nadu jobs |
| 45 | GET | `/regional/bangalore` | regional | Bangalore jobs |
| 46 | GET | `/regional/freshers` | regional | South India freshers |
| 47 | GET | `/regional/research` | regional | Regional research |
| 48 | GET | `/regional/internships` | regional | Regional internships |
| 49 | GET | `/regional/core-engineering` | regional | Core engineering |
| 50 | GET | `/regional/district/{district}` | regional | District-level jobs |
| 51 | GET | `/freshers/bangalore` | regional | Bangalore freshers |
| 52 | GET | `/freshers/tamilnadu` | regional | Tamil Nadu freshers |
| 53 | GET | `/freshers/medical-tech` | regional | MedTech freshers |
| 54 | GET | `/freshers/research` | regional | Research freshers |
| 55 | GET | `/freshers/today` | regional | Today's freshers (72h) |
| 56 | GET | `/daily-targets` | regional | Top 20 daily targets |
| 57 | GET | `/medtech-freshers` | regional | MedTech fresher categories |
| 58 | GET | `/linkedin/jobs` | linkedin | LinkedIn jobs |
| 59 | GET | `/linkedin/medtech` | linkedin | LinkedIn MedTech |
| 60 | GET | `/linkedin/company/{company}` | linkedin | Company insights |
| 61 | GET | `/linkedin/hiring-now` | linkedin | Active hiring |
| 62 | GET | `/linkedin/hiring-trends` | linkedin | Hiring trends |
| 63 | GET | `/linkedin/skills/{job_url}` | linkedin | Job skills |
| 64 | GET | `/linkedin/categories` | linkedin | Job categories |
| 65 | GET | `/scraper/status` | linkedin | Scraper status |

**Total: 65 endpoints across 16 routers**

---

## 6. Career Radar Scoring Engine

### 6.1 Overview

The Career Radar is the core intelligence engine of JobCopilot. It scores every job in the database against a personalized career profile tuned for an IIT Jodhpur M.Tech Medical Technology student. The scoring system combines multiple signals — domain relevance, role fit, freshness, location, and company tracking — into a single actionable score.

### 6.2 Scoring Components

The total score for each job is computed as:

```
Total Score = Collection Weight
            + Role Bonus
            + Early Career Bonus
            + Freshness Bonus
            + Location Bonus
            + Watchlist Bonus
            + Platform Bonus
            - Negative Keyword Penalty
            - Seniority Penalty
```

### 6.3 Collection Weights (Domain Relevance)

Each job is matched against 11 defined collections. When a job's title or description contains a collection's keywords, the collection's weight is added to the score.

| Collection | Weight | Keywords |
|---|---|---|
| **Medical Devices** | 10 | medical device, surgical instrument, diagnostic equipment, implant |
| **Biomedical Engineering** | 10 | biomedical, biomed, bioengineering, biomechanics |
| **Research Engineering** | 10 | research engineer, R&D engineer, research scientist, research associate |
| **Diagnostics and Biosensors** | 10 | diagnostics, biosensor, biosensing, point-of-care, lateral flow, PCR, immunoassay, raman, sers, spectroscopy, microfluidics, biomarker, sepsis, wearable sensor |
| **Medical Technology** | 9 | medical technology, medtech, medical device, clinical engineering |
| **Healthcare AI** | 8 | healthcare AI, medical AI, clinical AI, health informatics, medical imaging AI |
| **Healthcare Technology** | 7 | healthtech, health tech, healthcare technology, digital health, telemedicine |
| **Embedded Systems** | 7 | embedded, firmware, RTOS, microcontroller, ARM |
| **IoT** | 6 | IoT, internet of things, connected devices, smart devices, edge computing |
| **Python Development** | 4 | python, django, flask, fastapi, pandas |
| **Product Management** | 3 | product manager, product owner, product management, product strategy |

**Note:** Each collection is counted only once per job (first keyword match wins).

### 6.4 Role-Specific Bonuses

Roles that directly align with M.Tech Medical Technology receive additional bonus points:

| Role Keyword | Bonus |
|---|---|
| medical device engineer | +15 |
| biomedical engineer | +15 |
| research associate | +15 |
| project associate | +15 |
| clinical research associate | +12 |
| quality engineer | +12 |
| regulatory affairs | +12 |
| validation engineer | +12 |
| r&d engineer | +12 |
| healthcare ai | +10 |
| clinical data analyst | +10 |
| project scientist | +10 |
| research scientist | +10 |
| jrf | +10 |
| srf | +10 |

**Note:** Only the first matching role bonus is applied (highest match wins due to order).

### 6.5 Freshness Bonuses

Recently posted jobs receive higher scores to prioritize actionable opportunities:

| Days Since Posted | Bonus |
|---|---|
| 0 (Today) | +15 |
| 1 (Yesterday) | +10 |
| 2-3 days | +7 |
| 4-7 days | +3 |
| 8-14 days | +1 |
| 15+ days | +0 |

### 6.6 ATS Platform Bonuses

Faster-updating ATS platforms receive a small bonus (their jobs tend to be more current):

| Platform | Bonus |
|---|---|
| Greenhouse | +5 |
| Lever | +4 |
| Ashby | +3 |
| Workday | +1 |
| SuccessFactors | +1 |

### 6.7 Location Bonuses

| Condition | Bonus |
|---|---|
| India (any major city) | +10 |
| Remote | +2 |

**India cities recognized:** Bangalore, Bengaluru, Hyderabad, Chennai, Pune, Mumbai, Delhi, Noida, Gurugram/Gurgaon.

### 6.8 Watchlist Company Bonus

Jobs from companies in the user's watchlist receive:

| Condition | Bonus |
|---|---|
| Company in watchlist | +5 |

### 6.9 Early Career Bonus

Jobs matching the user's career stage (fresher/early career):

| Keyword in Title | Bonus |
|---|---|
| associate, junior, entry, graduate, engineer i, scientist i, research associate, research assistant, project associate, project assistant, trainee, intern, fresher, early career | +10 |

**Note:** Only one early career bonus is applied per job.

### 6.10 Negative Keyword Penalties

Jobs with irrelevant role keywords in the title are penalized:

| Keyword | Penalty |
|---|---|
| sales, marketing, account executive, business development, recruiter, talent acquisition, customer success, SDR, BDR, real estate, financial advisor, insurance agent, content writer, social media manager, graphic designer, copywriter, it support, help desk, network administrator, devops | **-25** |

### 6.11 Seniority Penalties

Jobs too senior for an early-career profile:

| Keyword | Penalty |
|---|---|
| director, principal, vp, vice president, head of, chief, cto, ceo, svp | **-15** |

### 6.12 Score Thresholds & Status Labels

| Score Range | Status Label | Action |
|---|---|---|
| 85+ | 🔥 Apply Immediately | Drop everything and apply |
| 70-84 | ⭐ Strong Match | Apply within 24 hours |
| 50-69 | 👍 Good Match | Apply this week |
| 15-49 | 📋 Optional | Review when free |
| < 15 | (Filtered out) | Not shown |

**Minimum score threshold:** 15 (jobs below this are excluded from results)
**High priority threshold:** 25 (used for /career-radar/top)
**Action list threshold:** 25 (used for /career-radar/action-list)

### 6.13 "Why Recommended" Explanations

Each scored job includes a `why` array explaining the recommendation:

```json
{
  "why": [
    "Biomedical Engineer role",
    "Biomedical Engineering match",
    "Medical Devices match",
    "India location",
    "Fresher-friendly",
    "Posted recently"
  ]
}
```

Explanation categories:
1. **Role match** — Which role bonus was triggered
2. **Collection match** — Top 2 matching collections
3. **Location** — India location or Remote position
4. **Career stage** — Fresher-friendly indicator
5. **Freshness** — Posted recently / Posted this week

### 6.14 Biomedical Research Profile (Alternative Weights)

A second scoring profile tuned specifically for SERS/biosensor/diagnostics research:

| Collection | Default Weight | Biomedical Weight |
|---|---|---|
| Diagnostics and Biosensors | 10 | **10** |
| Biomedical Engineering | 10 | **10** |
| Medical Devices | 10 | **10** |
| Research Engineering | 10 | **10** |
| Medical Technology | 9 | **9** |
| Healthcare AI | 8 | **7** |
| Embedded Systems | 7 | **5** |
| Healthcare Technology | 7 | **5** |
| IoT | 6 | **4** |
| Python Development | 4 | **3** |
| Product Management | 3 | **1** |

### 6.15 Scoring Example

**Job:** "Research Associate - Biosensor Development" at Abbott, Bangalore, posted today, via Greenhouse

```
Collection: Diagnostics and Biosensors    = +10
Collection: Research Engineering          = +10
Role Bonus: research associate            = +15
Early Career: associate                   = +10
Freshness: Today                          = +15
Location: Bangalore (India)              = +10
Watchlist: Abbott (in watchlist)          = +5
Platform: Greenhouse                      = +5
─────────────────────────────────────────
Total Score                               = 80 → ⭐ Strong Match
```

---

## 7. Database Schema

### 7.1 Database Configuration

- **Provider:** MongoDB Atlas (Free Tier M0)
- **Storage:** 512MB
- **Database Name:** `jobcopilot`
- **Region:** AWS Mumbai (ap-south-1)
- **Connection:** PyMongo with connection pooling and retry logic

### 7.2 Collections Overview

| Collection | Documents | Purpose |
|---|---|---|
| `jobs` | 557+ | All scraped job listings |
| `saved_jobs` | Variable | User-saved jobs for later review |
| `applied_jobs` | Variable | Jobs marked as applied with status tracking |
| `company_watchlist` | 13 (seeded) | Companies to track for new postings |
| `scrape_history` | Growing | Record of each scrape run |
| `preferences` | 2 max | Pinned collections and companies |
| `notifications` | Growing | Notification tracking (prevent duplicates) |

### 7.3 `jobs` Collection

The primary collection storing all scraped job listings.

**Schema:**

```json
{
  "title": "Biomedical Engineer",
  "company": "Philips",
  "location": "Bangalore, India",
  "source": "LinkedIn",
  "job_url": "https://www.linkedin.com/jobs/view/123456",
  "description": "Full job description text...",
  "job_type": "Full-time",
  "salary": "₹8-12 LPA",
  "date_posted": "2025-01-15",
  "search_term": "Biomedical Engineer",
  "source_type": "jobspy",
  "source_platform": "linkedin",
  "created_at": "2025-01-15T02:30:00+00:00",
  "updated_at": "2025-01-15T02:30:00+00:00"
}
```

**Fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | Yes | Job title |
| `company` | string | Yes | Company name |
| `location` | string | Yes | Job location |
| `source` | string | Yes | Original source name |
| `job_url` | string | Yes | **Unique** — URL of the job posting |
| `description` | string | No | Full job description |
| `job_type` | string | No | Full-time, Part-time, Contract, Internship |
| `salary` | string | No | Salary information (if available) |
| `date_posted` | string | No | Date posted (YYYY-MM-DD format) |
| `search_term` | string | No | Original search term that found this job |
| `source_type` | string | No | "jobspy" or "jobhive" or "research_scraper" |
| `source_platform` | string | No | linkedin, indeed, naukri, google, greenhouse, lever, ashby, workday, successfactors |
| `created_at` | string | Auto | ISO 8601 timestamp of insertion |
| `updated_at` | string | Auto | ISO 8601 timestamp of last update |

**Indexes:**

| Index | Type | Purpose |
|---|---|---|
| `job_url` | Unique, Ascending | Deduplication — prevents duplicate job entries |
| `date_posted` | Ascending | Sort by recency |
| `source` | Ascending | Filter by source |
| `company` | Ascending | Filter by company |
| `title, description` | Text | Full-text search |
| `source_type` | Ascending | Filter by scraper type |
| `source_platform` | Ascending | Filter by platform |

### 7.4 `saved_jobs` Collection

Jobs saved by the user for later review.

**Schema:**

```json
{
  "job_url": "https://www.linkedin.com/jobs/view/123456",
  "title": "Biomedical Engineer",
  "company": "Philips",
  "location": "Bangalore, India",
  "source": "LinkedIn",
  "date_posted": "2025-01-15",
  "date_saved": "2025-01-15T10:30:00+00:00"
}
```

**Fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `job_url` | string | Yes | **Unique** — URL of the saved job |
| `title` | string | Yes | Job title |
| `company` | string | Yes | Company name |
| `location` | string | Yes | Job location |
| `source` | string | Yes | Source platform |
| `date_posted` | string | Yes | Original posting date |
| `date_saved` | string | Auto | ISO 8601 timestamp when saved |

**Indexes:**
- `job_url`: Unique (prevents saving the same job twice)

### 7.5 `applied_jobs` Collection

Jobs the user has applied to, with status tracking.

**Schema:**

```json
{
  "job_url": "https://www.linkedin.com/jobs/view/123456",
  "title": "Research Associate",
  "company": "Abbott",
  "location": "Bangalore",
  "status": "Interview",
  "date_applied": "2025-01-10T08:00:00+00:00",
  "updated_at": "2025-01-12T10:30:00+00:00"
}
```

**Fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `job_url` | string | Yes | **Unique** — URL of the applied job |
| `title` | string | Yes | Job title |
| `company` | string | Yes | Company name |
| `location` | string | Yes | Job location |
| `status` | string | Yes | Application status |
| `date_applied` | string | Auto | ISO 8601 timestamp when marked as applied |
| `updated_at` | string | Auto | ISO 8601 timestamp of last status update |

**Valid Statuses:** Interested → Applied → Interview → Offer → Rejected

**Indexes:**
- `job_url`: Unique (prevents duplicate application entries)

### 7.6 `company_watchlist` Collection

Companies being tracked for new job postings.

**Schema:**

```json
{
  "company_name": "Philips",
  "ats_platform": "workday",
  "tier": "tier1"
}
```

**Fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `company_name` | string | Yes | **Unique** — Company name (1-100 chars) |
| `ats_platform` | string | No | ATS platform (workday/greenhouse/lever/ashby/successfactors) |
| `tier` | string | No | Priority tier (tier1/tier2/tier3, default: tier3) |

**Constraints:**
- Maximum 50 entries
- Company name: 1-100 characters

**Default Seeded Companies (13):**

| Company | ATS Platform |
|---|---|
| Philips | Workday |
| GE HealthCare | Workday |
| Siemens Healthineers | SuccessFactors |
| Medtronic | Workday |
| Abbott | Workday |
| Dozee | Lever |
| Niramai | Greenhouse |
| Roche | - |
| Boston Scientific | - |
| Johnson and Johnson MedTech | - |
| Becton Dickinson | - |
| Fujifilm Healthcare | - |
| Skanray Technologies | - |

**Indexes:**
- `company_name`: Unique

### 7.7 `scrape_history` Collection

Record of each scrape run for monitoring and debugging.

**Schema:**

```json
{
  "timestamp": "2025-01-15T02:30:00+00:00",
  "jobs_found": 45,
  "duplicates_skipped": 30,
  "errors": ["JobSpy timeout on Naukri"]
}
```

**Fields:**

| Field | Type | Description |
|---|---|---|
| `timestamp` | string | ISO 8601 timestamp of the scrape run |
| `jobs_found` | int | Total jobs collected across all scrapers |
| `duplicates_skipped` | int | Jobs skipped due to duplicate job_url |
| `errors` | array[string] | Error messages from failed scrape attempts |

### 7.8 `preferences` Collection

User preferences for dashboard customization.

**Schema:**

```json
{
  "type": "pinned_collections",
  "items": ["Medical Devices", "Research Engineering", "Healthcare AI"]
}
```

**Fields:**

| Field | Type | Description |
|---|---|---|
| `type` | string | **Unique** — "pinned_collections" or "pinned_companies" |
| `items` | array[string] | List of pinned names |

**Constraints:**
- Maximum 5 pinned collections
- Maximum 10 pinned companies

**Indexes:**
- `type`: Unique

### 7.9 `notifications` Collection

Tracks which jobs have been notified to prevent duplicate notifications.

**Schema:**

```json
{
  "job_url": "https://www.linkedin.com/jobs/view/123456",
  "notified_at": "2025-01-15T02:35:00+00:00"
}
```

**Fields:**

| Field | Type | Description |
|---|---|---|
| `job_url` | string | URL of the notified job |
| `notified_at` | string | ISO 8601 timestamp when notification was sent |

---

## 8. Smart Search Engine

### 8.1 Overview

The Smart Search Engine (v2) provides an intelligent, weighted multi-field search with synonym expansion, multi-keyword tokenization, collection boosting, and faceted filters. It goes beyond simple text matching to deliver relevance-ranked results with explainable scoring.

### 8.2 Architecture

```mermaid
flowchart TD
    INPUT[User Query: "Abbott Bangalore Research Associate"]
    TOKENIZE[Tokenize into keywords]
    EXPAND[Synonym Expansion]
    QUERY[Build MongoDB OR query]
    FETCH[Fetch matching jobs max 100]
    SCORE[Score each job weighted]
    SORT[Sort by score descending]
    FACETS[Compute faceted filters]
    PAGINATE[Paginate results]
    OUTPUT[Return results + facets + suggestions]

    INPUT --> TOKENIZE
    TOKENIZE --> EXPAND
    EXPAND --> QUERY
    QUERY --> FETCH
    FETCH --> SCORE
    SCORE --> SORT
    SORT --> FACETS
    SORT --> PAGINATE
    PAGINATE --> OUTPUT
    FACETS --> OUTPUT
```

### 8.3 Multi-Keyword Tokenization

The search engine handles complex multi-keyword queries by:

1. **Extracting known phrases first** (longest match wins)
2. **Splitting remaining words** by spaces

**Known multi-word phrases preserved as single tokens:**
- research associate, research engineer, project associate, project assistant
- medical device, medical technology, healthcare ai, healthcare technology
- embedded systems, biomedical engineer, product manager, machine learning
- computer vision, deep learning, data scientist, graduate engineer
- research intern, clinical research, r&d engineer, full stack, backend developer

**Example tokenization:**

| Input | Tokens |
|---|---|
| `Abbott Bangalore` | ["abbott", "bangalore"] |
| `Research Associate` | ["research associate"] |
| `Abbott Bangalore Research Associate` | ["research associate", "abbott", "bangalore"] |
| `Medical Device Engineer India` | ["medical device", "engineer", "india"] |

### 8.4 Synonym Expansion

Each token is expanded with domain-specific synonyms:

| Token | Expanded To |
|---|---|
| `biomedical` | medical technology, medical device, healthcare, diagnostics, clinical |
| `medtech` | medical technology, medical device, healthcare technology |
| `research` | scientist, research associate, project associate, jrf, srf, r&d |
| `embedded` | firmware, microcontroller, esp32, stm32, rtos |
| `iot` | internet of things, connected devices, smart devices, edge computing, wireless sensor |
| `python` | django, flask, fastapi, backend developer |
| `ai` | machine learning, deep learning, artificial intelligence, computer vision, nlp |
| `healthcare` | medical, clinical, health tech, digital health, telemedicine |
| `intern` | internship, trainee, graduate engineer, fresher |
| `remote` | work from home, wfh, anywhere, distributed |
| `bangalore` | bengaluru, karnataka |
| `gurgaon` | gurugram |
| `delhi` | noida, new delhi, ncr |

**Bidirectional matching:** If the query matches a synonym value, the key is also added.

### 8.5 Weighted Scoring

Each field match contributes a different weight to the total score:

| Field | Weight | Rationale |
|---|---|---|
| **Collection** | 12 | Domain relevance is the strongest signal |
| **Title** | 10 | Title match indicates direct role fit |
| **Company** | 8 | Company match is highly relevant |
| **Location** | 4 | Location is a filter, not a relevance signal |
| **Description** | 3 | Description matches are weaker (common words) |

**Freshness bonus in search:**
- Posted <= 3 days: +3
- Posted 4-7 days: +2
- Posted 8-14 days: +1

### 8.6 Collection Boosting

When a search term matches a collection's name or keywords, and the job also contains that collection's keywords, a +12 collection boost is applied. This ensures domain-relevant jobs rank higher.

**Example:** Searching for "biomedical" → matches "Biomedical Engineering" collection → if job description contains "biomedical" → +12 boost.

### 8.7 Score Breakdown (Explainable Ranking)

Each result includes a `score_breakdown` array explaining exactly why it ranked where it did:

```json
{
  "search_score": 45,
  "score_breakdown": [
    "+10 title:research associate",
    "+8 company:abbott",
    "+4 location:bangalore",
    "+12 collection:Research Engineering",
    "+3 description:research",
    "+3 freshness"
  ]
}
```

### 8.8 Faceted Filters

After scoring, the engine computes facets from the result set:

| Facet | Description | Max Items |
|---|---|---|
| `top_companies` | Companies with most matching jobs | 10 |
| `top_locations` | Locations with most matching jobs | 10 |
| `top_platforms` | Source platforms with most matches | 5 |
| `top_collections` | Collections with most matches | 10 |

### 8.9 Suggestions on Empty Results

When no results are found, the engine returns helpful suggestions:

```json
{
  "suggestions": [
    "Biomedical Engineer",
    "Medical Device",
    "Research Associate",
    "Python Developer",
    "Embedded Systems",
    "Healthcare AI",
    "Abbott",
    "Bangalore",
    "Remote",
    "Internship"
  ]
}
```

### 8.10 Performance

- **Maximum results fetched:** 100 (from MongoDB)
- **Scoring:** In-memory after fetch
- **Pagination:** Applied after scoring and sorting
- **Typical response time:** < 500ms for 557 jobs

---

## 9. Regional Radar (South India Fresher)

### 9.1 Overview

The Regional Radar is a specialized subsystem designed for a fresher from South India. It provides location-based job filtering with a fresher-friendliness scoring system, district-level granularity, and core engineering focus.

### 9.2 Location Definitions

#### Tamil Nadu Locations
```
Chennai, Coimbatore, Salem, Erode, Madurai, Trichy (Tiruchirappalli),
Hosur, Vellore, Thanjavur, Tirunelveli, Kanchipuram, Pondicherry,
Puducherry, Tamil Nadu
```

#### Bangalore / Karnataka Locations
```
Bangalore, Bengaluru, Mysuru, Mysore, Mangalore, Mangaluru,
Hubli, Belgaum, Belagavi, Karnataka
```

#### All South India Locations
```
All Tamil Nadu + All Karnataka +
Hyderabad, Telangana, Kerala, Kochi, Thiruvananthapuram,
Andhra Pradesh, Visakhapatnam, Vijayawada
```

### 9.3 Fresher Scoring System

The fresher score determines how suitable a job is for a fresh graduate:

| Signal | Score | Condition |
|---|---|---|
| **Fresher keyword in title** | +20 | fresher, graduate, entry level, junior, associate, trainee, GET, GAT, graduate engineer trainee, apprentice, intern, project associate, jrf, research assistant, 0-2 years, 0-1 years, young professional, project assistant |
| **Seniority keyword in title** | -20 | senior, lead, principal, manager, director, head, vp, chief, architect, staff |
| **Low experience in description** | +15 | "0-2 years" or "0-1 years" or "freshers" found in description |
| **High experience in description** | -15 | "5+ years" or "7+ years" or "10+ years" found in description |
| **Core engineering keyword** | +5 | biomedical, medical device, embedded, firmware, electronics, mechanical, instrumentation, vlsi, signal processing, control systems, robotics, manufacturing, quality, production |
| **Posted <= 3 days** | +10 | Freshness bonus |
| **Posted 4-7 days** | +5 | Freshness bonus |

### 9.4 Fresher Score Interpretation

| Score | Interpretation |
|---|---|
| 35+ | Highly fresher-friendly (apply immediately) |
| 20-34 | Good for freshers |
| 10-19 | Possibly suitable |
| 0-9 | Neutral |
| < 0 | Not suitable for freshers (too senior) |

### 9.5 South India Research Institutions

The Regional Radar specifically tracks positions from:

| Institution | Location |
|---|---|
| IIT Madras | Chennai |
| IISc | Bangalore |
| NIMHANS | Bangalore |
| C-CAMP | Bangalore |
| CSIR-CLRI | Chennai |
| SCTIMST | Thiruvananthapuram |
| Anna University | Chennai |
| VIT | Vellore |
| SRM | Chennai |
| BITS Pilani | Multiple |
| IIT Hyderabad | Hyderabad |
| IIIT Hyderabad | Hyderabad |
| CMC Vellore | Vellore |

### 9.6 Core Engineering Keywords

Jobs matching these keywords receive a +5 fresher score bonus:

```
biomedical, medical device, embedded, firmware, electronics,
mechanical, instrumentation, vlsi, signal processing,
control systems, robotics, manufacturing, quality, production
```

### 9.7 Daily Targets Algorithm

The `/daily-targets` endpoint combines Career Radar and Regional Radar scoring:

```
Combined Score = Career Radar Score + max(Fresher Score, 0)
```

**Filters applied:**
1. India location only (or Remote)
2. Posted within last 7 days
3. Career Radar score >= 25
4. Not already applied
5. Not already saved

**Output:** Top 20 targets sorted by combined score.

### 9.8 MedTech Freshers Categories

The `/medtech-freshers` endpoint organizes jobs into 6 role categories aligned with M.Tech Medical Technology:

| Category | Keywords |
|---|---|
| Research Associate | research associate, project associate, research assistant |
| Clinical Research | clinical research, clinical data, clinical engineer |
| Biomedical Engineer | biomedical engineer, biomedical, bioengineering |
| Medical Device Engineer | medical device, medtech, regulatory affairs, validation engineer, quality engineer |
| Healthcare AI | healthcare ai, medical ai, health informatics, clinical ai |
| Diagnostics & Biosensors | diagnostics, biosensor, spectroscopy, point-of-care, biomarker |

---

## 10. Environment Variables

### 10.1 Required Variables

| Variable | Description | Example |
|---|---|---|
| `MONGODB_URI` | MongoDB Atlas connection string | `mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority` |

### 10.2 Optional Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_NAME` | `jobcopilot` | MongoDB database name |
| `TELEGRAM_BOT_TOKEN` | (disabled) | Telegram Bot API token for notifications |
| `TELEGRAM_CHAT_ID` | (disabled) | Telegram chat ID to send notifications to |
| `SEARCH_TERMS` | See below | Comma-separated job search terms |
| `LOCATIONS` | See below | Comma-separated locations to search |
| `JOB_SOURCES` | `linkedin,indeed,naukri,google` | Comma-separated job sources for JobSpy |
| `SCHEDULE_TIME` | `08:00` | Daily scrape time in HH:MM 24-hour format |
| `PORT` | `8000` | Server port (Render sets this automatically) |

### 10.3 Default Search Terms

```
Biomedical Engineer, Medical Device Engineer, Research Engineer,
Research Associate, Healthcare Technology, Healthcare AI,
Signal Processing Engineer, Embedded Systems Engineer, IoT Engineer,
Python Developer, Backend Developer, R&D Engineer,
Clinical Data Analyst, Biomedical Research, Medical Technology,
Research Scientist
```

### 10.4 Default Locations

```
India, Remote, Bangalore, Hyderabad, Chennai, Pune,
Mumbai, Delhi, Noida, Gurugram, Ahmedabad, Kolkata
```

### 10.5 Default Job Sources

```
linkedin, indeed, naukri, google
```

### 10.6 GitHub Actions Secrets

The following secrets must be configured in the GitHub repository settings:

| Secret | Used By | Description |
|---|---|---|
| `MONGODB_URI` | daily-scraper.yml | MongoDB Atlas connection string |

### 10.7 Render Environment Variables

Configure these in the Render dashboard:

| Variable | Value |
|---|---|
| `MONGODB_URI` | MongoDB Atlas connection string |
| `DATABASE_NAME` | `jobcopilot` |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |
| `SEARCH_TERMS` | Comma-separated search terms |
| `LOCATIONS` | Comma-separated locations |
| `JOB_SOURCES` | `linkedin,indeed,naukri,google` |

### 10.8 `.env.example` Template

```env
# MongoDB connection string (required)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority

# Database name (default: jobcopilot)
DATABASE_NAME=jobcopilot

# Telegram Bot API credentials (optional, notifications disabled if not set)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-telegram-chat-id

# Comma-separated search terms (India-focused for Medical Technology profile)
SEARCH_TERMS=Biomedical Engineer,Medical Device Engineer,Research Associate,Research Engineer,Clinical Research,Healthcare AI,Embedded Systems Engineer,IoT Engineer,Python Developer,Fresher Engineer,Graduate Engineer Trainee,Project Associate,JRF,Biosensor,Diagnostics

# Comma-separated locations (India-first)
LOCATIONS=India,Bangalore,Chennai,Coimbatore,Hyderabad,Pune,Mumbai,Gurgaon,Remote,Delhi,Noida

# Comma-separated job sources (linkedin, indeed, naukri, google)
JOB_SOURCES=linkedin,indeed,naukri,google

# Daily scrape schedule time in HH:MM 24-hour format (default: 08:00)
SCHEDULE_TIME=08:00
```

---

## 11. Installation & Local Development Guide

### 11.1 Prerequisites

| Requirement | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Backend runtime |
| pip | Latest | Package management |
| Git | Latest | Version control |
| MongoDB Atlas account | Free tier | Database |
| Telegram Bot (optional) | - | Notifications |

### 11.2 Clone the Repository

```bash
git clone https://github.com/sukesh-periyasamy/jobcopilot.git
cd jobcopilot
```

### 11.3 Backend Setup

#### Windows

```powershell
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy environment template
copy .env.example .env

# Edit .env with your MongoDB URI
notepad .env
```

#### Linux / macOS

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your MongoDB URI
nano .env
```

### 11.4 MongoDB Atlas Setup

1. Go to [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create a free M0 cluster (AWS Mumbai recommended for India)
3. Create a database user with read/write access
4. Whitelist your IP address (or 0.0.0.0/0 for development)
5. Get the connection string and add it to `.env`:

```env
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
```

### 11.5 Running the Backend

#### Start the API Server

```bash
cd backend
python main.py serve
```

The server starts at `http://localhost:8000`.

#### Run a Single Scrape

```bash
cd backend
python main.py scrape
```

#### Run the Daily Scraper Directly

```bash
cd backend
python daily_scraper.py
```

### 11.6 Running the Frontend Locally

The frontend is static HTML/CSS/JS. You can serve it with any static file server:

```bash
# Using Python's built-in server
cd docs
python -m http.server 3000
```

Then open `http://localhost:3000` in your browser.

**Important:** Update the API base URL in `docs/js/app.js` to point to `http://localhost:8000` for local development.

### 11.7 Running Tests

```bash
cd backend

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_career_radar.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run only property-based tests (Hypothesis)
pytest -k "hypothesis"
```

### 11.8 CLI Commands

```bash
# Show help
python main.py

# Start API server
python main.py serve

# Run scraper
python main.py scrape
```

### 11.9 Development Workflow

1. **Make changes** to backend code
2. **Run tests:** `pytest`
3. **Start server:** `python main.py serve`
4. **Test endpoints:** Use browser or curl
5. **Check frontend:** Open `docs/index.html` in browser

### 11.10 Common Issues

| Issue | Solution |
|---|---|
| `MONGODB_URI not set` | Ensure `.env` file exists with valid URI |
| `Connection timeout` | Check MongoDB Atlas IP whitelist |
| `ModuleNotFoundError` | Activate virtual environment |
| `Port already in use` | Kill existing process or change PORT env var |
| `JobSpy import error` | Install with `pip install python-jobspy` |
| `pyarrow version conflict` | Ensure `pyarrow>=18.0.0` in requirements |

---

## 12. Deployment Guide

### 12.1 GitHub Pages (Frontend)

The frontend is deployed automatically from the `docs/` folder on the `main` branch.

#### Setup Steps:

1. Go to repository **Settings** → **Pages**
2. Set **Source** to "Deploy from a branch"
3. Set **Branch** to `main` and folder to `/docs`
4. Click **Save**

#### Configuration:

- Update `docs/js/app.js` to point to the production backend URL:
  ```javascript
  const API_BASE = "https://jobcopilot-uydv.onrender.com";
  ```

#### URL:
`https://sukesh-periyasamy.github.io/jobcopilot/`

---

### 12.2 Render Web Service (Backend API)

#### Setup Steps:

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New** → **Web Service**
3. Connect your GitHub repository
4. Configure:

| Setting | Value |
|---|---|
| Name | jobcopilot |
| Region | Oregon (or closest) |
| Branch | main |
| Root Directory | backend |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Plan | Free |

5. Add environment variables (see Section 10.7)
6. Set health check path to `/health`

#### Important Notes:

- Free tier spins down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds (cold start)
- The `runtime.txt` file pins Python to 3.11.11

---

### 12.3 Render Cron Job (Daily Scraper)

#### Setup Steps:

1. Go to Render Dashboard → **New** → **Cron Job**
2. Configure:

| Setting | Value |
|---|---|
| Name | jobcopilot-scraper |
| Region | Oregon |
| Branch | main |
| Root Directory | backend |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Command | `python daily_scraper.py` |
| Schedule | `30 2 * * *` (08:00 IST) |
| Plan | Free |

3. Add the same environment variables as the web service

---

### 12.4 MongoDB Atlas Setup

#### Cluster Configuration:

| Setting | Value |
|---|---|
| Tier | M0 (Free) |
| Provider | AWS |
| Region | Mumbai (ap-south-1) |
| Storage | 512MB |
| Database | jobcopilot |

#### Network Access:

Add the following IPs to the whitelist:
- Your local IP (for development)
- `0.0.0.0/0` (allow all — acceptable for personal project)
- Render's outbound IPs (if restricting access)

#### Database User:

Create a user with `readWrite` role on the `jobcopilot` database.

#### Collections:

Collections are created automatically on first use. Indexes are ensured by the `JobsRepository.ensure_indexes()` method on startup.

---

### 12.5 GitHub Actions Configuration

#### Daily Scraper Workflow (`.github/workflows/daily-scraper.yml`)

**Schedule:** `cron: '30 2 * * *'` (08:00 AM IST = 02:30 UTC)

**Required Secrets:**
- `MONGODB_URI` — MongoDB Atlas connection string

**Steps:**
1. Checkout repository
2. Setup Python 3.11
3. Install dependencies
4. Verify critical dependencies (pyarrow, pandas, requests)
5. Test MongoDB connection
6. Run scraper (`python daily_scraper.py`)

**Environment Variables (hardcoded in workflow):**
```yaml
SEARCH_TERMS: "Biomedical Engineer,Medical Device Engineer,Research Associate,..."
LOCATIONS: "India,Bangalore,Chennai,Coimbatore,Hyderabad,Pune,Mumbai,..."
JOB_SOURCES: "linkedin,indeed,naukri,google"
```

#### Daily Email Workflow (`.github/workflows/daily-email.yml`)

**Schedule:** `cron: '35 2 * * *'` (08:05 AM IST)

Sends a daily email summary of new jobs and career radar matches.

#### Publish to PyPI Workflow (`.github/workflows/publish-to-pypi.yml`)

Triggered on release creation. Publishes the package to PyPI.

---

### 12.6 Deployment Checklist

- [ ] MongoDB Atlas cluster created and accessible
- [ ] Database user created with readWrite permissions
- [ ] IP whitelist configured (0.0.0.0/0 for simplicity)
- [ ] Render Web Service deployed with correct env vars
- [ ] Render Cron Job configured with correct schedule
- [ ] GitHub Pages enabled on docs/ folder
- [ ] GitHub Actions secrets configured (MONGODB_URI)
- [ ] Frontend API_BASE URL updated to production backend
- [ ] Health check endpoint responding at /health
- [ ] Telegram bot created and token configured (optional)
- [ ] First manual scrape run successful
- [ ] Daily cron job verified (check scrape_history collection)

---

## 13. Testing

### 13.1 Overview

JobCopilot has a comprehensive test suite with **346+ tests** covering all major components. The tests use pytest as the runner and Hypothesis for property-based testing.

### 13.2 Test Statistics

| Metric | Value |
|---|---|
| Total tests | 346+ |
| Test files | 21 |
| Test framework | pytest |
| Property-based testing | Hypothesis |
| Async support | pytest-asyncio |
| Mocking | unittest.mock |
| All tests passing | ✅ Yes |

### 13.3 Test Files

| File | Tests | Description |
|---|---|---|
| `test_settings.py` | ~25 | Settings loading, validation, defaults |
| `test_repository.py` | ~40 | All CRUD operations, pagination, indexes |
| `test_scraper.py` | ~20 | JobSpy scraper logic |
| `test_jobhive_scraper.py` | ~15 | JobHive ATS scraper |
| `test_daily_scraper.py` | ~25 | Full workflow, retry logic, error handling |
| `test_notifier.py` | ~20 | Telegram notifications, message formatting |
| `test_filter_engine.py` | ~15 | MongoDB query building |
| `test_collection_engine.py` | ~20 | Collection classification |
| `test_collections_api.py` | ~15 | Collections API endpoints |
| `test_watchlist_api.py` | ~20 | Watchlist CRUD endpoints |
| `test_preferences_api.py` | ~15 | Preferences API endpoints |
| `test_export_api.py` | ~10 | CSV/XLSX export |
| `test_export_service.py` | ~10 | Export service logic |
| `test_schemas.py` | ~20 | Pydantic model validation |
| `test_connection.py` | ~10 | MongoDB connection, retry, singleton |
| `test_retry.py` | ~15 | Retry decorator with backoff |
| `test_logger.py` | ~5 | Logging configuration |
| `test_main.py` | ~15 | CLI commands, FastAPI app |
| `test_intelligence_summary.py` | ~15 | Intelligence report generation |
| `conftest.py` | - | Shared fixtures and mocks |

### 13.4 Running Tests

```bash
cd backend

# Run all tests
pytest

# Verbose output with test names
pytest -v

# Run specific test file
pytest tests/test_career_radar.py

# Run tests matching a pattern
pytest -k "test_score"

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run with HTML coverage report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser

# Run only property-based tests
pytest -k "hypothesis or property"

# Run with Hypothesis verbose output
pytest --hypothesis-show-statistics

# Fail fast (stop on first failure)
pytest -x

# Run in parallel (if pytest-xdist installed)
pytest -n auto
```

### 13.5 Property-Based Testing (Hypothesis)

JobCopilot uses Hypothesis for property-based testing, which generates random inputs to find edge cases that manual tests might miss.

**Key properties tested:**

1. **Settings validation:**
   - Any valid HH:MM time string passes validation
   - Invalid time formats always raise ValueError
   - Comma-separated lists always produce non-empty results

2. **Filter engine:**
   - Any combination of filter criteria produces a valid MongoDB query
   - Empty filters produce an empty query `{}`
   - Filters with values always produce `$and` conditions

3. **Repository:**
   - Bulk insert with empty list always returns zero counts
   - Duplicate URLs are always skipped (idempotency)
   - Pagination always returns valid page metadata

4. **Scoring:**
   - Score is always an integer
   - Negative keywords always reduce score
   - Collection matches always increase score

### 13.6 Test Fixtures (conftest.py)

Common fixtures used across tests:

```python
@pytest.fixture
def mock_database():
    """Mock MongoDB database for unit tests."""
    ...

@pytest.fixture
def sample_job_record():
    """A valid JobRecord instance for testing."""
    ...

@pytest.fixture
def sample_settings():
    """Settings instance with test values."""
    ...

@pytest.fixture
def mock_jobs_collection():
    """Mock MongoDB jobs collection."""
    ...
```

### 13.7 Test Patterns

**Unit tests** — Test individual functions in isolation:
```python
def test_freshness_bonus_today():
    service = CareerRadarService()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    bonus = service._freshness_bonus(today)
    assert bonus == 15
```

**Integration tests** — Test API endpoints with mocked database:
```python
def test_get_career_radar_top(client, mock_db):
    response = client.get("/career-radar/top")
    assert response.status_code == 200
    data = response.json()
    assert "high_priority" in data
    assert "stats" in data
```

**Property-based tests** — Test invariants with random inputs:
```python
@given(st.text(min_size=1, max_size=100))
def test_tokenize_never_empty(query):
    service = SmartSearchService()
    tokens = service._tokenize_query(query)
    assert len(tokens) >= 1
```

### 13.8 Mocking Strategy

- **MongoDB:** All database operations are mocked using `unittest.mock.patch`
- **External APIs:** Telegram, HTTP requests are mocked
- **Time:** `datetime.now()` is mocked for freshness tests
- **Environment:** `os.environ` is patched for settings tests

---

## 14. Current Status & Future Roadmap

### 14.1 Current Statistics

| Metric | Value |
|---|---|
| Total jobs scraped | 557+ |
| Career Radar matches | 345 (62% match rate) |
| India feed matches | 25 |
| Action list items | 17 high-priority |
| Research fellowships found | 108 |
| Research fellowships scored | 100 |
| Collections defined | 11 |
| Watchlist companies | 13 (seeded) |
| API endpoints | 65 |
| Test files | 21 |
| Tests passing | 346+ |
| Frontend pages | 13 |
| Daily scrape sources | 9 (4 job boards + 5 ATS platforms) |

### 14.2 Version History

| Version | Features |
|---|---|
| **v1.0** | Core scraping (JobSpy), basic API, MongoDB storage |
| **v1.1** | Watchlist, saved jobs, applied jobs, export, stats |
| **v1.2** | Collections, opportunities, internships, research, analytics, preferences |
| **v1.3** | Career Radar scoring engine, research radar, watchlist alerts |
| **v1.4** | Smart Search v2, regional radar, LinkedIn analytics, daily targets, fresher radar |

### 14.3 What's Working Well

- ✅ **Daily automation** — Scraper runs reliably at 08:00 IST via GitHub Actions
- ✅ **Deduplication** — Unique index on job_url prevents duplicates across runs
- ✅ **Career Radar** — Scoring engine surfaces relevant jobs with explainable rankings
- ✅ **Smart Search** — Multi-keyword search with synonyms finds relevant results
- ✅ **Regional Radar** — South India fresher focus with district-level granularity
- ✅ **Telegram notifications** — Daily intelligence summary + top matches
- ✅ **Zero cost** — Entire system runs on free tiers
- ✅ **Test coverage** — 346+ tests with property-based testing
- ✅ **Research Radar** — Dedicated feed for JRF/SRF/RA positions

### 14.4 Known Limitations

| Limitation | Impact | Workaround |
|---|---|---|
| Render free tier cold starts | 30s delay after inactivity | Health check keeps it warm |
| MongoDB 512MB limit | ~10K jobs before cleanup needed | Periodic old job deletion |
| LinkedIn scraper deprecated | Relies on JobSpy for LinkedIn | JobSpy handles LinkedIn via Render |
| No resume matching | Manual relevance assessment | Career Radar scoring compensates |
| No login/auth | Single user only | Personal project, no auth needed |
| CORS allow all | Security concern for production | Acceptable for personal use |

### 14.5 Future Roadmap

#### Phase 1: Additional Data Sources (Planned)

| Feature | Priority | Description |
|---|---|---|
| Naukri direct scraper | High | Direct Naukri scraping for India-specific jobs |
| Freshersworld scraper | High | Dedicated fresher job board |
| Internshala scraper | Medium | Internship-focused platform |
| TimesJobs scraper | Medium | Additional India job board |
| Monster India scraper | Low | Legacy job board |

#### Phase 2: Intelligence Enhancements (Planned)

| Feature | Priority | Description |
|---|---|---|
| Resume matching | High | Score jobs against uploaded resume |
| Skill gap analysis | High | Identify missing skills for target roles |
| Application tracking Kanban | Medium | Visual pipeline board improvements |
| Company research automation | Medium | Auto-fetch company info (Glassdoor, LinkedIn) |
| Salary estimation | Medium | Predict salary ranges from similar roles |
| Interview preparation | Low | Generate interview questions per role |

#### Phase 3: Platform Improvements (Planned)

| Feature | Priority | Description |
|---|---|---|
| Email notifications | High | Daily email digest (in addition to Telegram) |
| Mobile-responsive frontend | Medium | Better mobile experience |
| Dark mode | Low | Theme toggle |
| PWA support | Low | Installable web app |
| Browser extension | Low | Save jobs from any job board |

#### Phase 4: Advanced Analytics (Planned)

| Feature | Priority | Description |
|---|---|---|
| Hiring velocity tracking | Medium | Track how fast companies fill roles |
| Market demand trends | Medium | Which skills are trending up/down |
| Application success rate | Medium | Track conversion rates |
| Competitor analysis | Low | Compare with similar profiles |

### 14.6 Technical Debt

| Item | Priority | Description |
|---|---|---|
| Add type hints to all functions | Medium | Some older code lacks type annotations |
| Async database operations | Low | Currently synchronous PyMongo |
| Rate limiting | Low | No rate limiting on API (personal use) |
| API versioning | Low | No /v1/ prefix (single user) |
| Structured logging | Low | Basic logging, could use structured JSON |
| Docker containerization | Low | Would simplify local development |

---

## Appendix A: Data Sources Detail

### A.1 JobSpy (python-jobspy)

JobSpy is a Python library that scrapes job listings from major job boards.

**Platforms scraped:**
- LinkedIn
- Indeed
- Naukri
- Google Jobs

**Configuration:**
- Search terms: 15 configured (Biomedical Engineer, Medical Device Engineer, etc.)
- Locations: 11 configured (India, Bangalore, Chennai, etc.)
- Results per search: Limited by platform

**Runtime:** Runs on Render (Python 3.11 required for full compatibility)

### A.2 JobHive (jobhive-py)

JobHive scrapes jobs from ATS (Applicant Tracking System) platforms used by companies.

**Platforms scraped:**
- Greenhouse
- Lever
- Ashby
- Workday
- SuccessFactors (SAP)

**How it works:**
1. Takes company names from the watchlist
2. Queries each company's ATS platform API
3. Returns structured job listings

### A.3 Research Institution Scraper

Custom scraper for Indian research institutions.

**Institutions tracked:**
- IISc (Indian Institute of Science)
- DRDO (Defence Research and Development Organisation)
- C-DAC (Centre for Development of Advanced Computing)
- AIIMS (All India Institute of Medical Sciences)
- IITs (Indian Institutes of Technology)
- CSIR Labs
- ISRO (Indian Space Research Organisation)
- BARC (Bhabha Atomic Research Centre)
- THSTI (Translational Health Science and Technology Institute)
- NIBMG (National Institute of Biomedical Genomics)
- ICMR (Indian Council of Medical Research)
- NIMHANS (National Institute of Mental Health and Neuro-Sciences)
- SCTIMST (Sree Chitra Tirunal Institute for Medical Sciences)

### A.4 LinkedIn Scraper (Deprecated)

The dedicated LinkedIn scraper using `linkedin-jobs-scraper` package has been deprecated because LinkedIn's anonymous access strategy no longer works reliably. LinkedIn jobs are now collected via JobSpy on Render.

---

## Appendix B: Notification System

### B.1 Telegram Bot

**Features:**
- New job notifications (when new jobs are inserted)
- Watchlist match alerts (when a watchlist company posts a new job)
- Daily intelligence summary (overview of the day's scrape)
- Career Radar top 10 (highest-scoring matches)

**Message format:**
```
🎯 Career Radar — Top Matches

1. ⭐ Biomedical Engineer
   🏢 Philips | 📍 Bangalore, India
   Score: 87 | Biomedical Engineering, Medical Devices
   🔗 https://...

2. ⭐ Research Associate
   🏢 Abbott | 📍 Bangalore
   Score: 75 | Research Engineering, Diagnostics
   🔗 https://...
```

**Message splitting:** Messages exceeding Telegram's 4096 character limit are automatically split into multiple messages.

### B.2 Intelligence Summary

The daily intelligence summary includes:
- Total new jobs found
- Top companies hiring
- Watchlist company activity
- High-priority matches
- Source breakdown

### B.3 Watchlist Alerts

When a new job is inserted from a watchlist company, an immediate alert is sent:
```
🏢 Watchlist Alert: Philips

New job posted:
📋 Biomedical Engineer
📍 Bangalore, India
🔗 https://...
```

---

## Appendix C: Frontend Pages

### C.1 Page Inventory

| Page | File | Description |
|---|---|---|
| Dashboard | `index.html` | Personal pinned sections + metrics + recent jobs |
| Jobs | `jobs.html` | Universal smart search with facets |
| Career Radar | `career-radar.html` | Personalized scored job matches with tabs |
| Analytics | `analytics.html` | Chart.js analytics dashboard (7 charts) |
| Internships | `internships.html` | Internship listings with keyword filter |
| Saved | `saved.html` | Saved jobs management |
| Watchlist | `watchlist.html` | Company watchlist management |
| Settings | `settings.html` | User settings and preferences |
| India Feed | `india-feed.html` | India-focused career radar |
| LinkedIn | `linkedin.html` | LinkedIn-specific views and analytics |
| Pipeline | `pipeline.html` | Application pipeline/Kanban board |
| Regional | `regional.html` | Regional radar (South India) |
| Today | `today.html` | Today's fresh jobs |

### C.2 Dashboard (index.html)

The main dashboard shows:
- **Stats cards:** Total jobs, jobs today, jobs this week, saved, applied, companies tracked
- **Pinned company jobs:** Latest jobs from pinned companies
- **Pinned collection jobs:** Latest jobs from pinned collections
- **New research opportunities:** Recent research positions
- **Recent jobs:** Last 10 posted jobs

### C.3 Career Radar Page (career-radar.html)

Tabbed interface showing:
- **Top Matches:** Highest-scoring jobs overall
- **Research:** Research institution matches
- **Internships:** Internship matches
- **Watchlist:** Jobs from watchlist companies
- **Remote:** Remote position matches

Each job card shows:
- Score badge with color coding
- Status label (Apply Immediately / Strong Match / Good Match)
- "Why recommended" tags
- Collection badges
- Quick actions (Save, Apply, Open)

### C.4 Analytics Page (analytics.html)

7 interactive Chart.js charts:
1. Jobs per day (line chart)
2. Jobs per company (bar chart)
3. Jobs per source (pie chart)
4. Jobs per platform (doughnut chart)
5. Jobs per location (bar chart)
6. Jobs per collection (horizontal bar)
7. Internship vs Full-time (pie chart)

### C.5 Design Principles

- **Light theme** — Clean, professional appearance
- **Responsive** — Works on desktop and tablet
- **Fast** — No framework overhead (vanilla JS)
- **Accessible** — Semantic HTML, proper contrast
- **CDN-only** — Chart.js loaded from CDN, no build step

---

## Appendix D: Retry & Error Handling

### D.1 Retry Decorator

The `retry_with_backoff` utility provides exponential backoff retry logic:

```python
def retry_with_backoff(fn, max_retries=3, initial_backoff=1.0):
    """Retry a function with exponential backoff.
    
    Backoff sequence: 1s → 2s → 4s (with initial_backoff=1.0)
    """
```

**Used by:**
- MongoDB connection (3 retries, 1s initial backoff)
- Daily scraper workflow (3 retries, 60s initial backoff)

### D.2 Scraper Error Handling

Each scraper is wrapped in try/except and returns an empty `ScrapeResult` on failure:

```python
def _run_jobspy(settings):
    try:
        return scrape_all(settings)
    except ImportError:
        return ScrapeResult(jobs=[], errors=["JobSpy not available"])
    except Exception as exc:
        return ScrapeResult(jobs=[], errors=[f"JobSpy failed: {exc}"])
```

This ensures that if one scraper fails, the others still run and their results are stored.

### D.3 Bulk Insert Error Handling

MongoDB's `insert_many(ordered=False)` is used for bulk inserts. This means:
- All documents are attempted regardless of individual failures
- Duplicate key errors (code 11000) are counted as `duplicates_skipped`
- The operation never fails entirely due to duplicates

### D.4 API Error Handling

All API endpoints wrap their logic in try/except and return appropriate HTTP status codes:
- `200 OK` — Success
- `201 Created` — Resource created
- `400 Bad Request` — Validation error
- `404 Not Found` — Resource not found
- `409 Conflict` — Duplicate resource
- `500 Internal Server Error` — Unexpected error

---

## Appendix E: Collections Definition

### E.1 Complete Collection Definitions

```python
COLLECTIONS = [
    CollectionDefinition(
        "Medical Technology",
        ["medical technology", "medtech", "medical device", "clinical engineering"]
    ),
    CollectionDefinition(
        "Biomedical Engineering",
        ["biomedical", "biomed", "bioengineering", "biomechanics"]
    ),
    CollectionDefinition(
        "Healthcare Technology",
        ["healthtech", "health tech", "healthcare technology", "digital health", "telemedicine"]
    ),
    CollectionDefinition(
        "Medical Devices",
        ["medical device", "surgical instrument", "diagnostic equipment", "implant"]
    ),
    CollectionDefinition(
        "Research Engineering",
        ["research engineer", "R&D engineer", "research scientist", "research associate"]
    ),
    CollectionDefinition(
        "Embedded Systems",
        ["embedded", "firmware", "RTOS", "microcontroller", "ARM"]
    ),
    CollectionDefinition(
        "IoT",
        ["IoT", "internet of things", "connected devices", "smart devices", "edge computing"]
    ),
    CollectionDefinition(
        "Python Development",
        ["python", "django", "flask", "fastapi", "pandas"]
    ),
    CollectionDefinition(
        "Product Management",
        ["product manager", "product owner", "product management", "product strategy"]
    ),
    CollectionDefinition(
        "Healthcare AI",
        ["healthcare AI", "medical AI", "clinical AI", "health informatics", "medical imaging AI"]
    ),
    CollectionDefinition(
        "Diagnostics and Biosensors",
        ["diagnostics", "biosensor", "biosensing", "point-of-care", "lateral flow",
         "PCR", "immunoassay", "raman", "sers", "spectroscopy", "microfluidics",
         "biomarker", "sepsis", "wearable sensor"]
    ),
]
```

### E.2 Internship Keywords

```python
INTERNSHIP_KEYWORDS = [
    "Internship", "Trainee", "Graduate Engineer", "Research Intern",
    "Project Associate", "Project Assistant", "JRF", "SRF", "RA",
    "Summer Internship", "Industrial Trainee", "Associate Engineer",
    "Graduate Trainee", "Young Professional", "Project Engineer",
]
```

### E.3 Research Institutions

```python
RESEARCH_INSTITUTIONS = [
    "IISc", "DRDO", "C-DAC", "AIIMS", "IITs", "CSIR Labs",
    "ISRO", "BARC", "THSTI", "NIBMG", "ICMR", "NIMHANS", "SCTIMST",
]
```

---

## Appendix F: Default Watchlist Companies

| # | Company | ATS Platform | Tier | Sector |
|---|---|---|---|---|
| 1 | Philips | Workday | tier3 | Medical Devices |
| 2 | GE HealthCare | Workday | tier3 | Medical Imaging |
| 3 | Siemens Healthineers | SuccessFactors | tier3 | Medical Devices |
| 4 | Medtronic | Workday | tier3 | Medical Devices |
| 5 | Abbott | Workday | tier3 | Diagnostics |
| 6 | Dozee | Lever | tier3 | HealthTech (India) |
| 7 | Niramai | Greenhouse | tier3 | AI Diagnostics (India) |
| 8 | Roche | - | tier3 | Diagnostics |
| 9 | Boston Scientific | - | tier3 | Medical Devices |
| 10 | Johnson and Johnson MedTech | - | tier3 | Medical Devices |
| 11 | Becton Dickinson | - | tier3 | Medical Devices |
| 12 | Fujifilm Healthcare | - | tier3 | Medical Imaging |
| 13 | Skanray Technologies | - | tier3 | Medical Devices (India) |

---

## Appendix G: GitHub Actions Workflows

### G.1 Daily Scraper Workflow

**File:** `.github/workflows/daily-scraper.yml`

```yaml
name: Daily Job Scraper

on:
  schedule:
    - cron: '30 2 * * *'  # 08:00 AM IST
  workflow_dispatch:       # Manual trigger

jobs:
  scrape:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - Checkout Repo (actions/checkout@v4)
      - Setup Python 3.11 (actions/setup-python@v5)
      - Install Dependencies (pip install -r requirements.txt)
      - Verify Dependencies (pyarrow, pandas, requests)
      - Test MongoDB Connection (ping)
      - Run Scraper (python daily_scraper.py)
```

**Environment variables passed:**
- `MONGODB_URI` from GitHub Secrets
- `DATABASE_NAME`: jobcopilot
- `SEARCH_TERMS`: 15 India-focused terms
- `LOCATIONS`: 11 Indian cities + Remote
- `JOB_SOURCES`: linkedin, indeed, naukri, google

### G.2 Daily Email Workflow

**File:** `.github/workflows/daily-email.yml`

**Schedule:** 5 minutes after scraper (08:05 AM IST)

Sends email summary of new jobs and career radar matches.

### G.3 Publish to PyPI Workflow

**File:** `.github/workflows/publish-to-pypi.yml`

Triggered on release creation. Builds and publishes the package.

---

## Appendix H: Performance Characteristics

### H.1 Response Times (Typical)

| Endpoint | Response Time | Notes |
|---|---|---|
| `/health` | < 50ms | No DB call |
| `/jobs` | 100-200ms | Indexed query + pagination |
| `/jobs/search` | 150-300ms | Text index search |
| `/jobs/smart-search` | 300-500ms | Regex + in-memory scoring |
| `/career-radar` | 500-1000ms | Scores all 557+ jobs |
| `/career-radar/top` | 500-800ms | Score + filter |
| `/analytics` | 200-400ms | Aggregation pipeline |
| `/stats` | 100-150ms | Count queries |
| `/daily-targets` | 600-1000ms | Career + Fresher scoring |

### H.2 Database Performance

| Operation | Performance |
|---|---|
| Bulk insert (50 jobs) | < 500ms |
| Paginated query (50 results) | < 100ms |
| Text search | < 200ms |
| Regex search | 200-500ms |
| Aggregation pipeline | 100-300ms |
| Count documents | < 50ms |

### H.3 Scraper Performance

| Scraper | Typical Duration | Jobs Found |
|---|---|---|
| JobSpy (all sources) | 5-15 minutes | 30-100 |
| JobHive (all platforms) | 2-5 minutes | 20-50 |
| Research scraper | 1-2 minutes | 5-20 |
| **Total daily run** | **10-20 minutes** | **50-150** |

### H.4 Storage Usage

| Collection | Avg Document Size | Estimated Total |
|---|---|---|
| jobs (557 docs) | ~2KB | ~1.1MB |
| scrape_history | ~200B | ~50KB |
| saved_jobs | ~500B | ~10KB |
| applied_jobs | ~500B | ~5KB |
| company_watchlist | ~100B | ~2KB |
| preferences | ~200B | ~1KB |
| **Total** | | **~1.2MB** (of 512MB limit) |

---

## Appendix I: Security Considerations

### I.1 Current Security Posture

| Aspect | Status | Notes |
|---|---|---|
| Authentication | None | Personal single-user project |
| Authorization | None | All endpoints public |
| CORS | Allow all origins | Acceptable for personal use |
| Input validation | Pydantic models | Request body validation |
| SQL injection | N/A | MongoDB (NoSQL) |
| NoSQL injection | Mitigated | Regex escaping on user input |
| Rate limiting | None | Personal use, low traffic |
| HTTPS | Yes | Render provides TLS |
| Secrets management | GitHub Secrets + Render env | Not in code |
| Dependency scanning | None | Manual updates |

### I.2 Sensitive Data

| Data | Storage | Protection |
|---|---|---|
| MongoDB URI | GitHub Secrets / Render env | Never in code |
| Telegram token | Render env vars | Never in code |
| Job data | MongoDB Atlas | Atlas encryption at rest |
| User preferences | MongoDB Atlas | No PII stored |

### I.3 Recommendations for Production Use

If this project were to be used by multiple users:
1. Add JWT authentication
2. Implement rate limiting (e.g., slowapi)
3. Restrict CORS to specific origins
4. Add API key for scraper endpoints
5. Implement user isolation (multi-tenant)
6. Add input sanitization beyond Pydantic
7. Enable MongoDB Atlas audit logging
8. Add dependency vulnerability scanning (Dependabot)

---

## Appendix J: Glossary

| Term | Definition |
|---|---|
| **ATS** | Applicant Tracking System — software companies use to manage job postings (Greenhouse, Lever, Workday, etc.) |
| **Career Radar** | The personalized scoring engine that ranks jobs by relevance to the user's profile |
| **Collection** | A named grouping of jobs defined by keyword matching (e.g., "Medical Devices") |
| **Fresher** | A recent graduate with 0-2 years of experience |
| **GET** | Graduate Engineer Trainee — common entry-level role in India |
| **JRF** | Junior Research Fellow — research position in Indian institutions |
| **JobHive** | Python library for scraping ATS platforms |
| **JobSpy** | Python library for scraping job boards (LinkedIn, Indeed, etc.) |
| **MedTech** | Medical Technology — the intersection of medicine and engineering |
| **Regional Radar** | Location-based job filtering focused on South India |
| **SERS** | Surface-Enhanced Raman Spectroscopy — the user's research area |
| **Smart Search** | Weighted multi-field search with synonym expansion |
| **SRF** | Senior Research Fellow — research position in Indian institutions |
| **Watchlist** | Companies being tracked for new job postings |

---

## Appendix K: Contact & Credits

### Project Owner
- **Name:** Sukesh Periyasamy
- **Education:** M.Tech Medical Technology, IIT Jodhpur
- **Research:** SERS-based biosensors for sepsis biomarker detection
- **GitHub:** sukesh-periyasamy

### Technologies & Libraries Credits
- [FastAPI](https://fastapi.tiangolo.com/) — Modern Python web framework
- [MongoDB Atlas](https://www.mongodb.com/atlas) — Cloud database
- [python-jobspy](https://github.com/Bunsly/JobSpy) — Job board scraper
- [jobhive-py](https://github.com/jobhive/jobhive-py) — ATS platform scraper
- [Chart.js](https://www.chartjs.org/) — JavaScript charting library
- [Hypothesis](https://hypothesis.readthedocs.io/) — Property-based testing
- [Render](https://render.com/) — Cloud hosting platform
- [GitHub Pages](https://pages.github.com/) — Static site hosting
- [GitHub Actions](https://github.com/features/actions) — CI/CD automation

---

*End of Documentation*

*Generated for JobCopilot v1.4 — Career Radar + Smart Search + Regional Radar*
