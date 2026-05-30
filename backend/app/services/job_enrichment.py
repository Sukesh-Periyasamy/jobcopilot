"""Job Enrichment Service — skill extraction and categorization.

Extracts skills from job descriptions and assigns categories
based on title/description keywords. Used during scraping and
for enriching existing jobs.
"""

from __future__ import annotations

import re

# Skills to detect in descriptions
SKILL_KEYWORDS: list[str] = [
    "python", "java", "c++", "matlab", "r", "sql", "javascript",
    "machine learning", "deep learning", "tensorflow", "pytorch",
    "computer vision", "nlp", "natural language processing",
    "medical devices", "iso 13485", "iso 14971", "fda", "ce marking",
    "gmp", "quality systems", "design controls", "dhf", "dhr",
    "biomedical", "signal processing", "image processing",
    "embedded", "firmware", "rtos", "microcontroller", "arm",
    "iot", "wireless", "bluetooth", "wifi",
    "docker", "kubernetes", "aws", "gcp", "azure",
    "mongodb", "postgresql", "mysql", "redis",
    "fastapi", "django", "flask", "node.js", "react",
    "clinical trials", "regulatory", "validation", "verification",
    "raman spectroscopy", "sers", "biosensor", "microfluidics",
    "pcr", "elisa", "immunoassay", "diagnostics",
    "solidworks", "autocad", "ansys", "comsol",
    "labview", "simulink", "verilog", "vhdl",
    "git", "ci/cd", "agile", "scrum",
    "statistics", "data analysis", "pandas", "numpy", "scipy",
]

# Category mapping based on title keywords
CATEGORY_MAP: dict[str, list[str]] = {
    "Medical Device": ["medical device", "medtech", "biomedical engineer", "clinical engineer"],
    "Clinical Research": ["clinical research", "clinical data", "clinical trial", "cra"],
    "Research & Development": ["research associate", "project associate", "r&d", "research scientist", "jrf", "srf"],
    "Healthcare AI": ["healthcare ai", "medical ai", "health informatics", "clinical ai", "medical imaging"],
    "Quality & Regulatory": ["quality engineer", "regulatory affairs", "validation", "verification", "v&v", "qa/qc"],
    "Embedded Systems": ["embedded", "firmware", "microcontroller", "rtos", "fpga"],
    "Diagnostics": ["diagnostics", "biosensor", "spectroscopy", "point-of-care", "ivd"],
    "Software Engineering": ["software engineer", "backend", "frontend", "full stack", "developer"],
    "Data Science": ["data scientist", "data analyst", "machine learning engineer", "ai engineer"],
    "Product Management": ["product manager", "product owner", "program manager"],
    "Internship": ["intern", "internship", "trainee", "apprentice"],
}


def extract_skills(description: str) -> list[str]:
    """Extract skills from a job description.

    Args:
        description: Job description text.

    Returns:
        List of detected skill names (title-cased).
    """
    if not description:
        return []

    desc_lower = description.lower()
    found_skills = []

    for skill in SKILL_KEYWORDS:
        # Use word boundary-like matching for short skills
        if len(skill) <= 3:
            # Short skills need more context (avoid false positives)
            if re.search(rf'\b{re.escape(skill)}\b', desc_lower):
                found_skills.append(skill.upper() if len(skill) <= 3 else skill.title())
        else:
            if skill in desc_lower:
                found_skills.append(skill.title())

    return found_skills[:15]  # Limit to top 15 skills


def categorize_job(title: str, description: str = "") -> str:
    """Assign a category to a job based on title and description.

    Args:
        title: Job title.
        description: Job description (optional).

    Returns:
        Category name string.
    """
    combined = f"{title} {description}".lower()

    # Check each category's keywords
    for category, keywords in CATEGORY_MAP.items():
        for kw in keywords:
            if kw in combined:
                return category

    return "Other"


def enrich_job(job: dict) -> dict:
    """Enrich a job dict with skills and category.

    Args:
        job: Job dictionary with at least title and description.

    Returns:
        Same dict with added 'skills' and 'category' fields.
    """
    title = job.get("title", "")
    description = job.get("description", "")

    job["skills"] = extract_skills(description)
    job["category"] = categorize_job(title, description)

    return job
