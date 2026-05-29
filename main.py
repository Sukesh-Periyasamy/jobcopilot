"""Job Copilot - Orchestrator entry point.

Runs the full pipeline: scrape → store → parse resume → extract skills → match → display.
"""

import os
import sys

from scraper import scrape_all_jobs, save_jobs_to_csv
from matcher import extract_resume_text, extract_skills, compute_match, SKILLS_DICTIONARY

# Configuration constants
SEARCH_TERMS = [
    "Biomedical Engineer",
    "Medical Device Engineer",
    "Research Engineer",
    "Healthcare AI",
    "Signal Processing Engineer",
    "Embedded Systems Engineer",
    "Python Developer",
    "IoT Engineer",
]

SITES = ["linkedin", "indeed", "naukri"]
COUNTRY = "india"
RESULTS_WANTED = 15
RESUME_PATH = "resume/resume.pdf"
OUTPUT_DIR = "data"


def main() -> None:
    """
    Entry point that runs the full pipeline:
    1. Scrape jobs for all search terms
    2. Deduplicate and save to CSV
    3. Parse resume and extract skills
    4. Score each job against skills
    5. Print summary with top 10 matches

    Exit codes:
        0: Success (including no results found)
        1: Resume file not found
    """
    # Check if resume file exists
    if not os.path.exists(RESUME_PATH):
        print(f"Error: Resume file not found at '{RESUME_PATH}'")
        sys.exit(1)

    # Scrape jobs from all configured boards and search terms
    print(f"Scraping jobs for {len(SEARCH_TERMS)} search terms across {SITES}...")
    jobs_df = scrape_all_jobs(
        search_terms=SEARCH_TERMS,
        sites=SITES,
        country=COUNTRY,
        results_wanted=RESULTS_WANTED,
    )

    total_jobs_scraped = len(jobs_df)

    # If no jobs scraped, exit gracefully
    if jobs_df.empty:
        print("No results found across all search terms and job boards.")
        sys.exit(0)

    # Save to CSV (deduplicates by job_url)
    csv_path = save_jobs_to_csv(jobs_df, OUTPUT_DIR)
    unique_jobs_df = jobs_df.drop_duplicates(subset=["job_url"], keep="first") if "job_url" in jobs_df.columns else jobs_df
    unique_jobs_count = len(unique_jobs_df)
    print(f"Saved {unique_jobs_count} unique jobs to {csv_path}")

    # Parse resume and extract skills
    resume_text = extract_resume_text(RESUME_PATH)
    skills = extract_skills(resume_text, SKILLS_DICTIONARY)
    print(f"Extracted {len(skills)} skills from resume.")

    # Score each job against resume skills
    results = []
    for idx, row in unique_jobs_df.iterrows():
        description = row.get("description", "") or ""
        title = row.get("title", "") or ""
        company = row.get("company", "") or ""
        match_result = compute_match(description, skills)
        results.append({
            "title": title,
            "company": company,
            "score": match_result["score"],
            "matched_skills": match_result["matched_skills"],
        })

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)

    # Print summary
    print("\n" + "=" * 60)
    print("JOB COPILOT SUMMARY")
    print("=" * 60)
    print(f"Total jobs scraped: {total_jobs_scraped}")
    print(f"Unique jobs after dedup: {unique_jobs_count}")
    print(f"\nTop 10 matches by score:")
    print("-" * 60)

    for i, result in enumerate(results[:10], start=1):
        print(f"  {i:2d}. {result['title']:<40} | {result['company']:<20} | Score: {result['score']}%")

    print("-" * 60)


if __name__ == "__main__":
    main()
