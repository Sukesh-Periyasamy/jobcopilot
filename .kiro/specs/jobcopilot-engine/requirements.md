# Requirements Document

## Introduction

JobCopilot is a personal job search engine that automatically collects, stores, filters, and tracks jobs from multiple sources across India. It helps users discover internships and jobs without manually searching job portals every day. The system uses JobSpy for scraping, MongoDB Atlas for storage, Streamlit for the dashboard, Telegram Bot API for notifications, and APScheduler for automated daily runs. No AI matching, no resume analysis, no LLM integration. Completely functional using free resources only.

## Glossary

- **Scraper**: The module responsible for querying JobSpy with configured search terms and locations to collect job listings
- **Jobs_Repository**: The data access layer that handles all MongoDB CRUD operations for job records
- **Dashboard**: The Streamlit web application providing visual access to job data, saved jobs, applied jobs, and company watchlist
- **Scheduler**: The APScheduler-based module that triggers automated daily scraping at a configured time
- **Notifier**: The Telegram Bot API integration that sends daily job summaries and watchlist alerts to the user
- **Filter_Engine**: The module that applies user-defined filters (source, location, company, keyword, job type, date, search term) to job listings
- **Job_Record**: A normalized data object representing a single job listing stored in MongoDB
- **Watchlist**: A collection of company names the user wants to monitor for new job postings
- **Scrape_History**: A log of each scraping run including timestamp, jobs found, duplicates skipped, and errors

## Requirements

### Requirement 1: Job Scraping via JobSpy

**User Story:** As a job seeker, I want the system to automatically scrape jobs from multiple sources using configurable search terms and locations, so that I receive a comprehensive list of relevant opportunities without manual searching.

#### Acceptance Criteria

1. WHEN a scrape cycle is triggered, THE Scraper SHALL query JobSpy for each configured search term and each configured location combination across all configured job sources (LinkedIn, Indeed, Naukri, Google Jobs), requesting up to 15 results per source per search term per location
2. THE Scraper SHALL support configurable search terms via a Python settings file that can be modified without changes to scraper logic
3. THE Scraper SHALL support configurable job sources via a Python settings file that can be modified without changes to scraper logic, accepting values from the set: linkedin, indeed, naukri, google
4. THE Scraper SHALL support configurable locations via a Python settings file that can be modified without changes to scraper logic
5. WHEN JobSpy returns job results, THE Scraper SHALL normalize each job into a Job_Record containing: title (string), company (string), location (string), source (string identifying the job board), job_url (string), description (string), job_type (string), salary (string representation of compensation range and interval, or empty string if unavailable), date_posted (date string in YYYY-MM-DD format or empty string if unavailable), created_at (ISO 8601 timestamp of record creation), updated_at (ISO 8601 timestamp of last modification)
6. IF a job source returns a result with missing optional fields (description, job_type, salary, date_posted), THEN THE Scraper SHALL set those fields to an empty string in the Job_Record
7. IF a job source fails to respond or raises an error for a given search term and location combination, THEN THE Scraper SHALL log the error with the source name, search term, and location, and continue processing remaining combinations without discarding already-collected results
8. IF all configured job sources return zero results for all search term and location combinations, THEN THE Scraper SHALL return an empty result set without raising an error

### Requirement 2: MongoDB Storage and Deduplication

**User Story:** As a job seeker, I want scraped jobs stored persistently with automatic deduplication, so that I have a clean, non-redundant database of job opportunities.

#### Acceptance Criteria

1. WHEN normalized Job_Records are produced, THE Jobs_Repository SHALL insert them into the MongoDB "jobs" collection using bulk insert operations, processing all records from a single scrape cycle in one operation
2. THE Jobs_Repository SHALL maintain a unique index on the job_url field in the "jobs" collection
3. WHEN a Job_Record with a duplicate job_url is inserted, THE Jobs_Repository SHALL skip the duplicate without raising an error and SHALL increment the duplicates_skipped counter for the current scrape run
4. IF a Job_Record has a null or empty job_url, THEN THE Jobs_Repository SHALL skip that record without inserting it and SHALL count it as an error in the scrape_history
5. THE Jobs_Repository SHALL maintain the following collections: jobs, saved_jobs, applied_jobs, company_watchlist, scrape_history
6. WHEN the application starts, THE Jobs_Repository SHALL create indexes if they do not already exist on the following fields: job_url (unique) on the jobs collection, date_posted on the jobs collection, source on the jobs collection, and company on the jobs collection
7. WHEN a scrape cycle completes, THE Jobs_Repository SHALL record the scrape run in the scrape_history collection with the following fields: timestamp (UTC ISO 8601 format), jobs_found (integer count of total records received), duplicates_skipped (integer count of records skipped due to duplicate job_url), and errors (list of strings, each describing a single failure encountered during the insert operation)

