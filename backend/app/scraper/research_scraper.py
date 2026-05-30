"""IIT/NIT/IISc Research Position Scraper.

Scrapes research positions (JRF, SRF, Project Associate, Research Associate)
from Indian research institution job portals. Uses publicly available
RSS feeds and job listing pages.

Note: This scraper targets publicly accessible job listing pages.
Some institutions may require additional handling.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

import httpx

from app.models.job import JobRecord, ScrapeResult

logger = logging.getLogger(__name__)

# Known research institution career page URLs
# These are publicly accessible job listing endpoints
RESEARCH_PORTALS = [
    {
        "name": "IISc Bangalore",
        "url": "https://iisc.ac.in/opportunities/",
        "type": "page",
    },
    {
        "name": "IIT Madras",
        "url": "https://research.iitm.ac.in/",
        "type": "page",
    },
    {
        "name": "IIT Bombay",
        "url": "https://www.ircc.iitb.ac.in/IRCC-Webpage/rnd/HRMSSearchResult.jsp",
        "type": "page",
    },
    {
        "name": "IIT Delhi",
        "url": "https://home.iitd.ac.in/jobs-iitd.php",
        "type": "page",
    },
    {
        "name": "IIT Hyderabad",
        "url": "https://iith.ac.in/careers/",
        "type": "page",
    },
    {
        "name": "IIT Jodhpur",
        "url": "https://iitj.ac.in/uploaded_docs/Recruitment/",
        "type": "page",
    },
]

# Research position keywords to look for
RESEARCH_KEYWORDS = [
    "JRF", "SRF", "Research Associate", "Project Associate",
    "Project Assistant", "Research Scientist", "Research Fellow",
    "Project Scientist", "Research Assistant", "Young Professional",
]

# Salary ranges for common positions (approximate)
SALARY_ESTIMATES = {
    "JRF": "INR 31,000 + HRA",
    "SRF": "INR 35,000 + HRA",
    "Research Associate": "INR 47,000 + HRA",
    "Project Associate": "INR 25,000 - 35,000",
    "Project Assistant": "INR 20,000 - 31,000",
}


def scrape_research_institutions() -> ScrapeResult:
    """Attempt to scrape research positions from IIT/IISc portals.

    This is a best-effort scraper. Many institution pages have
    varying formats and may not always be parseable. Jobs that
    can't be extracted are logged and skipped.

    Returns:
        ScrapeResult with collected jobs and any errors.
    """
    all_jobs: list[JobRecord] = []
    all_errors: list[str] = []

    now_iso = datetime.now(timezone.utc).isoformat()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    client = httpx.Client(timeout=30.0, follow_redirects=True)

    for portal in RESEARCH_PORTALS:
        try:
            logger.info("Checking research portal: %s", portal["name"])
            response = client.get(portal["url"])

            if response.status_code != 200:
                logger.warning(
                    "Portal %s returned status %d",
                    portal["name"],
                    response.status_code,
                )
                continue

            # Extract text content
            text = response.text

            # Look for research position keywords in the page
            found_positions = []
            for keyword in RESEARCH_KEYWORDS:
                # Find lines containing the keyword
                pattern = re.compile(
                    rf".*{re.escape(keyword)}.*",
                    re.IGNORECASE | re.MULTILINE,
                )
                matches = pattern.findall(text)
                for match in matches[:5]:  # Limit per keyword
                    # Clean HTML tags
                    clean = re.sub(r"<[^>]+>", " ", match).strip()
                    clean = re.sub(r"\s+", " ", clean)
                    if len(clean) > 20 and len(clean) < 500:
                        found_positions.append((keyword, clean))

            # Create job records from found positions
            seen_titles = set()
            for keyword, description in found_positions:
                # Generate a title from the keyword and institution
                title = f"{keyword} - {portal['name']}"
                if title in seen_titles:
                    continue
                seen_titles.add(title)

                # Estimate salary
                salary = SALARY_ESTIMATES.get(keyword, "")

                job = JobRecord(
                    title=title,
                    company=portal["name"],
                    location="India",
                    source="research_portal",
                    job_url=portal["url"],
                    description=description[:500],
                    job_type="Research",
                    salary=salary,
                    date_posted=today,
                    search_term="Research",
                    source_type="research_scraper",
                    source_platform="institution",
                    created_at=now_iso,
                    updated_at=now_iso,
                )
                all_jobs.append(job)

            logger.info(
                "Portal %s: found %d positions",
                portal["name"],
                len(seen_titles),
            )

        except Exception as exc:
            error_msg = f"Error scraping {portal['name']}: {exc}"
            logger.error(error_msg)
            all_errors.append(error_msg)

    client.close()

    logger.info(
        "Research scraper complete: %d jobs, %d errors",
        len(all_jobs),
        len(all_errors),
    )

    return ScrapeResult(jobs=all_jobs, errors=all_errors)
