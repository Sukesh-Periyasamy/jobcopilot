# Implementation Plan: JobCopilot v1.1 Upgrade

## Overview

This plan implements the JobCopilot v1.1 upgrade incrementally: starting with data model extensions and new dependencies, then the JobHive scraper, scrape orchestrator merge, filter engine updates, export service, watchlist/company tracker enhancements, and finally frontend updates. Each step builds on the previous, ensuring no orphaned code.

## Tasks

- [x] 1. Extend data models and add dependencies
  - [x] 1.1 Update JobRecord dataclass with source metadata fields
    - Add `source_type: str = ""` and `source_platform: str = ""` fields to the `JobRecord` dataclass in `backend/app/models/job.py`
    - Ensure default values maintain backward compatibility with existing code
    - _Requirements: 3.1, 3.2_

  - [x] 1.2 Update FilterCriteria with new filter fields
    - Add `source_type: str | None = None` and `source_platform: str | None = None` to `FilterCriteria` in `backend/app/services/filter_engine.py`
    - _Requirements: 4.1, 4.2_

  - [x] 1.3 Update Pydantic schemas (JobResponse, WatchlistRequest, new schemas)
    - Add `source_type` and `source_platform` to `JobResponse` in `backend/app/models/schemas.py`
    - Update `WatchlistRequest` to accept optional `ats_platform` field with regex validation
    - Add `WatchlistEntry`, `AtsGroupResponse` schemas
    - _Requirements: 3.1, 3.2, 6.1, 6.4, 6.5_

  - [x] 1.4 Add new dependencies to requirements.txt
    - Add `jobhive-py` and `openpyxl` to `backend/requirements.txt`
    - _Requirements: 1.1, 5.2, 12.5_

- [x] 2. Implement JobHive scraper and update JobSpy scraper
  - [x] 2.1 Create JobHive scraper module
    - Create `backend/app/scraper/jobhive_scraper.py` with `scrape_jobhive(settings)` function
    - Implement `_normalize_jobhive_result(raw, platform, search_term)` helper
    - Iterate over ATS platforms (greenhouse, lever, ashby, workday, successfactors)
    - Set `source_type="jobhive"` and `source_platform` to lowercase platform name
    - Handle per-platform failures gracefully (log and continue)
    - Return `ScrapeResult` with collected jobs and errors
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 3.4_

  - [x]* 2.2 Write property test for JobHive normalization
    - **Property 1: JobHive Normalization Correctness**
    - Use Hypothesis to generate random dicts with varying fields
    - Verify: source_type == "jobhive", source_platform == lowercase platform name, missing optional fields default to empty string
    - **Validates: Requirements 1.2, 1.3, 3.4**

  - [x] 2.3 Update JobSpy scraper with source metadata
    - Modify `_normalize_row` in `backend/app/scraper/scraper.py` to set `source_type="jobspy"` and `source_platform` from the lowercase `site` field
    - _Requirements: 3.3_

  - [x]* 2.4 Write property test for JobSpy normalization
    - **Property 2: JobSpy Normalization Correctness**
    - Use Hypothesis to generate random DataFrame rows with varying site values
    - Verify: source_type == "jobspy", source_platform == lowercase site value
    - **Validates: Requirements 3.3**

  - [x]* 2.5 Write unit tests for JobHive scraper
    - Test platform failure isolation (one platform fails, others succeed)
    - Test empty results from all platforms
    - Test missing optional fields normalization
    - Test results with missing required fields (title, job_url) are skipped
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 3. Update scrape orchestrator to merge results
  - [x] 3.1 Update daily_scraper.py to invoke both scrapers
    - Add `_run_jobhive(settings)` wrapper function with error handling
    - Update `_run_workflow()` to call both scrapers sequentially
    - Merge results: combine job lists and error lists
    - Handle partial failures (one scraper fails, other succeeds)
    - Pass merged result to existing bulk insert, history, and notification logic
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 12.4_

  - [x]* 3.2 Write property test for scrape merge completeness
    - **Property 3: Scrape Merge Completeness**
    - Use Hypothesis to generate random ScrapeResult pairs
    - Verify: merged job count == sum of individual counts, merged error count == sum of individual error counts
    - **Validates: Requirements 2.2, 2.4**

  - [x]* 3.3 Write unit tests for scrape orchestrator
    - Test JobHive failure with JobSpy success scenario
    - Test JobSpy failure with JobHive success scenario
    - Test both scrapers succeed scenario
    - Test scrape history records combined counts
    - _Requirements: 2.5, 2.6_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Update repository and database layer
  - [x] 5.1 Update repository for backward compatibility and new indexes
    - Update `_doc_to_job_record` in `backend/app/database/repository.py` to handle missing `source_type`/`source_platform` fields (default source_type to "jobspy", derive source_platform from source field)
    - Add `source_type` and `source_platform` indexes in `ensure_indexes`
    - Add `get_export_jobs` method with filter support and 10000 record limit
    - Update watchlist methods to handle `ats_platform` field
    - Update default watchlist seed with ATS platform info (Philips/workday, GE HealthCare/workday, Siemens Healthineers/successfactors, Medtronic/workday, Abbott/workday, Dozee/lever, Niramai/greenhouse)
    - _Requirements: 3.5, 3.6, 5.7, 6.1, 6.2, 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x]* 5.2 Write property test for backward compatibility defaults
    - **Property 4: Backward Compatibility Defaults**
    - Use Hypothesis to generate legacy MongoDB documents (missing source_type and source_platform)
    - Verify: source_type defaults to "jobspy", source_platform derived from lowercase source field
    - **Validates: Requirements 3.5**

  - [x]* 5.3 Write unit tests for repository updates
    - Test index creation for new fields
    - Test backward compatibility for legacy documents
    - Test get_export_jobs with 10000 limit
    - Test watchlist methods with ats_platform field
    - _Requirements: 7.1, 7.2, 7.3, 3.5, 3.6_