### Requirement 3: Job Filtering

**User Story:** As a job seeker, I want to filter jobs by multiple criteria, so that I can quickly find the most relevant opportunities.

#### Acceptance Criteria

1. WHEN a filter request is submitted with a source criterion, THE Filter_Engine SHALL return only Job_Listings where the site field matches one of the specified sources (linkedin, indeed, naukri, google) using case-insensitive exact match
2. WHEN a filter request is submitted with a location criterion, THE Filter_Engine SHALL return only Job_Listings where the location field contains the specified location string as a case-insensitive substring
3. WHEN a filter request is submitted with a company name criterion, THE Filter_Engine SHALL return only Job_Listings where the company field contains the specified company name as a case-insensitive substring
4. WHEN a filter request is submitted with a keyword criterion, THE Filter_Engine SHALL return only Job_Listings where the title or description field contains the specified keyword as a case-insensitive substring, supporting keywords between 1 and 200 characters in length
5. WHEN a filter request is submitted with a job type criterion, THE Filter_Engine SHALL return only Job_Listings where the job_type field matches one of the specified values (full-time, part-time, internship, contract) using case-insensitive exact match
6. WHEN a filter request is submitted with a date posted range criterion specifying a start date and/or end date in YYYY-MM-DD format, THE Filter_Engine SHALL return only Job_Listings where the date_posted field falls within the specified inclusive date range
7. WHEN a filter request is submitted with a search term criterion, THE Filter_Engine SHALL return only Job_Listings where the search_term field used during scraping matches the specified value as a case-insensitive exact match
8. WHEN multiple filters are applied simultaneously, THE Filter_Engine SHALL return only Job_Listings matching all specified criteria using AND logic
9. IF all applied filters result in zero matching Job_Listings, THEN THE Filter_Engine SHALL return an empty result set without raising an error
10. IF a filter criterion contains an empty or null value, THEN THE Filter_Engine SHALL ignore that criterion and not apply it to the filtering logic

### Requirement 4: Streamlit Dashboard

**User Story:** As a job seeker, I want a web dashboard to browse, save, and track jobs visually, so that I can manage my job search from a single interface.

#### Acceptance Criteria

1. THE Dashboard SHALL display a main page with summary metrics: Total Jobs, Jobs Today (posted within the current calendar day in local system time), Jobs This Week (posted within the current Monday-to-Sunday calendar week), Saved Jobs count, Applied Jobs count, Companies Tracked count
2. THE Dashboard SHALL display a Recent Jobs section on the main page showing the 10 most recently posted job listings, ordered by date posted descending
3. THE Dashboard SHALL provide an "All Jobs" page with a paginated table showing columns: Title, Company, Location, Source, Date Posted, Apply Button, Save Button
4. WHEN the user clicks an Apply button, THE Dashboard SHALL open the job_url in a new browser tab
5. WHEN the user clicks a Save button for a job not already in the "saved_jobs" collection, THE Dashboard SHALL store the job in the "saved_jobs" MongoDB collection and display a confirmation indicator
6. IF the user clicks a Save button for a job that already exists in the "saved_jobs" collection (matched by job_url), THEN THE Dashboard SHALL display a message indicating the job is already saved and shall not create a duplicate entry
7. THE Dashboard SHALL provide a "Saved Jobs" page listing all bookmarked jobs from the saved_jobs collection, displaying Title, Company, Location, Date Saved, and a Remove button
8. THE Dashboard SHALL provide an "Applied Jobs" page with status tracking using statuses: Interested, Applied, Assessment, Interview, Offer, Rejected, Joined, where new entries default to "Interested" status
9. WHEN the user updates an application status, THE Dashboard SHALL persist the new status in the "applied_jobs" collection
10. THE Dashboard SHALL provide a "Company Watchlist" page allowing users to add and remove company names, with each company name limited to 100 characters and a maximum of 50 companies in the watchlist
11. THE Dashboard SHALL provide a "Settings" page for configuring search terms, locations, sources, and schedule time, persisting all settings in a "settings" MongoDB collection
12. WHEN the jobs table exceeds 50 rows, THE Dashboard SHALL paginate the results displaying 50 rows per page with navigation controls to move between pages
13. IF the MongoDB connection is unavailable, THEN THE Dashboard SHALL display an error message indicating the database is unreachable and disable data-modification actions until the connection is restored

