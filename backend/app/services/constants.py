"""Constants for the Career Opportunity Radar service layer.

Defines collection definitions, internship keywords, and research institutions
used by the Collection Engine, Internship Tracker, and Research Tracker services.
"""

from dataclasses import dataclass


@dataclass
class CollectionDefinition:
    """A named grouping of jobs defined by keyword matching."""

    name: str
    keywords: list[str]


COLLECTIONS: list[CollectionDefinition] = [
    CollectionDefinition("Medical Technology", ["medical technology", "medtech", "medical device", "clinical engineering"]),
    CollectionDefinition("Biomedical Engineering", ["biomedical", "biomed", "bioengineering", "biomechanics"]),
    CollectionDefinition("Healthcare Technology", ["healthtech", "health tech", "healthcare technology", "digital health", "telemedicine"]),
    CollectionDefinition("Medical Devices", ["medical device", "surgical instrument", "diagnostic equipment", "implant"]),
    CollectionDefinition("Research Engineering", ["research engineer", "R&D engineer", "research scientist", "research associate"]),
    CollectionDefinition("Embedded Systems", ["embedded", "firmware", "RTOS", "microcontroller", "ARM"]),
    CollectionDefinition("IoT", ["IoT", "internet of things", "connected devices", "smart devices", "edge computing"]),
    CollectionDefinition("Python Development", ["python", "django", "flask", "fastapi", "pandas"]),
    CollectionDefinition("Product Management", ["product manager", "product owner", "product management", "product strategy"]),
    CollectionDefinition("Healthcare AI", ["healthcare AI", "medical AI", "clinical AI", "health informatics", "medical imaging AI"]),
    CollectionDefinition("Diagnostics and Biosensors", ["diagnostics", "biosensor", "point-of-care", "lateral flow", "PCR", "immunoassay"]),
]

INTERNSHIP_KEYWORDS: list[str] = [
    "Internship",
    "Trainee",
    "Graduate Engineer",
    "Research Intern",
    "Project Associate",
    "Project Assistant",
    "JRF",
    "SRF",
    "RA",
    "Summer Internship",
    "Industrial Trainee",
    "Associate Engineer",
    "Graduate Trainee",
    "Young Professional",
    "Project Engineer",
]

RESEARCH_INSTITUTIONS: list[str] = [
    "IISc",
    "DRDO",
    "C-DAC",
    "AIIMS",
    "IITs",
    "CSIR Labs",
    "ISRO",
    "BARC",
    "THSTI",
    "NIBMG",
    "ICMR",
    "NIMHANS",
    "SCTIMST",
]