- [x] 6. Extend filter engine with source filtering
  - [x] 6.1 Add source_type and source_platform filter logic
    - Update `build_query` in `backend/app/services/filter_engine.py` to handle `source_type` filter (case-insensitive regex match)
    - Add `source_platform` filter with special "ats" umbrella value (matches greenhouse, lever, ashby, workday, successfactors)
    - Ensure new filters compose with existing filters using AND logic
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6_

  - [x]* 6.2 Write property test for source filter correctness
    - **Property 5: Source Filter Correctness**
    - Use Hypothesis to generate sets of JobRecords and filter values (including "ats" umbrella)
    - Verify: filtered results only contain records matching the criterion
    - **Validates: Requirements 4.1, 4.2, 4.3**

  - [x]* 6.3 Write property test for filter composition AND logic
    - **Property 6: Filter Composition AND Logic**
    - Use Hypothesis to generate multi-criteria filters
    - Verify: every job in result satisfies ALL specified criteria simultaneously
    - **Validates: Requirements 4.4**

  - [x]* 6.4 Write unit tests for filter engine updates
    - Test "ats" umbrella value returns correct platforms
    - Test combined source_type + source_platform + existing filters
    - Test backward compatibility of existing source filter
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6_

- [x] 7. Implement export service and API
  - [x] 7.1 Create export service module
    - Create `backend/app/services/export_service.py`
    - Implement `export_csv(jobs)` returning `(BytesIO, was_truncated)` tuple
    - Implement `export_xlsx(jobs)` returning `(BytesIO, was_truncated)` tuple
    - Define `EXPORT_COLUMNS` constant and `MAX_EXPORT_RECORDS = 10000`
    - Generate files in-memory (BytesIO) without disk writes
    - Handle empty job lists (header-only file)
    - Handle truncation at 10000 records
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.7, 12.3_

  - [x] 7.2 Create export API router
    - Create `backend/app/api/export.py` with `GET /export/csv` and `GET /export/xlsx` endpoints
    - Accept all filter parameters (including source_type, source_platform)
    - Return StreamingResponse with correct Content-Type and Content-Disposition headers
    - Add `X-Export-Truncated: true` header when results are truncated
    - Register router in main app
    - _Requirements: 5.1, 5.2, 5.3, 5.6, 5.7_

  - [x]* 7.3 Write property test for export round-trip correctness
    - **Property 7: Export Round-Trip Correctness**
    - Use Hypothesis to generate lists of JobRecords
    - Export to CSV/XLSX, parse output, verify columns and values match originals
    - **Validates: Requirements 5.1, 5.2, 5.4**

  - [x]* 7.4 Write unit tests for export service
    - Test empty export (header-only)
    - Test truncation at 10000 records
    - Test correct Content-Type headers
    - Test CSV and XLSX output format
    - _Requirements: 5.4, 5.5, 5.6, 5.7_

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Update watchlist API for company tracker
  - [x] 9.1 Update watchlist API endpoints
    - Update `GET /watchlist` to return `[{company_name, ats_platform}]` format
    - Update `POST /watchlist` to accept optional `ats_platform` field
    - Add `GET /watchlist/ats-info` endpoint returning companies grouped by ATS platform
    - Maintain existing validation (max 50 companies, max 100 chars per name)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

  - [x]* 9.2 Write property test for ATS-info grouping
    - **Property 8: ATS-Info Grouping Correctness**
    - Use Hypothesis to generate watchlist entries with various ats_platform values
    - Verify: every company in a group has the corresponding platform, every company with non-null platform appears in exactly one group
    - **Validates: Requirements 6.5**

  - [x]* 9.3 Write unit tests for watchlist API updates
    - Test ats_platform storage and retrieval
    - Test ats_platform validation (only valid platforms accepted)
    - Test backward compatibility (entries without ats_platform return null)
    - Test ats-info grouping endpoint
    - _Requirements: 6.1, 6.3, 6.4, 6.5, 6.6, 6.7_