### Requirement 5: Telegram Notifications

**User Story:** As a job seeker, I want to receive daily Telegram notifications with new job listings, so that I stay informed without opening the dashboard.

#### Acceptance Criteria

1. WHEN a scrape cycle completes and new jobs are found that have not been previously notified, THE Notifier SHALL send a summary message via Telegram Bot API containing the count of new jobs found and the formatted job details
2. THE Notifier SHALL format each job entry in the notification with: job title, company name, location, and apply URL, and SHALL split messages into multiple Telegram messages if the content exceeds 4096 characters per message
3. THE Notifier SHALL track which jobs have been previously notified and SHALL only include jobs in a notification that have not appeared in any prior notification
4. WHEN a job is found whose company name matches an entry in the Watchlist (a user-configured list of company names stored in the application configuration), THE Notifier SHALL send a separate alert for that job within the same scrape cycle, independent of the daily summary
5. IF the Telegram Bot Token or Chat ID is not configured as environment variables, THEN THE Notifier SHALL log a warning message indicating which value is missing and skip all notification sending without raising an unhandled exception
6. IF a scrape cycle completes with zero new un-notified jobs, THEN THE Notifier SHALL not send any Telegram message for that cycle
7. IF the Telegram Bot API request fails due to a network error or invalid credentials, THEN THE Notifier SHALL log an error message indicating the failure reason and continue execution without raising an unhandled exception

### Requirement 6: Scheduled Automation

**User Story:** As a job seeker, I want the system to run automatically every day at a configured time, so that fresh jobs are collected without manual intervention.

#### Acceptance Criteria

1. THE Scheduler SHALL execute the full scrape-store-notify workflow daily at 08:00 local system time by default
2. THE Scheduler SHALL support configurable schedule time via a settings variable accepting values in HH:MM 24-hour format within the range 00:00 to 23:59
3. WHEN the scheduled job triggers, THE Scheduler SHALL execute the workflow in order: Scrape Jobs for all configured Search_Terms, Store results in MongoDB, Deduplicate by job_url, Notify via Telegram, Update Dashboard data
4. IF a scheduled run fails due to an unhandled exception during any workflow step, THEN THE Scheduler SHALL log the failure with a timestamp and error description, and retry the full workflow up to 3 times with exponential backoff starting at 60 seconds and doubling each attempt
5. IF all 3 retry attempts fail, THEN THE Scheduler SHALL log a final failure message indicating the number of attempts exhausted and the last error encountered, and wait for the next scheduled execution
6. THE Scheduler SHALL allow manual triggering of the scrape workflow via command-line invocation outside the scheduled time, executing the same workflow as the scheduled run

### Requirement 7: Error Handling and Resilience

**User Story:** As a job seeker, I want the system to handle failures gracefully, so that partial failures do not prevent the rest of the workflow from completing.

#### Acceptance Criteria

1. IF JobSpy fails for a specific source, THEN THE Scraper SHALL log the error with the source name and error message and continue scraping remaining sources without discarding already-collected results
2. IF the MongoDB connection fails, THEN THE Jobs_Repository SHALL retry the connection up to 3 times with exponential backoff (starting at 1 second, doubling each attempt) before raising an error
3. IF the Telegram API call fails, THEN THE Notifier SHALL retry up to 3 times with exponential backoff and log the failure without stopping the workflow
4. IF a search term returns empty results, THEN THE Scraper SHALL log the empty result with the search term name and proceed to the next search term
5. IF job data contains missing required fields (title or job_url), THEN THE Scraper SHALL log the invalid record details and skip it without stopping the batch

### Requirement 8: Logging and Observability

**User Story:** As a system operator, I want comprehensive rotating logs, so that I can monitor system health and debug issues.

#### Acceptance Criteria

