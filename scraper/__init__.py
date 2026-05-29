"""Scraper package - exposes job scraping utilities."""

from scraper.scrape_jobs import scrape_all_jobs, save_jobs_to_csv

__all__ = ["scrape_all_jobs", "save_jobs_to_csv"]
