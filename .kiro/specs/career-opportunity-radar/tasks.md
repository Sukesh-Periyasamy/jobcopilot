# Implementation Plan: Career Opportunity Radar

## Overview

This plan upgrades JobCopilot from v1.1.0 to v1.2.0 by adding five new backend service modules (Collection Engine, Opportunity Feed, Internship Tracker, Research Tracker, Analytics Engine), enhancing the Telegram notifier, introducing tiered watchlist and personal dashboard preferences, and delivering two new frontend pages (analytics.html, internships.html). All tasks build incrementally on the existing FastAPI + PyMongo + static HTML architecture.

## Tasks

- [x] 1. Define data models and shared constants
  - [x] 1.1 Create collection definitions, internship keywords, and research institutions constants
    - Create `backend/app/services/__init__.py` if not present
    - Create `backend/app/services/constants.py` with `CollectionDefinition` dataclass, `COLLECTIONS` list (11 collections), `INTERNSHIP_KEYWORDS` list (15 keywords), and `RESEARCH_INSTITUTIONS` list (13 institutions)
    - _Requirements: 1.1, 1.3, 4.1, 5.1_

  - [x] 1.2 Add new Pydantic response models to schemas
    - Add `CollectionSummary`, `CollectionDetail`, `OpportunityFeedResponse`, `AnalyticsResponse`, `PersonalDashboardResponse`, and `PaginatedResult` models to `backend/app/models/schemas.py`
    - _Requirements: 2.1, 2.2, 3.1, 6.5, 12.3_

  - [x] 1.3 Add tier field to watchlist schema and update existing watchlist endpoints
    - Modify `backend/app/api/watchlist.py` to include `tier` field (default "tier3") in watchlist responses
    - Add `PATCH /watchlist/{company}` endpoint for updating tier
    - Validate tier values to only allow "tier1", "tier2", "tier3"
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [x] 1.4 Create preferences MongoDB collection document schema
    - Add preferences collection access in `backend/app/database/connection.py` or repository
    - Document schema: `{"type": "pinned_collections"|"pinned_companies", "items": [...]}`
    - _Requirements: 12.5_

- [x] 2. Implement Collection Engine service
  - [x] 2.1 Implement CollectionEngine class
    - Create `backend/app/services/collection_engine.py`
    - Implement `get_all_collections()` returning all collection names with job counts
    - Implement `get_collection(name)` returning collection metadata or None
    - Implement `get_collection_jobs(name, page, page_size)` returning paginated jobs sorted by date_posted descending
    - Implement `_build_collection_query(keywords)` building MongoDB `$or` query with case-insensitive regex on title and description
    - _Requirements: 1.2, 1.4, 1.5, 2.1, 2.2, 2.3, 11.5_

  - [ ]* 2.2 Write property test for collection keyword classification (Property 1)
    - **Property 1: Collection keyword classification is correct and complete**
    - Use Hypothesis to generate job records with controlled keyword embedding
    - Verify jobs are classified into exactly those collections whose keywords appear in title/description
    - **Validates: Requirements 1.2, 1.4**

  - [ ]* 2.3 Write property test for paginated results sort order (Property 2)
    - **Property 2: Paginated results are sorted descending by date_posted**
    - Use Hypothesis to generate job sets with varied dates
    - Verify all paginated responses from collection_engine are sorted by date_posted descending
    - **Validates: Requirements 2.3, 4.2, 5.2**

- [x] 3. Implement Collections API endpoints
  - [x] 3.1 Create collections API router
    - Create `backend/app/api/collections.py`
    - Implement `GET /collections` returning list of all collections with counts
    - Implement `GET /collections/{name}` returning collection metadata or 404
    - Implement `GET /collections/{name}/jobs` with page/page_size query params (defaults: 1, 50)
    - Register router in main app
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 3.2 Write unit tests for collections API
    - Test 404 response for non-existent collection
    - Test default pagination parameters
    - Test response structure matches CollectionSummary/CollectionDetail models
    - _Requirements: 2.4, 2.5_

