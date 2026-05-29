# Implementation Plan: Job Copilot

## Overview

Implement a Python job search automation pipeline that scrapes job listings from LinkedIn, Indeed, and Naukri using the existing `python-jobspy` library, stores results in daily CSV files, extracts skills from a resume PDF, and scores each job against the resume. The implementation follows a modular structure with a scraper wrapper, CSV storage utility, resume parser with skills extraction, a matcher, and an orchestrator entry point.

## Tasks

- [x] 1. Set up project structure and dependencies
  - [x] 1.1 Create directory structure and module init files
    - Create `scraper/` directory with `__init__.py`
    - Create `matcher/` directory with `__init__.py`
    - Create `data/` directory (empty, for CSV output)
    - Create `resume/` directory and place resume PDF at `resume/resume.pdf`
    - Create `tests/` directory with `tests/fixtures/` subdirectory
    - _Requirements: 7.1, 7.2, 7.3, 7.5_

  - [x] 1.2 Add project dependencies
    - Add `PyPDF2>=3.0` to project dependencies for PDF text extraction
    - Add `hypothesis>=6.0` and `pytest>=7.0` to dev dependencies
    - _Requirements: 3.1_

- [x] 2. Implement scraper module
  - [x] 2.1 Implement `scraper/scrape_jobs.py` with `scrape_all_jobs()` function
    - Create function that accepts `search_terms`, `sites`, `country`, and `results_wanted` parameters
    - Iterate over each search term, calling `jobspy.scrape_jobs()` with `site_name=sites`, `country_indeed=country`, `results_wanted=results_wanted`
    - Catch and log exceptions per search term so partial failures don't halt the pipeline
    - Concatenate all result DataFrames and return the combined DataFrame
    - Return an empty DataFrame if all searches yield no results
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 2.2 Expose scraper function in `scraper/__init__.py`
    - Import and re-export `scrape_all_jobs` from `scraper/scrape_jobs.py`
    - _Requirements: 7.2, 7.6_

  - [ ]* 2.3 Write property test for scraper resilience (Property 1)
    - **Property 1: Scraper resilience on partial failures**
    - Mock `jobspy.scrape_jobs()` to raise exceptions for random subsets of boards
    - Verify that results from non-failing boards are still returned
    - Verify no exception is raised to the caller
    - **Validates: Requirements 1.4**

- [x] 3. Implement CSV storage
  - [x] 3.1 Implement `save_jobs_to_csv()` utility function
    - Create function in `scraper/scrape_jobs.py` (or a shared utils module) that accepts a DataFrame and output directory
    - Create `data/` directory if it doesn't exist using `os.makedirs(output_dir, exist_ok=True)`
    - Deduplicate by `job_url` keeping first occurrence: `df.drop_duplicates(subset=["job_url"], keep="first")`
    - Fill NaN/None values with empty strings for required columns (site, title, company, location, job_url, description, date_posted, job_type, skills)
    - Write to `data/jobs_YYYY-MM-DD.csv` with UTF-8 encoding, overwriting if exists
    - Raise `IOError` with descriptive message on filesystem write failure
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

  - [ ]* 3.2 Write property test for CSV column completeness (Property 2)
    - **Property 2: CSV column completeness**
    - Generate DataFrames with random None fields using Hypothesis
    - Verify saved CSV always contains all required columns with empty strings for missing values
    - **Validates: Requirements 2.3**

  - [ ]* 3.3 Write property test for CSV combining all search term results (Property 3)
    - **Property 3: CSV combines all search term results**
    - Generate multiple DataFrames of varying sizes
    - Verify combined output row count equals sum of input rows before deduplication
    - **Validates: Requirements 2.4**

  - [ ]* 3.4 Write property test for deduplication (Property 4)
    - **Property 4: Deduplication preserves first occurrence**
    - Generate job lists with controlled duplicate job_urls
    - Verify every job_url is unique in output and retained row matches first occurrence
    - **Validates: Requirements 2.5**