- [x] 10. Update jobs API endpoint with new filter parameters
  - [x] 10.1 Add source_type and source_platform query parameters to GET /jobs
    - Update `backend/app/api/jobs.py` to accept `source_type` and `source_platform` optional query parameters
    - Pass new parameters to FilterCriteria and filter engine
    - Ensure existing parameters continue to work unchanged
    - _Requirements: 4.5, 4.6_

- [x] 11. Implement frontend updates
  - [x] 11.1 Update frontend filter dropdown with ATS source options
    - Update source filter dropdown in `frontend/js/jobs.js` to include: All Sources, LinkedIn Jobs, Indeed Jobs, Naukri Jobs, Google Jobs, ATS Jobs (umbrella), Workday Jobs, Greenhouse Jobs, Lever Jobs, Ashby Jobs, SuccessFactors Jobs
    - Map "ATS Jobs" selection to `source_platform=ats` API parameter
    - Map specific platform selections to corresponding `source_platform` values
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [x] 11.2 Add source platform badges to job cards
    - Update `frontend/js/components.js` to render color-coded pill badges based on `source_platform`
    - Define color mapping: LinkedIn (blue), Indeed (purple), Naukri (red), Google (green), Workday (orange), Greenhouse (teal), Lever (indigo), Ashby (pink), SuccessFactors (amber)
    - Handle backward compatibility: derive badge from `source` field when `source_platform` is missing
    - Style badges as pill-shaped elements matching glassmorphism design
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 11.3 Add export buttons to jobs feed page
    - Add CSV and XLSX export buttons near filter controls in `frontend/jobs.html` and `frontend/js/jobs.js`
    - On click, make GET request to `/export/csv` or `/export/xlsx` with current active filters
    - Show loading indicator on clicked button, disable both buttons during export
    - Display toast notification on error, re-enable buttons
    - Trigger file download on success
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [x] 11.4 Enhance watchlist page with company tracker
    - Update `frontend/watchlist.html` and `frontend/js/watchlist.js` to display ATS platform badges per company
    - Add ATS platform dropdown to the add-company form (Workday, Greenhouse, Lever, Ashby, SuccessFactors, None)
    - Display "Unknown" when company has no ATS platform
    - Use same color-coded badges as job cards
    - Maintain existing add/remove functionality
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 11.5 Update API client for new endpoints and parameters
    - Update `frontend/js/api.js` to support new filter parameters (source_type, source_platform)
    - Add export endpoint calls (GET /export/csv, GET /export/xlsx) with blob response handling
    - Add watchlist ats-info endpoint call (GET /watchlist/ats-info)
    - Update watchlist POST to include ats_platform field
    - _Requirements: 4.5, 5.1, 5.2, 6.3, 6.5_

  - [x] 11.6 Add CSS styles for source badges and export controls
    - Add pill badge styles with platform-specific colors to `frontend/css/style.css`
    - Add export button styles with loading state
    - Ensure consistency with existing glassmorphism design system
    - _Requirements: 8.4, 9.1_

- [x] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The implementation uses Python (FastAPI, pytest, hypothesis) matching the existing codebase
- All exports are in-memory (BytesIO) to comply with Render's ephemeral filesystem (Requirement 12.3)
- Backward compatibility is handled at read-time, no data migration needed (Requirement 3.6)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.4"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["2.1", "2.3"] },
    { "id": 3, "tasks": ["2.2", "2.4", "2.5", "5.1"] },
    { "id": 4, "tasks": ["3.1", "5.2", "5.3"] },
    { "id": 5, "tasks": ["3.2", "3.3", "6.1"] },
    { "id": 6, "tasks": ["6.2", "6.3", "6.4", "7.1"] },
    { "id": 7, "tasks": ["7.2", "7.3", "7.4"] },
    { "id": 8, "tasks": ["9.1", "10.1"] },
    { "id": 9, "tasks": ["9.2", "9.3", "11.5"] },
    { "id": 10, "tasks": ["11.1", "11.2", "11.3", "11.4", "11.6"] }
  ]
}
```