- [x] 4. Implement Opportunity Feed Service
  - [x] 4.1 Implement OpportunityFeedService class
    - Create `backend/app/services/opportunity_feed.py`
    - Implement `get_feed()` returning dict with 6 categories
    - Implement `_get_top_companies()` aggregating companies by job count (top 10)
    - Implement `_get_new_companies()` finding companies first seen in last 7 days
    - Implement `_get_remote_jobs()` querying jobs with "remote" in location
    - Implement `_get_internships()` querying jobs matching internship keywords in title
    - Implement `_get_research_roles()` querying jobs from research institutions
    - Implement `_get_healthcare_roles()` querying jobs matching healthcare/medtech keywords
    - Each category limited to max 10 entries
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

  - [ ]* 4.2 Write property test for filtered queries returning only matching results (Property 3)
    - **Property 3: Filtered queries return only matching results**
    - Use Hypothesis to generate job sets with varied locations, titles, companies
    - Verify remote_jobs all have "remote" in location, internships have internship keywords in title, research roles have institution names in company/description
    - **Validates: Requirements 3.4, 3.5, 3.6, 4.1, 4.3, 5.1, 5.4**

  - [ ]* 4.3 Write property test for new companies first-seen within 7 days (Property 4)
    - **Property 4: New companies are first-seen within 7 days**
    - Use Hypothesis to generate job sets with varied date_posted values
    - Verify new_companies only contains companies whose earliest date_posted is within last 7 days
    - **Validates: Requirements 3.3**

  - [ ]* 4.4 Write property test for maximum entry limits (Property 5)
    - **Property 5: Opportunity feed and recent research enforce maximum entry limits**
    - Use Hypothesis to generate large job sets
    - Verify each category in /opportunities response contains at most 10 entries
    - **Validates: Requirements 3.8, 5.3**

- [x] 5. Implement Opportunities API endpoint
  - [x] 5.1 Create opportunities API router
    - Create `backend/app/api/opportunities.py`
    - Implement `GET /opportunities` returning categorized feed
    - Register router in main app
    - _Requirements: 3.1_

- [x] 6. Implement Internship Tracker service and API
  - [x] 6.1 Implement InternshipTracker class
    - Create `backend/app/services/internship_tracker.py`
    - Implement `get_internships(keyword, page, page_size)` returning paginated internships sorted by date_posted descending
    - Implement `_build_internship_query(keyword)` building regex `$or` query matching internship keywords in title
    - Support optional keyword filter for specific Internship_Keyword
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 6.2 Create internships API router
    - Create `backend/app/api/internships.py`
    - Implement `GET /internships` with optional keyword, page, page_size query params
    - Register router in main app
    - _Requirements: 4.2, 4.3_

  - [ ]* 6.3 Write unit tests for internship tracker
    - Test keyword filtering returns only matching results
    - Test pagination defaults
    - Test empty results for non-matching keyword
    - _Requirements: 4.1, 4.3_

- [x] 7. Implement Research Tracker service and API
  - [x] 7.1 Implement ResearchTracker class
    - Create `backend/app/services/research_tracker.py`
    - Implement `get_research_jobs(institution, page, page_size)` returning paginated research jobs sorted by date_posted descending
    - Implement `get_recent_research(limit=10)` returning most recent research opportunities
    - Implement `_build_research_query(institution)` building regex `$or` query matching institution names in company or description
    - Support optional institution filter
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 7.2 Create research API router
    - Create `backend/app/api/research.py`
    - Implement `GET /research` with optional institution, page, page_size query params
    - Implement `GET /research/recent` returning 10 most recent research jobs
    - Register router in main app
    - _Requirements: 5.2, 5.3, 5.4_

  - [ ]* 7.3 Write unit tests for research tracker
    - Test institution filtering returns only matching results
    - Test /research/recent returns at most 10 entries
    - Test pagination defaults
    - _Requirements: 5.1, 5.3, 5.4_

