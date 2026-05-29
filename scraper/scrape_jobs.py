"""Scraper module that wraps jobspy.scrape_jobs() for configured search terms."""

from __future__ import annotations

import datetime
import logging
import os
from typing import List

import pandas as pd

from jobspy import scrape_jobs

logger = logging.getLogger(__name__)


def scrape_all_jobs(
    search_terms: List[str],
    sites: List[str],
    country: str,
    results_wanted: int,
) -> pd.DataFrame:
    """
    Scrapes jobs for all search terms across all sites.

    Args:
        search_terms: List of role keywords to search for.
        sites: List of job board names (e.g., ["linkedin", "indeed", "naukri"]).
        country: Country code string (e.g., "india").
        results_wanted: Number of results per site per search term.

    Returns:
        Combined DataFrame of all job listings (may contain duplicates).
        Returns an empty DataFrame if all searches yield no results.

    Raises:
        No exceptions raised - errors per search term are logged and skipped.
    """
    all_results: List[pd.DataFrame] = []

    for term in search_terms:
        try:
            df = scrape_jobs(
                site_name=sites,
                search_term=term,
                country_indeed=country,
                results_wanted=results_wanted,
            )
            if df is not None and not df.empty:
                all_results.append(df)
        except Exception as e:
            logger.error(
                "Failed to scrape jobs for search term '%s': %s", term, e
            )

    if all_results:
        return pd.concat(all_results, ignore_index=True)

    return pd.DataFrame()


# Required columns for the CSV output
REQUIRED_CSV_COLUMNS = [
    "site",
    "title",
    "company",
    "location",
    "job_url",
    "description",
    "date_posted",
    "job_type",
    "skills",
]


def save_jobs_to_csv(df: pd.DataFrame, output_dir: str = "data") -> str:
    """
    Deduplicates by job_url and saves to a daily CSV file.

    Args:
        df: DataFrame of job listings.
        output_dir: Directory path for CSV storage.

    Returns:
        The file path of the written CSV.

    Raises:
        IOError: If the file cannot be written.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Deduplicate by job_url, keeping first occurrence
    if "job_url" in df.columns:
        df = df.drop_duplicates(subset=["job_url"], keep="first").copy()
    else:
        df = df.copy()

    # Ensure all required columns exist and fill NaN/None with empty strings
    for col in REQUIRED_CSV_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df[REQUIRED_CSV_COLUMNS] = df[REQUIRED_CSV_COLUMNS].fillna("")

    # Build the output file path with today's date
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    file_path = os.path.join(output_dir, f"jobs_{today_str}.csv")

    # Write to CSV with UTF-8 encoding
    try:
        df.to_csv(file_path, index=False, encoding="utf-8")
    except OSError as e:
        raise IOError(
            f"Failed to write CSV file to '{file_path}': {e}"
        ) from e

    return file_path
