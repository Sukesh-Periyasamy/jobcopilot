# Requirements Document

## Introduction

JobCopilot is a personal job search automation tool for a Biomedical Engineer profile. It scrapes job listings from multiple job boards (LinkedIn, Indeed, Naukri) for relevant search terms, stores results in daily CSV files, and matches jobs against a resume to produce relevance scores. The system leverages the locally available python-jobspy library for scraping and uses PDF text extraction for resume parsing.

## Glossary

- **Scraper**: The module that uses the python-jobspy library to fetch job listings from external job boards
- **Job_Board**: An external website that lists job postings (LinkedIn, Indeed, Naukri)
- **Search_Term**: A role-specific keyword used to query job boards (e.g., "Biomedical Engineer", "Medical Device Engineer")
- **Job_Listing**: A single job posting record containing title, company, location, URL, description, and metadata
- **CSV_Store**: The `data/` directory where scraped job results are persisted as CSV files
- **Resume_Parser**: The module that extracts text content from a PDF resume file
- **Skills_List**: A structured collection of skills extracted from the resume text
- **Match_Score**: A numeric value (0-100) representing how well a job description aligns with the resume skills
- **Match_Result**: A JSON object containing the match score and the list of matched skills
- **Orchestrator**: The `main.py` entry point that coordinates scraping, storage, and matching workflows

## Requirements

### Requirement 1: Multi-Site Job Scraping

**User Story:** As a job seeker, I want to scrape job listings from multiple job boards simultaneously, so that I can discover relevant opportunities across platforms without manual searching.

#### Acceptance Criteria

1. WHEN the Scraper is invoked with a Search_Term, THE Scraper SHALL query LinkedIn, Indeed, and Naukri concurrently using the python-jobspy library with the country parameter set to India and results_wanted set to 15 per Job_Board
2. THE Scraper SHALL support the following Search_Terms: "Biomedical Engineer", "Medical Device Engineer", "Research Engineer", "Healthcare AI", "Signal Processing Engineer", "Embedded Systems Engineer", "Python Developer", "IoT Engineer"
3. WHEN a Job_Board returns results, THE Scraper SHALL collect Job_Listings containing at minimum: title, company name, location, job URL, and description
4. IF a Job_Board fails to respond or returns an error, THEN THE Scraper SHALL log an error message indicating the Job_Board name and failure reason, and continue scraping from the remaining Job_Boards without discarding already-collected results
5. IF all Job_Boards return zero results for a Search_Term, THEN THE Scraper SHALL return an empty result set without raising an error

### Requirement 2: Daily Job Storage

**User Story:** As a job seeker, I want scraped jobs saved to CSV files organized by date, so that I can track new listings over time and avoid re-processing old results.

#### Acceptance Criteria

1. WHEN scraping completes for all Search_Terms, THE CSV_Store SHALL save results to a CSV file in the `data/` directory
2. THE CSV_Store SHALL name each file using the format `jobs_YYYY-MM-DD.csv` where the date represents the scraping date, using UTF-8 encoding
3. THE CSV_Store SHALL include the following columns in the CSV: site, title, company, location, job_url, description, date_posted, job_type, and skills, writing an empty string for any field that has no value
4. WHEN multiple Search_Terms produce results, THE CSV_Store SHALL combine all results into a single daily CSV file
5. THE CSV_Store SHALL deduplicate Job_Listings by job_url before writing to the CSV file, retaining the first occurrence encountered
6. IF the `data/` directory does not exist, THEN THE CSV_Store SHALL create the directory before writing
7. IF a CSV file for today's date already exists in the `data/` directory, THEN THE CSV_Store SHALL overwrite the existing file with the new results
8. IF the CSV_Store fails to write the file due to a filesystem error, THEN THE CSV_Store SHALL raise a descriptive error indicating the write failure and the target file path

### Requirement 3: Resume Text Extraction

**User Story:** As a job seeker, I want my resume PDF parsed into structured text, so that the system can identify my skills for job matching.

#### Acceptance Criteria

1. WHEN a resume PDF file path is provided, THE Resume_Parser SHALL extract all text content from the PDF and return it as a single concatenated string with page content separated by newline characters
2. THE Resume_Parser SHALL support multi-page PDF documents of up to 10 pages
3. IF the PDF file does not exist at the specified path, THEN THE Resume_Parser SHALL raise a descriptive error indicating the file was not found
4. IF the PDF file is corrupted or unreadable, THEN THE Resume_Parser SHALL raise a descriptive error indicating the file could not be parsed
5. WHEN text is extracted, THE Resume_Parser SHALL preserve the logical reading order of the document content (top-to-bottom, left-to-right within each page)
6. IF the PDF contains no extractable text content (e.g., scanned image-only document), THEN THE Resume_Parser SHALL raise a descriptive error indicating that no text could be extracted from the file

