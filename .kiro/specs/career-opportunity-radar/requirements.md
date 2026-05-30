# Requirements Document

## Introduction

Career Opportunity Radar is a major upgrade from JobCopilot v1.1.0 to v1.2.0. It transforms the existing job aggregation tool into an intelligent career opportunity discovery system with automatic job collections, an opportunity feed, dedicated internship and research tracking, analytics dashboards, and enhanced Telegram intelligence summaries. The upgrade preserves all v1.1 functionality and remains within Render free-tier (single web service, single cron job, 512MB RAM) and MongoDB Atlas free-tier (512MB storage) constraints. No AI, resume matching, GPT, Claude API, or auto-apply features are introduced.

## Glossary

- **Collection_Engine**: The backend service module responsible for classifying jobs into named collections based on keyword matching against job title and description fields.
- **Opportunity_Feed_Service**: The backend service module that aggregates and returns categorized job summaries (top companies, new companies, remote jobs, internships, research roles, healthcare roles).
- **Internship_Tracker**: The backend service module that identifies and filters internship-type positions using predefined role keywords.
- **Research_Tracker**: The backend service module that identifies and filters research opportunities from specified Indian research institutions.
- **Analytics_Engine**: The backend service module that computes aggregate statistics from the jobs collection (counts by day, company, source, platform, location).
- **Dashboard_Frontend**: The static HTML/CSS/JS frontend page (analytics.html) that renders analytics charts using Chart.js.
- **Internship_Frontend**: The static HTML/CSS/JS frontend page (internships.html) that displays filtered internship listings.
- **Telegram_Intelligence_Service**: The enhanced Telegram notification module that sends daily intelligence summaries with categorized top opportunities.
- **Collection**: A named grouping of jobs defined by a set of keywords matched against job title and description fields.
- **Research_Institution**: One of the predefined Indian research organizations tracked for opportunities: IISc, DRDO, C-DAC, AIIMS, IITs, CSIR Labs, ISRO, BARC, THSTI (Translational Health Science and Technology Institute), NIBMG (National Institute of Biomedical Genomics), ICMR (Indian Council of Medical Research), NIMHANS (National Institute of Mental Health and Neurosciences), SCTIMST (Sree Chitra Tirunal Institute for Medical Sciences and Technology).
- **Internship_Keyword**: One of the predefined role identifiers used to classify internship positions: Internship, Trainee, Graduate Engineer, Research Intern, Project Associate, Project Assistant, JRF, SRF, RA, Summer Internship, Industrial Trainee, Associate Engineer, Graduate Trainee, Young Professional, Project Engineer.
- **Company_Tier**: A classification level for watchlist companies indicating priority — Tier 1 (Dream Companies), Tier 2 (Target Companies), Tier 3 (General Watchlist).
- **Personal_Dashboard**: The personalized section of the main dashboard that highlights opportunities from pinned collections and pinned companies.
- **API_Server**: The FastAPI backend application deployed on Render free-tier.

## Requirements

### Requirement 1: Collection Definition and Classification

**User Story:** As a job seeker, I want jobs automatically grouped into domain-specific collections, so that I can browse opportunities by career interest area without manual searching.

#### Acceptance Criteria

1. THE Collection_Engine SHALL maintain a predefined set of collections: Medical Technology, Biomedical Engineering, Healthcare Technology, Medical Devices, Research Engineering, Embedded Systems, IoT, Python Development, Product Management, Healthcare AI, Diagnostics and Biosensors.
2. WHEN a job record exists in the jobs collection, THE Collection_Engine SHALL classify the job into one or more collections by performing case-insensitive keyword matching against the job title and description fields.
3. THE Collection_Engine SHALL associate each collection with a defined list of keywords that determine membership.
4. WHEN a job matches keywords for multiple collections, THE Collection_Engine SHALL include the job in each matching collection.
5. THE Collection_Engine SHALL perform classification at query time without duplicating job documents in the database.

### Requirement 2: Collections API

