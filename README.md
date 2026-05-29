# JobCopilot Engine

Personal job search automation system that scrapes, stores, filters, and tracks job listings from multiple Indian job portals — running entirely on free-tier resources (₹0/month).

## Architecture

```
┌─────────────────────┐       HTTPS        ┌─────────────────────────┐
│  GitHub Pages (₹0)  │ ──────────────────► │  Render Free Tier (₹0)  │
│  Static HTML/CSS/JS │                     │  FastAPI REST API        │
└─────────────────────┘                     └────────────┬────────────┘
                                                         │
                                            ┌────────────▼────────────┐
                                            │  MongoDB Atlas Free (₹0) │
                                            │  512 MB Storage          │
                                            └────────────┬────────────┘
                                                         │
┌─────────────────────┐                     ┌────────────▼────────────┐
│  Render Cron Job    │ ──── daily 02:00 ──►│  daily_scraper.py        │
│  (08:00 IST)        │      UTC            │  Scrape → Store → Notify │
└─────────────────────┘                     └──────────────────────────┘
```

- **Frontend**: Static site on GitHub Pages — dark-mode glassmorphism UI
- **Backend**: FastAPI on Render Free — REST API with CORS
- **Database**: MongoDB Atlas Free — persistent storage with deduplication
- **Scheduler**: Render Cron Job — daily scraping at 08:00 AM IST (02:00 UTC)
- **Notifications**: Telegram Bot API — daily summaries + watchlist alerts

## Tech Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| Frontend    | HTML5, CSS3 (glassmorphism), Vanilla JS |
| Backend     | Python 3.11, FastAPI, Uvicorn       |
| Database    | MongoDB Atlas (Free Tier)           |
| Scraping    | JobSpy (LinkedIn, Indeed, Naukri, Google) |
| Hosting     | GitHub Pages + Render Free          |
| Scheduler   | Render Cron Jobs                    |
| Notifications | Telegram Bot API                  |
| Testing     | pytest, Hypothesis (property-based) |

## Features

- **Multi-source scraping** — LinkedIn, Indeed, Naukri, Google Jobs via JobSpy
- **Automatic deduplication** — unique index on job_url prevents duplicates
- **Advanced filtering** — by source, location, company, keyword, job type, date range
- **Full-text search** — search across job titles and descriptions
- **Job saving & tracking** — save interesting jobs, track application status
- **Company watchlist** — monitor specific companies for new postings
- **Telegram notifications** — daily summaries + instant watchlist alerts
- **Dashboard metrics** — total jobs, today's jobs, this week, saved, applied
- **Pagination** — configurable page size (default 50)
- **Retry with backoff** — resilient to transient failures
- **Rotating logs** — 10 MB max, 5 backups

## Local Development

### Prerequisites

- Python 3.11+
- MongoDB Atlas account (free tier) or local MongoDB
- (Optional) Telegram Bot token for notifications

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your MongoDB URI and optional Telegram credentials

# Run the API server
python main.py serve
# Server starts at http://localhost:8000

# Run a single scrape cycle
python main.py scrape
```

### Frontend Setup

```bash
cd frontend

# No build step required — just serve the static files
# Option 1: Python's built-in server
python -m http.server 8080

# Option 2: Any static file server
npx serve .
```

Open `http://localhost:8080` in your browser.

> **Note**: For local development, update `API_BASE` in `frontend/js/api.js` to `http://localhost:8000` and add `http://localhost:8080` to the CORS origins in `backend/main.py`.

## Deployment

### Render (Backend + Cron Job)

