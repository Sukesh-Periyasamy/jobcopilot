# Requirements Document

## Introduction

JobCopilot Engine v1.1 is an upgrade to the existing v1.0 personal job search automation system. The upgrade adds a second scraping source (JobHive via jobhive-py) alongside the existing JobSpy integration, introduces enhanced source metadata tracking, ATS-based filtering, job export capabilities (CSV/XLSX), and a company tracker with ATS platform information. The system continues to run on free-tier resources (Render Free, MongoDB Atlas Free 512MB, GitHub Pages) with no AI/ML features. The upgrade is backward compatible with all existing v1.0 data and APIs.

## Glossary

- **JobHive_Scraper**: The module responsible for querying ATS platforms (Greenhouse, Lever, Ashby, Workday, SuccessFactors) via the jobhive-py library to collect job listings
- **JobSpy_Scraper**: The existing module that queries job boards (LinkedIn, Indeed, Naukri, Google) via the JobSpy library
- **Scrape_Orchestrator**: The daily scraper workflow that coordinates both JobSpy_Scraper and JobHive_Scraper, merges results, and stores them in MongoDB
- **Job_Record**: A normalized data object representing a single job listing stored in MongoDB, extended with source_type and source_platform fields
- **Source_Type**: A classification field indicating the scraping library used to collect a job: "jobspy" or "jobhive"
- **Source_Platform**: A specific platform identifier indicating where a job was sourced from: linkedin, indeed, naukri, google, workday, greenhouse, lever, ashby, or successfactors
- **ATS**: Applicant Tracking System — enterprise software used by companies to manage job postings and applications (e.g., Greenhouse, Lever, Workday)
- **Export_Service**: The module responsible for generating downloadable CSV and XLSX files from filtered job data
- **Company_Tracker**: An extension of the existing watchlist that stores ATS platform information for tracked companies
- **Filter_Engine**: The existing query builder module, extended to support source_type and source_platform filtering
- **Jobs_Repository**: The existing data access layer, extended with new indexes and export query support

## Requirements

### Requirement 1: JobHive Scraper Integration

**User Story:** As a job seeker, I want the system to scrape jobs from ATS platforms (Greenhouse, Lever, Ashby, Workday, SuccessFactors) using jobhive-py, so that I can discover jobs posted directly on company career pages that are not listed on traditional job boards.

#### Acceptance Criteria

1. WHEN a scrape cycle is triggered, THE JobHive_Scraper SHALL query the jobhive-py library for job listings from the following ATS platforms: Greenhouse, Lever, Ashby, Workday, and SuccessFactors
2. WHEN jobhive-py returns job results, THE JobHive_Scraper SHALL normalize each result into a Job_Record containing: title (string), company (string), location (string), source (string matching the ATS platform name), job_url (string), description (string), job_type (string or empty), salary (string or empty), date_posted (string in YYYY-MM-DD format or empty), search_term (string), source_type ("jobhive"), source_platform (one of: greenhouse, lever, ashby, workday, successfactors), created_at (ISO 8601), updated_at (ISO 8601)
3. IF jobhive-py returns a result with missing optional fields (description, job_type, salary, date_posted), THEN THE JobHive_Scraper SHALL set those fields to an empty string in the Job_Record
4. IF jobhive-py fails for a specific ATS platform, THEN THE JobHive_Scraper SHALL log the error with the platform name and error message and continue processing remaining platforms without discarding already-collected results
5. IF all configured ATS platforms return zero results, THEN THE JobHive_Scraper SHALL return an empty result set without raising an error
6. THE JobHive_Scraper SHALL be implemented in the file backend/app/scraper/jobhive_scraper.py

### Requirement 2: Scrape Workflow Merge

**User Story:** As a job seeker, I want JobHive results merged with JobSpy results in the daily scrape workflow, so that I receive a unified view of jobs from all sources.

#### Acceptance Criteria

1. WHEN the daily scrape cycle executes, THE Scrape_Orchestrator SHALL invoke both the JobSpy_Scraper and the JobHive_Scraper sequentially
2. WHEN both scrapers complete, THE Scrape_Orchestrator SHALL merge the results from JobSpy_Scraper and JobHive_Scraper into a single list of Job_Records before performing bulk insert
3. THE Scrape_Orchestrator SHALL preserve deduplication using the existing unique index on job_url, ensuring that duplicate jobs from different scrapers are skipped
4. WHEN recording scrape history, THE Scrape_Orchestrator SHALL include the combined job count and errors from both scrapers in a single scrape_history entry
5. IF the JobHive_Scraper fails entirely while the JobSpy_Scraper succeeds, THEN THE Scrape_Orchestrator SHALL proceed with storing and notifying based on JobSpy results alone, logging the JobHive failure
6. IF the JobSpy_Scraper fails entirely while the JobHive_Scraper succeeds, THEN THE Scrape_Orchestrator SHALL proceed with storing and notifying based on JobHive results alone, logging the JobSpy failure

### Requirement 3: Source Metadata Fields