### Requirement 4: Skills Extraction from Resume

**User Story:** As a job seeker, I want my skills automatically identified from my resume, so that they can be compared against job descriptions.

#### Acceptance Criteria

1. WHEN resume text is provided, THE Resume_Parser SHALL extract a Skills_List from the text content using case-insensitive matching against the skills dictionary
2. THE Resume_Parser SHALL identify skills using keyword matching against a predefined skills dictionary containing at least 50 entries spanning biomedical engineering, software development, and embedded systems domains, supporting both single-word skills (e.g., "python") and multi-word skills (e.g., "signal processing")
3. THE Skills_List SHALL contain individual skill entries as lowercase normalized strings with each entry no longer than 100 characters
4. WHEN a skill appears multiple times in the resume, THE Resume_Parser SHALL include the skill only once in the Skills_List
5. IF no skills from the dictionary are found in the resume text, THEN THE Resume_Parser SHALL return an empty Skills_List

### Requirement 5: Job-Resume Match Scoring

**User Story:** As a job seeker, I want each job scored against my resume, so that I can prioritize applications for the most relevant positions.

#### Acceptance Criteria

1. WHEN a Job_Listing description and a Skills_List are provided, THE Matcher SHALL compute a Match_Score between 0 and 100
2. THE Matcher SHALL calculate the Match_Score as the percentage of Skills_List items found in the Job_Listing description using case-insensitive substring matching, rounded down to the nearest integer
3. THE Matcher SHALL return a Match_Result containing the numeric score and the list of matched skill strings
4. THE Match_Result SHALL follow the format: `{"score": <integer>, "matched_skills": [<list of matched skill strings>]}`
5. IF the Job_Listing description is empty or missing, THEN THE Matcher SHALL return a Match_Score of 0 with an empty matched_skills list
6. IF the Skills_List is empty or missing, THEN THE Matcher SHALL return a Match_Score of 0 with an empty matched_skills list

### Requirement 6: Project Orchestration

**User Story:** As a job seeker, I want a single entry point that runs the full pipeline, so that I can execute scraping, storage, and matching with one command.

#### Acceptance Criteria

1. WHEN `main.py` is executed, THE Orchestrator SHALL run the scraping pipeline for all configured Search_Terms
2. WHEN scraping completes, THE Orchestrator SHALL save results to the CSV_Store
3. WHEN CSV storage completes, THE Orchestrator SHALL run the Matcher against each Job_Listing using the resume at `resume/resume.pdf`
4. WHEN matching completes for all Job_Listings, THE Orchestrator SHALL print a summary to the console showing the total number of jobs scraped, the number of unique jobs after deduplication, and the top 10 jobs by Match_Score with each entry displaying the job title, company name, and Match_Score
5. IF no jobs are scraped across all Search_Terms and Job_Boards, THEN THE Orchestrator SHALL print a message indicating no results were found and exit with exit code 0 without raising an unhandled exception
6. IF the resume file does not exist at `resume/resume.pdf`, THEN THE Orchestrator SHALL print an error message indicating the resume file was not found and exit with exit code 1 without proceeding to the matching step

### Requirement 7: Project File Structure

**User Story:** As a developer, I want the project organized into clear modules, so that the codebase is maintainable and extensible for future features.

#### Acceptance Criteria

1. THE project SHALL use the following directory structure: `data/` for CSV storage, `scraper/` for scraping logic, `resume/` for the resume PDF, `matcher/` for matching logic
2. THE Scraper module SHALL be located at `scraper/scrape_jobs.py` and the `scraper/` directory SHALL contain an `__init__.py` file that exposes the scraping function for import
3. THE Matcher module SHALL be located at `matcher/matcher.py` and the `matcher/` directory SHALL contain an `__init__.py` file that exposes the matching function for import
4. THE Orchestrator entry point SHALL be located at `main.py` in the project root
5. THE resume PDF SHALL be stored at `resume/resume.pdf`
6. WHEN any module under `scraper/` or `matcher/` is imported, THE project SHALL resolve imports without errors when executed from the project root directory