**User Story:** As a frontend developer, I want API endpoints to retrieve collections and their jobs, so that I can build collection browsing interfaces.

#### Acceptance Criteria

1. WHEN a GET request is made to /collections, THE API_Server SHALL return a list of all collection names with the job count for each collection.
2. WHEN a GET request is made to /collections/{name} with a valid collection name, THE API_Server SHALL return the collection metadata including name, keywords, and total job count.
3. WHEN a GET request is made to /collections/{name}/jobs, THE API_Server SHALL return a paginated list of jobs belonging to the specified collection, sorted by date_posted descending.
4. WHEN a GET request is made to /collections/{name} with a collection name that does not exist, THE API_Server SHALL return an HTTP 404 response with a descriptive error message.
5. WHEN a GET request is made to /collections/{name}/jobs, THE API_Server SHALL accept optional page and page_size query parameters with defaults of 1 and 50 respectively.

### Requirement 3: Opportunity Feed

**User Story:** As a job seeker, I want a single endpoint that surfaces categorized top opportunities, so that I can quickly discover the most relevant openings across different dimensions.

#### Acceptance Criteria

1. WHEN a GET request is made to /opportunities, THE API_Server SHALL return a JSON response containing six categories: top_companies, new_companies, remote_jobs, internships, research_roles, healthcare_roles.
2. THE Opportunity_Feed_Service SHALL populate top_companies with companies that have the highest number of active job postings.
3. THE Opportunity_Feed_Service SHALL populate new_companies with companies that appeared in the jobs collection for the first time within the last 7 days.
4. THE Opportunity_Feed_Service SHALL populate remote_jobs with jobs where the location field contains the term "remote" (case-insensitive).
5. THE Opportunity_Feed_Service SHALL populate internships with jobs matching any Internship_Keyword in the title field.
6. THE Opportunity_Feed_Service SHALL populate research_roles with jobs from any Research_Institution.
7. THE Opportunity_Feed_Service SHALL populate healthcare_roles with jobs matching the Healthcare Technology or Medical Technology collection keywords.
8. THE Opportunity_Feed_Service SHALL limit each category to a maximum of 10 entries.

### Requirement 4: Internship Tracking

**User Story:** As a student or early-career professional, I want a dedicated internship section with relevant filters, so that I can find internship and trainee positions efficiently.

#### Acceptance Criteria

1. THE Internship_Tracker SHALL identify internship positions by matching any of the following keywords (case-insensitive) in the job title: Internship, Trainee, Graduate Engineer, Research Intern, Project Associate, Project Assistant, JRF, SRF, RA, Summer Internship, Industrial Trainee, Associate Engineer, Graduate Trainee, Young Professional, Project Engineer.
2. WHEN a GET request is made to /internships, THE API_Server SHALL return a paginated list of jobs matching Internship_Keywords, sorted by date_posted descending.
3. WHEN a GET request is made to /internships with a keyword query parameter, THE API_Server SHALL filter results to only those matching the specified Internship_Keyword.
4. THE Internship_Frontend SHALL display internship listings with title, company, location, date posted, and a link to the job URL.
5. THE Internship_Frontend SHALL provide a filter dropdown allowing selection of specific Internship_Keywords.
6. THE Internship_Frontend SHALL reuse the existing dark mode glassmorphism design system from the v1.1 frontend.

### Requirement 5: Research Opportunities Tracking

**User Story:** As a researcher or research-oriented professional, I want to track job openings from major Indian research institutions, so that I can discover academic and government research positions.

#### Acceptance Criteria