1. WHEN a scrape cycle completes for a search term, THE Scraper SHALL log an entry containing the search term, each job source queried, and the count of jobs returned per source
2. THE Jobs_Repository SHALL log the count of new jobs inserted and duplicates skipped after each storage operation
3. THE Notifier SHALL log the count of notifications sent and any delivery failures
4. THE Scheduler SHALL log the start time, end time, and outcome of each scheduled run in ISO 8601 format
5. WHEN log files exceed 10 MB, THE Logger SHALL rotate logs and retain the last 5 rotated files
6. THE Logger SHALL write logs to both console output and a file named `jobcopilot.log` in the `data/` directory
7. THE Logger SHALL format each log entry with a timestamp in ISO 8601 format, a log level (DEBUG, INFO, WARNING, or ERROR), the module name, and the message text

### Requirement 9: Configuration Management

**User Story:** As a user, I want all configurable values managed through environment variables and a settings module, so that I can adjust behavior without modifying code.

#### Acceptance Criteria

1. THE Settings module SHALL load configuration from a .env file using python-dotenv, falling back to system environment variables for any value not present in the .env file
2. IF the .env file does not exist, THEN THE Settings module SHALL load all configuration values from system environment variables without raising an error
3. THE Settings module SHALL expose the following configuration: MONGODB_URI (string), DATABASE_NAME (string, default "jobcopilot"), TELEGRAM_BOT_TOKEN (string), TELEGRAM_CHAT_ID (string), search terms list (comma-separated string parsed into a list), locations list (comma-separated string parsed into a list), job sources list (comma-separated string parsed into a list), schedule time (string in HH:MM 24-hour format, default "08:00")
4. THE Settings module SHALL provide default values when not explicitly configured: search terms defaults to "Biomedical Engineer,Medical Device Engineer,Research Engineer,Research Associate,Healthcare Technology,Healthcare AI,Signal Processing Engineer,Embedded Systems Engineer,IoT Engineer,Python Developer,Backend Developer,R&D Engineer,Clinical Data Analyst,Biomedical Research,Medical Technology,Research Scientist"; locations defaults to "India,Remote,Bangalore,Hyderabad,Chennai,Pune,Mumbai,Delhi,Noida,Gurugram,Ahmedabad,Kolkata"; job sources defaults to "linkedin,indeed,naukri,google"
5. IF the required environment variable MONGODB_URI is missing, THEN THE Settings module SHALL raise a descriptive error at startup indicating the variable name
6. IF the schedule time value does not match the HH:MM 24-hour format (00:00 to 23:59), THEN THE Settings module SHALL raise an error at startup indicating the invalid value

### Requirement 10: Performance and Scalability

**User Story:** As a job seeker, I want the system to handle large volumes of jobs efficiently, so that daily scraping of 1000+ jobs completes in a reasonable time.

#### Acceptance Criteria

1. THE Jobs_Repository SHALL use MongoDB indexes on job_url (unique), date_posted, source, and company fields to support efficient queries
2. THE Scraper SHALL process multiple search terms concurrently using thread-based parallelism with a maximum of 4 concurrent threads
3. WHEN the Dashboard loads job data, THE Dashboard SHALL use pagination with a configurable page size (default 50 records per page)
4. THE Jobs_Repository SHALL support bulk insert operations using ordered=False to minimize round-trips when storing multiple jobs from a single scrape

### Requirement 11: Application Entry Point

**User Story:** As a user, I want a single entry point to start the application in different modes, so that I can run the scraper, dashboard, or scheduler independently.

#### Acceptance Criteria

1. WHEN main.py is executed with the "scrape" argument, THE Application SHALL run a single scrape cycle and exit with exit code 0 on success or exit code 1 on failure
2. WHEN main.py is executed with the "dashboard" argument, THE Application SHALL start the Streamlit dashboard process
3. WHEN main.py is executed with the "schedule" argument, THE Application SHALL start the scheduler for continuous automated operation until the process is manually terminated
4. WHEN main.py is executed with no arguments, THE Application SHALL display the list of available commands ("scrape", "dashboard", "schedule") with a one-line description of each command and exit with exit code 0
5. IF main.py is executed with an unrecognized argument, THEN THE Application SHALL display an error message indicating the argument is not valid, display the list of available commands, and exit with exit code 2