**User Story:** As a job seeker, I want each job record to indicate which scraping source and platform it came from, so that I can identify and filter jobs by their origin.

#### Acceptance Criteria

1. THE Job_Record SHALL include a source_type field accepting values: "jobspy" or "jobhive"
2. THE Job_Record SHALL include a source_platform field accepting values: linkedin, indeed, naukri, google, workday, greenhouse, lever, ashby, or successfactors
3. WHEN the JobSpy_Scraper normalizes a job, THE JobSpy_Scraper SHALL set source_type to "jobspy" and source_platform to the lowercase site name returned by JobSpy (linkedin, indeed, naukri, or google)
4. WHEN the JobHive_Scraper normalizes a job, THE JobHive_Scraper SHALL set source_type to "jobhive" and source_platform to the lowercase ATS platform name (greenhouse, lever, ashby, workday, or successfactors)
5. WHEN the Jobs_Repository reads an existing Job_Record that lacks source_type or source_platform fields, THE Jobs_Repository SHALL treat the missing source_type as "jobspy" and derive source_platform from the existing source field for backward compatibility
6. THE Jobs_Repository SHALL NOT require a data migration for existing records; backward compatibility SHALL be handled at read time

### Requirement 4: ATS Source Filtering

**User Story:** As a job seeker, I want to filter jobs by ATS source type and specific platform, so that I can focus on jobs from particular sources or platforms.

#### Acceptance Criteria

1. WHEN a filter request includes a source_type criterion, THE Filter_Engine SHALL return only Job_Records where the source_type field matches the specified value using case-insensitive exact match
2. WHEN a filter request includes a source_platform criterion, THE Filter_Engine SHALL return only Job_Records where the source_platform field matches the specified value using case-insensitive exact match
3. WHEN a filter request includes source_platform set to "ats", THE Filter_Engine SHALL return Job_Records where source_platform is one of: greenhouse, lever, ashby, workday, or successfactors
4. WHEN source_type and source_platform filters are combined with existing filters (location, company, keyword, job_type, date range), THE Filter_Engine SHALL apply all criteria using AND logic
5. THE GET /jobs endpoint SHALL accept optional query parameters: source_type (string) and source_platform (string), in addition to all existing filter parameters
6. THE existing source filter parameter SHALL continue to function as before for backward compatibility

### Requirement 5: Job Export API

**User Story:** As a job seeker, I want to export filtered job listings as CSV or Excel files, so that I can analyze jobs offline or share them with others.

#### Acceptance Criteria

1. WHEN a GET request is made to /export/csv with filter parameters, THE Export_Service SHALL return a downloadable CSV file containing all jobs matching the specified filters
2. WHEN a GET request is made to /export/xlsx with filter parameters, THE Export_Service SHALL return a downloadable Excel file containing all jobs matching the specified filters
3. THE export endpoints SHALL support all existing filter parameters (source, location, company, keyword, job_type, date_from, date_to, search_term) plus the new source_type and source_platform parameters
4. THE exported file SHALL include the following columns: title, company, location, source, source_type, source_platform, job_url, description, job_type, salary, date_posted, search_term, created_at
5. WHEN the filter criteria match zero jobs, THE Export_Service SHALL return an empty file with only the header row
6. THE Export_Service SHALL set appropriate HTTP response headers: Content-Type (text/csv or application/vnd.openxmlformats-officedocument.spreadsheetml.sheet) and Content-Disposition with a filename including the current date
7. IF the export query exceeds 10000 records, THEN THE Export_Service SHALL limit the export to 10000 records and include a warning header indicating truncation

### Requirement 6: Company Tracker with ATS Information

**User Story:** As a job seeker, I want to track specific companies and see which ATS platform each company uses, so that I can monitor career pages of target companies directly.

#### Acceptance Criteria

1. THE Company_Tracker SHALL store ATS platform information for each tracked company as an optional field (ats_platform) in the company_watchlist collection
2. THE Company_Tracker SHALL support the following default tracked companies with their ATS platforms: Philips (workday), GE HealthCare (workday), Siemens Healthineers (successfactors), Medtronic (workday), Abbott (workday), Dozee (lever), Niramai (greenhouse)
3. WHEN a GET request is made to /watchlist, THE API SHALL return each company entry with its company_name and ats_platform fields
4. WHEN a POST request is made to /watchlist with a company_name and optional ats_platform, THE Company_Tracker SHALL store both fields in the company_watchlist collection
5. THE Company_Tracker SHALL provide a GET /watchlist/ats-info endpoint that returns all tracked companies grouped by their ATS platform
6. WHEN a company in the watchlist has no ats_platform value, THE Company_Tracker SHALL return ats_platform as null for that entry
7. THE existing watchlist validation rules SHALL remain: maximum 50 companies, maximum 100 characters per company name

### Requirement 7: Database Index Updates

**User Story:** As a system operator, I want database indexes optimized for the new source metadata fields, so that filtering by source_type and source_platform performs efficiently.

#### Acceptance Criteria