1. THE Research_Tracker SHALL identify research opportunities by matching any of the following institution names (case-insensitive) in the company or description fields: IISc, DRDO, C-DAC, AIIMS, IITs, CSIR Labs, ISRO, BARC, THSTI, NIBMG, ICMR, NIMHANS, SCTIMST.
2. WHEN a GET request is made to /research, THE API_Server SHALL return a paginated list of jobs from Research_Institutions, sorted by date_posted descending.
3. WHEN a GET request is made to /research/recent, THE API_Server SHALL return the 10 most recently posted research opportunities.
4. WHEN a GET request is made to /research with an institution query parameter, THE API_Server SHALL filter results to only those from the specified Research_Institution.
5. THE Collection_Engine SHALL include a "research_opportunities" collection that aggregates all jobs from Research_Institutions.

### Requirement 6: Analytics Computation

**User Story:** As a job seeker, I want to see aggregate statistics about the job market, so that I can understand hiring trends and identify where opportunities are concentrated.

#### Acceptance Criteria

1. THE Analytics_Engine SHALL compute the following metrics from the jobs collection: jobs_per_day (last 30 days), jobs_per_company (top 20), jobs_per_source (all sources), jobs_per_platform (all ATS platforms), jobs_per_location (top 20), jobs_per_collection (all collections).
2. THE Analytics_Engine SHALL compute top_hiring_companies as the 10 companies with the most job postings.
3. THE Analytics_Engine SHALL compute top_locations as the 10 locations with the most job postings.
4. THE Analytics_Engine SHALL compute top_ats_platforms as all ATS platforms ranked by job count.
5. WHEN a GET request is made to /analytics, THE API_Server SHALL return all computed analytics metrics in a single JSON response.
6. THE Analytics_Engine SHALL compute internship_vs_fulltime as the count of jobs matching Internship_Keywords versus all other jobs.
7. THE Analytics_Engine SHALL compute research_vs_industry as the count of jobs from Research_Institutions versus all other jobs.

### Requirement 7: Analytics Dashboard Frontend

**User Story:** As a job seeker, I want a visual analytics dashboard with charts, so that I can quickly grasp hiring trends and market patterns.

#### Acceptance Criteria

1. THE Dashboard_Frontend SHALL render an analytics page at analytics.html.
2. THE Dashboard_Frontend SHALL display the following charts: Jobs by Source, Jobs by ATS Platform, Jobs by Location, Jobs by Company, Internships vs Full-Time, Research vs Industry, Jobs by Collection.
3. THE Dashboard_Frontend SHALL use Chart.js loaded from a CDN for chart rendering.
4. THE Dashboard_Frontend SHALL fetch data from the /analytics API endpoint on page load.
5. THE Dashboard_Frontend SHALL reuse the existing dark mode glassmorphism design system from the v1.1 frontend.
6. THE Dashboard_Frontend SHALL display loading states while fetching analytics data.
7. IF the /analytics endpoint returns an error, THEN THE Dashboard_Frontend SHALL display a user-friendly error message.

### Requirement 8: Telegram Intelligence Summary

**User Story:** As a job seeker, I want a daily Telegram message with categorized top opportunities, so that I can stay informed about the best new openings without checking the dashboard.

#### Acceptance Criteria

1. WHEN the daily scraper completes, THE Telegram_Intelligence_Service SHALL send a daily intelligence summary message.
2. THE Telegram_Intelligence_Service SHALL include the following sections in the summary: Top 10 jobs (by recency), Top internships (up to 5), Top research openings (up to 5), Watchlist companies hiring (all matches), New ATS opportunities (up to 5).
3. THE Telegram_Intelligence_Service SHALL format the summary with section headers and job details (title, company, location, URL).
4. WHILE the Telegram bot token and chat ID are not configured, THE Telegram_Intelligence_Service SHALL skip sending the intelligence summary without raising an error.
5. IF the intelligence summary exceeds 4096 characters, THEN THE Telegram_Intelligence_Service SHALL split the message into multiple messages following the existing splitting logic.

### Requirement 9: Tiered Company Watchlist

**User Story:** As a job seeker, I want to organize my watchlist companies into priority tiers, so that I can distinguish between dream companies, target companies, and general tracking.

#### Acceptance Criteria