- [x] 8. Checkpoint - Core services complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Implement Analytics Engine service and API
  - [x] 9.1 Implement AnalyticsEngine class
    - Create `backend/app/services/analytics_engine.py`
    - Implement `compute_analytics()` returning all metrics in a single dict
    - Implement `_jobs_per_day()` aggregating job counts by date_posted for last 30 days
    - Implement `_jobs_per_company()` aggregating top 20 companies by job count
    - Implement `_jobs_per_source()` aggregating all sources by job count
    - Implement `_jobs_per_platform()` aggregating all ATS platforms by job count
    - Implement `_jobs_per_location()` aggregating top 20 locations by job count
    - Implement `_jobs_per_collection()` computing job count for each collection
    - Implement `_internship_vs_fulltime()` counting internship vs non-internship jobs
    - Implement `_research_vs_industry()` counting research institution vs other jobs
    - Use MongoDB aggregation pipelines ($group, $sort, $limit) for all computations
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 11.4_

  - [x] 9.2 Create analytics API router
    - Create `backend/app/api/analytics.py`
    - Implement `GET /analytics` returning all computed metrics
    - Register router in main app
    - _Requirements: 6.5_

  - [ ]* 9.3 Write property test for top-N aggregations ordering (Property 6)
    - **Property 6: Top-N aggregations are correctly ordered by count**
    - Use Hypothesis to generate job sets with varied companies, locations, platforms
    - Verify top_hiring_companies, top_locations, top_ats_platforms are ordered by descending job count
    - Verify no excluded entry has a higher count than any included entry
    - **Validates: Requirements 6.2, 6.3, 6.4**

  - [ ]* 9.4 Write property test for partition metrics summing to total (Property 7)
    - **Property 7: Partition metrics sum to total job count**
    - Use Hypothesis to generate job sets
    - Verify internship_count + fulltime_count == total jobs
    - Verify research_count + industry_count == total jobs
    - **Validates: Requirements 6.6, 6.7**

- [x] 10. Implement Telegram Intelligence Service
  - [x] 10.1 Enhance TelegramNotifier with intelligence summary
    - Modify `backend/app/services/notifier.py` (or existing Telegram notifier file)
    - Add `send_intelligence_summary(jobs, watchlist)` method
    - Format summary with 5 sections: Top 10 jobs, Top internships (5), Top research (5), Watchlist companies hiring, New ATS opportunities (5)
    - Include job title, company, location, URL for each entry
    - Implement message splitting at 4096 character limit using existing splitting logic
    - Prioritize Tier 1 watchlist companies first, then Tier 2, then Tier 3
    - Skip silently if Telegram credentials not configured
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 9.6_

  - [ ]* 10.2 Write property test for intelligence summary sections (Property 8)
    - **Property 8: Intelligence summary contains all required sections with formatted job details**
    - Use Hypothesis to generate non-empty job sets and watchlist entries
    - Verify summary contains all 5 section headers and job details (title, company, location, URL)
    - **Validates: Requirements 8.2, 8.3**

  - [ ]* 10.3 Write property test for message splitting (Property 9)
    - **Property 9: Message splitting respects Telegram character limit**
    - Use Hypothesis to generate intelligence summaries of varying lengths
    - Verify each split message is at most 4096 characters
    - Verify concatenation of all split messages contains all original content
    - **Validates: Requirements 8.5**

  - [ ]* 10.4 Write property test for tier ordering (Property 10)
    - **Property 10: Tier 1 watchlist companies appear first in intelligence summary**
    - Use Hypothesis to generate watchlist entries with mixed tiers
    - Verify Tier 1 companies appear before Tier 2, and Tier 2 before Tier 3
    - **Validates: Requirements 9.6**

- [x] 11. Implement Personal Dashboard Preferences
  - [x] 11.1 Implement preferences API endpoints
    - Create `backend/app/api/preferences.py`
    - Implement `POST /preferences/pinned-collections` (max 5, return 409 if exceeded)
    - Implement `POST /preferences/pinned-companies` (max 10, return 409 if exceeded)
    - Implement `GET /preferences/dashboard` returning jobs from pinned companies, pinned collections, and recent research (last 7 days)
    - Implement `DELETE /preferences/pinned-collections/{name}` to unpin a collection
    - Implement `DELETE /preferences/pinned-companies/{name}` to unpin a company
    - Register router in main app
    - _Requirements: 12.1, 12.2, 12.3, 12.5, 12.6, 12.7_

  - [ ]* 11.2 Write property test for personal dashboard filtering (Property 11)
    - **Property 11: Personal dashboard returns only jobs matching pinned preferences**
    - Use Hypothesis to generate pinned collections, pinned companies, and job sets
    - Verify response only includes jobs from pinned companies, matching pinned collection keywords, or research opportunities from last 7 days
    - **Validates: Requirements 12.3**

  - [ ]* 11.3 Write property test for pinned preferences limits (Property 12)
    - **Property 12: Pinned preferences enforce maximum limits**
    - Use Hypothesis to generate sequences of pin operations
    - Verify system never stores more than 5 pinned collections or 10 pinned companies
    - Verify excess attempts are rejected without modifying existing items
    - **Validates: Requirements 12.6, 12.7**