1. **Create a Render account** at [render.com](https://render.com)
2. **Connect your GitHub repo** to Render
3. **Create a Web Service**:
   - Name: `jobcopilot-api`
   - Root Directory: `backend`
   - Runtime: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. **Create a Cron Job**:
   - Name: `daily-scraper`
   - Root Directory: `backend`
   - Runtime: Python
   - Build Command: `pip install -r requirements.txt`
   - Command: `python daily_scraper.py`
   - Schedule: `0 2 * * *` (02:00 UTC = ~08:00 IST)
5. **Set environment variables** in the Render dashboard (see below)

Alternatively, use the `backend/render.yaml` Blueprint for one-click setup.

### GitHub Pages (Frontend)

1. Push the repository to GitHub
2. Go to **Settings → Pages**
3. Set source to the `main` branch, folder `/frontend`
4. Your site will be live at `https://<username>.github.io/<repo-name>/`

### MongoDB Atlas

1. Create a free cluster at [mongodb.com/atlas](https://www.mongodb.com/atlas)
2. Create a database user with read/write access
3. Whitelist `0.0.0.0/0` for Render access (or use Render's static IPs)
4. Copy the connection string to use as `MONGODB_URI`

## Environment Variables

| Variable             | Required | Default | Description |
|----------------------|----------|---------|-------------|
| `MONGODB_URI`        | Yes      | —       | MongoDB Atlas connection string |
| `DATABASE_NAME`      | No       | `jobcopilot` | MongoDB database name |
| `TELEGRAM_BOT_TOKEN` | No       | —       | Telegram Bot API token (from @BotFather) |
| `TELEGRAM_CHAT_ID`   | No       | —       | Telegram chat ID for notifications |
| `SEARCH_TERMS`       | No       | See below | Comma-separated job search terms |
| `LOCATIONS`          | No       | See below | Comma-separated locations |
| `JOB_SOURCES`        | No       | `linkedin,indeed,naukri,google` | Comma-separated sources |
| `SCHEDULE_TIME`      | No       | `08:00` | Daily scrape time (HH:MM, 24-hour) |

**Default search terms**: Biomedical Engineer, Medical Device Engineer, Research Engineer, Research Associate, Healthcare Technology, Healthcare AI, Signal Processing Engineer, Embedded Systems Engineer, IoT Engineer, Python Developer, Backend Developer, R&D Engineer, Clinical Data Analyst, Biomedical Research, Medical Technology, Research Scientist

**Default locations**: India, Remote, Bangalore, Hyderabad, Chennai, Pune, Mumbai, Delhi, Noida, Gurugram, Ahmedabad, Kolkata

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check → `{"status": "ok"}` |
| GET | `/jobs` | Paginated jobs with filters (page, page_size, source, location, company, keyword, job_type, date_from, date_to, search_term) |
| GET | `/jobs/recent` | Top 10 most recently posted jobs |
| GET | `/jobs/search?q=` | Full-text search across title and description |
| GET | `/jobs/company/{name}` | Jobs from a specific company |
| GET | `/stats` | Dashboard summary metrics |
| GET | `/watchlist` | List all watchlist companies |
| POST | `/watchlist` | Add company to watchlist |
| DELETE | `/watchlist/{company}` | Remove company from watchlist |
| POST | `/save-job` | Save a job |
| DELETE | `/save-job/{job_url}` | Remove from saved jobs |
| GET | `/saved-jobs` | List all saved jobs |
| POST | `/apply-job` | Mark job as applied |
| PATCH | `/apply-job/{job_url}` | Update application status |
| GET | `/applied-jobs` | List all applied jobs |

## Project Structure

```
jobcopilot/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI route handlers
│   │   │   ├── health.py
│   │   │   ├── jobs.py
│   │   │   ├── watchlist.py
│   │   │   ├── saved.py
│   │   │   ├── applied.py
│   │   │   └── stats.py
│   │   ├── config/         # Settings loader (python-dotenv)
│   │   ├── database/       # MongoDB connection + repository
│   │   ├── models/         # Dataclasses + Pydantic schemas
│   │   ├── scraper/        # JobSpy wrapper + normalization
│   │   ├── services/       # Filter engine + Telegram notifier
│   │   └── utils/          # Logger + retry utility
│   ├── tests/              # pytest + Hypothesis property tests
│   ├── daily_scraper.py    # Render Cron Job entry point
│   ├── main.py             # FastAPI app + CLI
│   ├── render.yaml         # Render Blueprint config
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html          # Dashboard
│   ├── jobs.html           # Jobs feed
│   ├── saved.html          # Saved jobs
│   ├── watchlist.html      # Company watchlist
│   ├── settings.html       # Settings
│   ├── css/style.css       # Dark mode glassmorphism
│   ├── js/
│   │   ├── api.js          # API abstraction layer
│   │   ├── dashboard.js
│   │   ├── jobs.js
│   │   ├── saved.js
│   │   ├── watchlist.js
│   │   ├── settings.js
│   │   └── components.js   # Reusable UI components
│   └── assets/
├── .gitignore
└── README.md
```

## Cost Breakdown

| Service | Tier | Monthly Cost |
|---------|------|--------------|
| GitHub Pages | Free | ₹0 |
| Render Web Service | Free (750 hrs/month) | ₹0 |
| Render Cron Job | Free (included) | ₹0 |
| MongoDB Atlas | Free (512 MB) | ₹0 |
| Telegram Bot API | Free | ₹0 |
| **Total** | | **₹0/month** |

> Free tier limitations: Render web services sleep after 15 minutes of inactivity (cold start ~30s on first request). MongoDB Atlas free tier limited to 512 MB storage. These are acceptable for personal use.

## License

MIT
