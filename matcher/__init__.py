"""Matcher package - resume parsing and job matching utilities."""

from matcher.matcher import (
    SKILLS_DICTIONARY,
    compute_match,
    extract_resume_text,
    extract_skills,
)

__all__ = [
    "extract_resume_text",
    "extract_skills",
    "compute_match",
    "SKILLS_DICTIONARY",
]