- [x] 12. Checkpoint - Backend complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Implement Analytics Dashboard Frontend
  - [x] 13.1 Create analytics.html page
    - Create `frontend/analytics.html` (or appropriate frontend directory matching existing structure)
    - Include Chart.js from CDN
    - Render charts: Jobs by Source, Jobs by ATS Platform, Jobs by Location, Jobs by Company, Internships vs Full-Time, Research vs Industry, Jobs by Collection
    - Fetch data from `/analytics` endpoint on page load
    - Display loading states while fetching
    - Display error message with retry button if API returns error
    - Reuse existing dark mode glassmorphism design system
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [x] 14. Implement Internships Frontend
  - [x] 14.1 Create internships.html page
    - Create `frontend/internships.html` (or appropriate frontend directory matching existing structure)
    - Display internship listings with title, company, location, date posted, and job URL link
    - Add filter dropdown for selecting specific Internship_Keywords
    - Fetch data from `/internships` endpoint with optional keyword param
    - Reuse existing dark mode glassmorphism design system
    - _Requirements: 4.4, 4.5, 4.6_

- [x] 15. Implement Personal Dashboard Frontend section
  - [x] 15.1 Add personal dashboard sections to index.html
    - Modify existing `frontend/index.html` (or main dashboard page)
    - Add pinned company jobs section, pinned collection jobs section, and new research opportunities section
    - Display these sections above all other dashboard content
    - Fetch data from `/preferences/dashboard` endpoint
    - Gracefully hide pinned sections if API fails, showing only existing v1.1 content
    - _Requirements: 12.3, 12.4_

- [x] 16. Wire daily scraper to Telegram Intelligence Service
  - [x] 16.1 Integrate intelligence summary into scraper workflow
    - Modify the daily scraper entry point to call `send_intelligence_summary()` after completing the scrape cycle
    - Pass scraped jobs and current watchlist to the intelligence service
    - Ensure existing Telegram notification behavior for new jobs and watchlist alerts is preserved
    - _Requirements: 8.1, 10.3, 10.4_

- [x] 17. Register all new API routers in main application
  - [x] 17.1 Update main FastAPI app to include all new routers
    - Register collections, opportunities, internships, research, analytics, and preferences routers in the main app file
    - Verify all existing v1.1 endpoints remain unchanged
    - _Requirements: 10.1, 10.2_

- [x] 18. Final checkpoint - Full integration
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document using Hypothesis
- Unit tests validate specific examples and edge cases
- All services follow the existing pattern of stateless Python classes
- No new dependencies beyond what's already in requirements.txt (hypothesis, pymongo, fastapi, etc.)
- Frontend pages follow existing static HTML pattern with no build step

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.4"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["2.1", "6.1", "7.1"] },
    { "id": 3, "tasks": ["2.2", "2.3", "3.1", "4.1", "6.2", "7.2"] },
    { "id": 4, "tasks": ["3.2", "4.2", "4.3", "4.4", "5.1", "6.3", "7.3"] },
    { "id": 5, "tasks": ["9.1"] },
    { "id": 6, "tasks": ["9.2", "9.3", "9.4"] },
    { "id": 7, "tasks": ["10.1", "11.1"] },
    { "id": 8, "tasks": ["10.2", "10.3", "10.4", "11.2", "11.3"] },
    { "id": 9, "tasks": ["13.1", "14.1", "15.1"] },
    { "id": 10, "tasks": ["16.1", "17.1"] }
  ]
}
```