- [x] 4. Checkpoint - Ensure scraper and CSV storage tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement resume parser and skills extraction
  - [x] 5.1 Implement `extract_resume_text()` in `matcher/matcher.py`
    - Use PyPDF2 to open and read the PDF file
    - Extract text from each page (up to 10 pages), concatenate with newline separators
    - Raise `FileNotFoundError` if PDF path doesn't exist
    - Raise `ValueError` if PDF is corrupted/unreadable or contains no extractable text
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 5.2 Define skills dictionary and implement `extract_skills()` in `matcher/matcher.py`
    - Create a `SKILLS_DICTIONARY` list with at least 50 entries covering biomedical engineering, software development, and embedded systems domains
    - Include both single-word (e.g., "python") and multi-word (e.g., "signal processing") skills
    - Implement `extract_skills(resume_text, skills_dict)` using case-insensitive substring matching (`skill.lower() in resume_text.lower()`)
    - Return deduplicated list of matched skills as lowercase strings (each ≤ 100 characters)
    - Return empty list if no skills match
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 5.3 Write property test for skills extraction correctness (Property 5)
    - **Property 5: Skills extraction correctness**
    - Generate text with embedded skills from a random subset of the dictionary
    - Verify extracted skills contain exactly those dictionary entries present as substrings
    - **Validates: Requirements 4.1, 4.2**

  - [ ]* 5.4 Write property test for skills output format (Property 6)
    - **Property 6: Skills output format invariant**
    - Generate arbitrary text and verify every returned skill is lowercase, ≤ 100 chars, and unique
    - **Validates: Requirements 4.3, 4.4**

- [x] 6. Implement matcher
  - [x] 6.1 Implement `compute_match()` in `matcher/matcher.py`
    - Accept `description` (str) and `skills` (list[str]) parameters
    - Return `{"score": 0, "matched_skills": []}` if description is empty/None or skills is empty/None
    - Perform case-insensitive substring matching for each skill in the description
    - Calculate score as `floor(matched_count / total_skills * 100)`
    - Return dict with `score` (int 0-100) and `matched_skills` (list of matched skill strings)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 6.2 Expose matcher functions in `matcher/__init__.py`
    - Import and re-export `extract_resume_text`, `extract_skills`, and `compute_match`
    - _Requirements: 7.3, 7.6_

  - [ ]* 6.3 Write property test for match score bounds (Property 7)
    - **Property 7: Match score is bounded**
    - Generate random descriptions and skill lists
    - Verify score is always an integer in [0, 100]
    - **Validates: Requirements 5.1**

  - [ ]* 6.4 Write property test for match score computation (Property 8)
    - **Property 8: Match score computation correctness**
    - Generate descriptions with known skill presence
    - Verify score equals `floor(found_count / total_count * 100)`
    - Verify matched_skills contains exactly the skills present in description
    - **Validates: Requirements 5.2, 5.3, 5.4**

- [x] 7. Checkpoint - Ensure matcher and resume parser tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement orchestrator
  - [x] 8.1 Implement `main.py` orchestrator entry point
    - Define configuration constants: `SEARCH_TERMS`, `SITES`, `COUNTRY`, `RESULTS_WANTED`, `RESUME_PATH`, `OUTPUT_DIR`
    - Check if resume file exists at `resume/resume.pdf`; if not, print error and `sys.exit(1)`
    - Call `scrape_all_jobs()` with configured parameters
    - If no jobs scraped (empty DataFrame), print "no results found" message and `sys.exit(0)`
    - Call `save_jobs_to_csv()` to deduplicate and persist results
    - Call `extract_resume_text()` and `extract_skills()` to get the skills list
    - Iterate over each job listing, call `compute_match()` for each
    - Print summary: total jobs scraped, unique jobs after dedup, top 10 by match score (title, company, score)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [ ]* 8.2 Write unit tests for orchestrator
    - Mock all dependencies (scraper, CSV store, resume parser, matcher)
    - Test successful pipeline flow end-to-end
    - Test exit code 1 when resume file is missing
    - Test exit code 0 when no jobs are scraped
    - Test summary output format with top 10 display
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 9. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document using Hypothesis
- Unit tests validate specific examples and edge cases
- The scraper module is a thin wrapper around the existing `jobspy.scrape_jobs()` function
- PyPDF2 is used for resume text extraction (lightweight, pure-Python)
- All matching uses simple case-insensitive substring matching for determinism

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1", "5.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "5.2"] },
    { "id": 3, "tasks": ["3.1", "5.3", "5.4"] },
    { "id": 4, "tasks": ["3.2", "3.3", "3.4", "6.1"] },
    { "id": 5, "tasks": ["6.2", "6.3", "6.4"] },
    { "id": 6, "tasks": ["8.1"] },
    { "id": 7, "tasks": ["8.2"] }
  ]
}
```
