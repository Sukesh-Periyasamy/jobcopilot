"""Resume parser and job matching module."""

import math
import os

from PyPDF2 import PdfReader


MAX_PAGES = 10


def extract_resume_text(pdf_path: str) -> str:
    """
    Extracts all text from a PDF resume file.

    Args:
        pdf_path: Path to the resume PDF file.

    Returns:
        Concatenated text from all pages (up to 10), separated by newlines.

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        ValueError: If the PDF is corrupted/unreadable or contains no extractable text.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Resume PDF not found: {pdf_path}")

    try:
        reader = PdfReader(pdf_path)
    except Exception as e:
        raise ValueError(f"PDF file is corrupted or unreadable: {pdf_path}") from e

    pages_to_read = min(len(reader.pages), MAX_PAGES)
    page_texts = []

    for i in range(pages_to_read):
        try:
            text = reader.pages[i].extract_text()
        except Exception as e:
            raise ValueError(
                f"Failed to extract text from page {i + 1} of PDF: {pdf_path}"
            ) from e
        if text:
            page_texts.append(text)

    if not page_texts:
        raise ValueError(
            f"No extractable text found in PDF: {pdf_path}. "
            "The file may be a scanned image-only document."
        )

    return "\n".join(page_texts)


# Skills dictionary covering biomedical engineering, software development,
# and embedded systems domains (50+ entries)
SKILLS_DICTIONARY: list[str] = [
    # Biomedical Engineering
    "biomedical engineering",
    "medical devices",
    "signal processing",
    "fda regulations",
    "clinical trials",
    "biomechanics",
    "bioinformatics",
    "medical imaging",
    "regulatory affairs",
    "quality assurance",
    "good manufacturing practices",
    "biocompatibility",
    "tissue engineering",
    "prosthetics",
    "rehabilitation engineering",
    "electrophysiology",
    "ultrasound",
    "mri",
    "eeg",
    "ecg",
    # Software Development
    "python",
    "machine learning",
    "deep learning",
    "tensorflow",
    "pytorch",
    "docker",
    "git",
    "sql",
    "java",
    "javascript",
    "react",
    "node.js",
    "aws",
    "azure",
    "kubernetes",
    "ci/cd",
    "rest api",
    "data analysis",
    "computer vision",
    "natural language processing",
    "pandas",
    "numpy",
    "scikit-learn",
    "flask",
    "django",
    # Embedded Systems
    "embedded systems",
    "iot",
    "firmware",
    "rtos",
    "pcb design",
    "arduino",
    "raspberry pi",
    "fpga",
    "verilog",
    "c programming",
    "c++",
    "microcontrollers",
    "arm",
    "uart",
    "spi",
    "i2c",
    "bluetooth",
    "zigbee",
    "can bus",
    "linux",
]


def extract_skills(resume_text: str, skills_dict: list[str]) -> list[str]:
    """
    Extracts skills from resume text using case-insensitive substring matching.

    Args:
        resume_text: Full text content of the resume.
        skills_dict: List of known skill keywords to match against.

    Returns:
        Deduplicated list of matched skills as lowercase strings (each ≤ 100 chars).
        Returns empty list if no skills match.
    """
    if not resume_text or not skills_dict:
        return []

    text_lower = resume_text.lower()
    matched: list[str] = []
    seen: set[str] = set()

    for skill in skills_dict:
        skill_lower = skill.lower()[:100]
        if skill_lower not in seen and skill_lower in text_lower:
            matched.append(skill_lower)
            seen.add(skill_lower)

    return matched


def compute_match(description: str, skills: list[str]) -> dict:
    """
    Computes a match score between a job description and a skills list.

    Args:
        description: Job listing description text.
        skills: List of skill strings extracted from resume.

    Returns:
        Dict with format: {"score": int, "matched_skills": list[str]}
        Score is percentage (0-100) of skills found in description, rounded down.
    """
    if not description or not skills:
        return {"score": 0, "matched_skills": []}

    description_lower = description.lower()
    matched_skills: list[str] = []

    for skill in skills:
        if skill.lower() in description_lower:
            matched_skills.append(skill)

    score = math.floor(len(matched_skills) / len(skills) * 100)

    return {"score": score, "matched_skills": matched_skills}