1. THE API_Server SHALL support a tier field on each watchlist entry with allowed values: "tier1" (Dream Companies), "tier2" (Target Companies), "tier3" (General Watchlist).
2. WHEN a company is added to the watchlist without a tier, THE API_Server SHALL default the tier to "tier3".
3. WHEN a GET request is made to /watchlist, THE API_Server SHALL include the tier field in each watchlist entry response.
4. WHEN a PATCH request is made to /watchlist/{company} with a new tier value, THE API_Server SHALL update the company tier.
5. THE API_Server SHALL include the following companies in the default watchlist seed: Philips, GE HealthCare, Siemens Healthineers, Medtronic, Abbott, Dozee, Niramai, Roche, Boston Scientific, Johnson and Johnson MedTech, Becton Dickinson, Fujifilm Healthcare, Skanray Technologies.
6. THE Telegram_Intelligence_Service SHALL prioritize Tier 1 companies in watchlist alerts by listing them first in the summary.

### Requirement 10: Backward Compatibility

**User Story:** As an existing user, I want all v1.1 features to continue working after the upgrade, so that I do not lose any existing functionality.

#### Acceptance Criteria

1. THE API_Server SHALL continue to serve all existing v1.1 endpoints with unchanged request and response formats: GET /health, GET /jobs, GET /jobs/recent, GET /jobs/search, GET /jobs/company/{name}, GET /stats, GET /watchlist, GET /watchlist/ats-info, POST /watchlist, DELETE /watchlist/{company}, POST /save-job, DELETE /save-job/{job_url}, GET /saved-jobs, POST /apply-job, PATCH /apply-job/{job_url}, GET /applied-jobs, GET /export/csv, GET /export/xlsx.
2. THE API_Server SHALL maintain backward compatibility for the existing JobRecord schema including source_type and source_platform fields.
3. THE daily scraper SHALL continue to execute the dual-scraper workflow (JobSpy + JobHive) with existing merge and deduplication logic.
4. THE API_Server SHALL preserve existing Telegram notification behavior for new jobs and watchlist alerts.

### Requirement 11: Resource Constraints

**User Story:** As a developer deploying on free-tier infrastructure, I want the system to remain within resource limits, so that the application runs reliably without paid upgrades.

#### Acceptance Criteria

1. THE API_Server SHALL operate within a single Render free-tier web service (512MB RAM).
2. THE daily scraper SHALL operate within a single Render free-tier cron job.
3. THE API_Server SHALL store all data within MongoDB Atlas free-tier storage limits (512MB).
4. THE API_Server SHALL perform analytics computations using MongoDB aggregation pipelines without caching collections or materialized views that consume additional storage.
5. THE Collection_Engine SHALL classify jobs at query time using MongoDB queries without creating separate collection documents for each job-collection mapping.
6. THE Dashboard_Frontend SHALL load Chart.js from a CDN without requiring a build step or bundler.
7. THE API_Server SHALL complete all API responses within 10 seconds to avoid Render free-tier request timeouts.

### Requirement 12: Personal Career Dashboard

**User Story:** As the primary user, I want a dashboard that highlights opportunities most relevant to my career interests, so that I can focus on high-value opportunities first.

#### Acceptance Criteria

1. THE API_Server SHALL support pinning collections via a POST request to /preferences/pinned-collections with a collection name.
2. THE API_Server SHALL support pinning companies via a POST request to /preferences/pinned-companies with a company name.
3. WHEN a GET request is made to /preferences/dashboard, THE API_Server SHALL return new jobs from pinned companies, new jobs from pinned collections, and new research opportunities from the last 7 days.
4. THE Dashboard_Frontend SHALL display pinned company jobs, pinned collection jobs, and new research opportunities in dedicated sections above all other dashboard content on the main index.html page.
5. THE API_Server SHALL store pinned preferences in a preferences collection in MongoDB.
6. THE API_Server SHALL limit pinned collections to a maximum of 5 entries.
7. THE API_Server SHALL limit pinned companies to a maximum of 10 entries.