1. WHEN the application starts, THE Jobs_Repository SHALL create an index on the source_type field in the jobs collection if it does not already exist
2. WHEN the application starts, THE Jobs_Repository SHALL create an index on the source_platform field in the jobs collection if it does not already exist
3. THE Jobs_Repository SHALL maintain all existing indexes (job_url unique, date_posted, source, company, text index on title and description) without modification
4. THE total index count SHALL remain within MongoDB Atlas free-tier limits (no more than 64 indexes per collection)
5. THE Jobs_Repository SHALL NOT perform any data migration on existing documents; new fields are added only to newly inserted records

### Requirement 8: Frontend ATS Source Badges

**User Story:** As a job seeker, I want to see color-coded badges indicating the source platform of each job in the jobs feed, so that I can quickly identify where each job was sourced from.

#### Acceptance Criteria

1. WHEN a job card is rendered in the jobs feed, THE Frontend SHALL display a source badge indicating the source_platform value
2. THE Frontend SHALL use distinct colors for each source platform: LinkedIn (blue), Indeed (purple), Naukri (red), Google (green), Workday (orange), Greenhouse (teal), Lever (indigo), Ashby (pink), SuccessFactors (amber)
3. WHEN a job record lacks a source_platform field, THE Frontend SHALL derive the badge from the existing source field for backward compatibility
4. THE source badges SHALL be rendered as pill-shaped elements consistent with the existing glassmorphism design system

### Requirement 9: Frontend Export Controls

**User Story:** As a job seeker, I want export buttons on the jobs feed page, so that I can download filtered results as CSV or Excel with one click.

#### Acceptance Criteria

1. THE Frontend SHALL display two export buttons (CSV and XLSX) on the jobs feed page, positioned near the filter controls
2. WHEN the user clicks the CSV export button, THE Frontend SHALL make a GET request to /export/csv with the currently active filter parameters and trigger a file download
3. WHEN the user clicks the XLSX export button, THE Frontend SHALL make a GET request to /export/xlsx with the currently active filter parameters and trigger a file download
4. WHILE an export request is in progress, THE Frontend SHALL display a loading indicator on the clicked export button and disable both export buttons
5. IF the export request fails, THEN THE Frontend SHALL display a toast notification with the error message and re-enable the export buttons

### Requirement 10: Frontend Company Tracker Page

**User Story:** As a job seeker, I want a company tracker page showing ATS information for each tracked company, so that I can see which career platforms my target companies use.

#### Acceptance Criteria

1. THE Frontend SHALL provide a company tracker view accessible from the existing watchlist page or as an enhanced section within it
2. THE Frontend SHALL display each tracked company with its name and ATS platform badge (color-coded matching the source badge colors)
3. WHEN a company has no ATS platform information, THE Frontend SHALL display "Unknown" as the platform indicator
4. THE Frontend SHALL allow adding new companies with an optional ATS platform selection dropdown containing: Workday, Greenhouse, Lever, Ashby, SuccessFactors, or None
5. THE Frontend SHALL maintain the existing watchlist add/remove functionality without modification

### Requirement 11: Frontend Filter Updates

**User Story:** As a job seeker, I want the filter dropdowns on the jobs feed page to include new ATS source options, so that I can filter jobs by specific ATS platforms.

#### Acceptance Criteria

1. THE Frontend SHALL update the source filter dropdown to include the following options: All Sources, LinkedIn Jobs, Indeed Jobs, Naukri Jobs, Google Jobs, ATS Jobs (umbrella), Workday Jobs, Greenhouse Jobs, Lever Jobs, Ashby Jobs, SuccessFactors Jobs
2. WHEN the user selects "ATS Jobs", THE Frontend SHALL pass source_platform=ats as the filter parameter to the API
3. WHEN the user selects a specific ATS platform (e.g., "Workday Jobs"), THE Frontend SHALL pass source_platform with the corresponding platform value (e.g., workday) to the API
4. WHEN the user selects a traditional source (e.g., "LinkedIn Jobs"), THE Frontend SHALL pass source_platform with the corresponding value (e.g., linkedin) to the API
5. THE Frontend SHALL preserve all existing filter functionality (location, company, keyword, job_type, date range) without modification

### Requirement 12: Free-Tier Compatibility

**User Story:** As a system operator, I want the v1.1 upgrade to remain within free-tier resource limits, so that the system continues to operate at zero cost.

#### Acceptance Criteria

1. THE system SHALL remain compatible with Render Free tier constraints: single web service, single cron job, 512MB RAM, services sleep after 15 minutes of inactivity
2. THE system SHALL remain compatible with MongoDB Atlas Free tier constraints: 512MB storage, shared cluster, limited connections
3. THE Export_Service SHALL generate files in-memory without writing to disk, to remain compatible with Render ephemeral filesystem
4. THE JobHive_Scraper SHALL execute within the Render Cron Job timeout limits (maximum 15 minutes total scrape cycle including both scrapers)
5. THE system SHALL NOT add any new paid dependencies or services

