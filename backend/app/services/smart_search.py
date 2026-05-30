"""Smart Search Engine v2 for JobCopilot.

Provides weighted multi-field search with synonym expansion,
regex matching, collection boosting, faceted filters, and relevance scoring.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone

from app.database.connection import get_database
from app.services.constants import COLLECTIONS

logger = logging.getLogger(__name__)

# Field weights for scoring
FIELD_WEIGHTS = {
    "title": 10,
    "company": 8,
    "collection": 12,
    "location": 4,
    "description": 3,
}

# Synonym mappings for expanded search
SYNONYMS: dict[str, list[str]] = {
    "biomedical": ["medical technology", "medical device", "healthcare", "diagnostics", "clinical"],
    "medtech": ["medical technology", "medical device", "healthcare technology"],
    "research": ["scientist", "research associate", "project associate", "jrf", "srf", "r&d"],
    "embedded": ["firmware", "microcontroller", "esp32", "stm32", "rtos"],
    "iot": ["internet of things", "connected devices", "smart devices", "edge computing", "wireless sensor"],
    "python": ["django", "flask", "fastapi", "backend developer"],
    "ai": ["machine learning", "deep learning", "artificial intelligence", "computer vision", "nlp"],
    "healthcare": ["medical", "clinical", "health tech", "digital health", "telemedicine"],
    "intern": ["internship", "trainee", "graduate engineer", "fresher"],
    "remote": ["work from home", "wfh", "anywhere", "distributed"],
    "bangalore": ["bengaluru", "karnataka"],
    "gurgaon": ["gurugram"],
    "delhi": ["noida", "new delhi", "ncr"],
}

# Suggestions when no results found
SEARCH_SUGGESTIONS = [
    "Biomedical Engineer",
    "Medical Device",
    "Research Associate",
    "Python Developer",
    "Embedded Systems",
    "Healthcare AI",
    "Abbott",
    "Bangalore",
    "Remote",
    "Internship",
]

MAX_RESULTS = 100


class SmartSearchService:
    """Weighted multi-field search with synonym expansion and multi-keyword support."""

    def search(self, query: str, page: int = 1, page_size: int = 50) -> dict:
        """Perform smart search with weighted scoring.

        Supports multi-keyword queries (e.g., "Abbott Bangalore Research Associate").
        Tokenizes input, expands each token with synonyms, and scores across
        title, company, location, description, and collections.

        Args:
            query: Search query string (can contain multiple keywords).
            page: Page number (1-indexed).
            page_size: Results per page.

        Returns:
            Dict with results, total, page, facets, suggestions.
        """
        if not query or not query.strip():
            return {
                "results": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "suggestions": SEARCH_SUGGESTIONS,
            }

        db = get_database()
        jobs_collection = db["jobs"]

        # Tokenize and expand query
        tokens = self._tokenize_query(query.strip())
        all_search_terms = []
        for token in tokens:
            all_search_terms.extend(self._expand_query(token))

        # Deduplicate
        seen = set()
        search_terms = []
        for t in all_search_terms:
            if t.lower() not in seen:
                seen.add(t.lower())
                search_terms.append(t)

        # Build MongoDB OR query across all fields
        or_conditions = []
        for term in search_terms:
            escaped = re.escape(term)
            or_conditions.append({"title": {"$regex": escaped, "$options": "i"}})
            or_conditions.append({"company": {"$regex": escaped, "$options": "i"}})
            or_conditions.append({"location": {"$regex": escaped, "$options": "i"}})
            or_conditions.append({"description": {"$regex": escaped, "$options": "i"}})

        mongo_query = {"$or": or_conditions}

        # Fetch matching jobs (limit to MAX_RESULTS for scoring)
        cursor = jobs_collection.find(mongo_query, {"_id": 0}).limit(MAX_RESULTS)
        matching_jobs = list(cursor)

        # Score and rank
        scored_jobs = []
        for job in matching_jobs:
            score, breakdown = self._score_job(job, search_terms)
            job["_search_score"] = score
            job["_score_breakdown"] = breakdown
            scored_jobs.append(job)

        # Sort by score descending
        scored_jobs.sort(key=lambda j: j["_search_score"], reverse=True)

        # Paginate
        total = len(scored_jobs)
        start = (page - 1) * page_size
        end = start + page_size
        page_results = scored_jobs[start:end]

        # Format results
        results = [self._format_result(job) for job in page_results]

        # Generate facets from scored results
        facets = self._compute_facets(scored_jobs)

        # Generate suggestions if no results
        suggestions = []
        if not results:
            suggestions = SEARCH_SUGGESTIONS

        return {
            "results": results,
            "total": total,
            "page": page,
            "page_size": page_size,
            "query": query,
            "expanded_terms": search_terms,
            "facets": facets,
            "suggestions": suggestions,
        }

    def _tokenize_query(self, query: str) -> list[str]:
        """Tokenize a multi-keyword query into individual search tokens.

        Handles quoted phrases and splits on spaces.
        Examples:
            'Abbott Bangalore' -> ['Abbott', 'Bangalore']
            'Research Associate' -> ['Research Associate']  (kept as phrase if it matches a known term)
            'Abbott Bangalore Research Associate' -> ['Abbott', 'Bangalore', 'Research Associate']
        """
        query_lower = query.lower()

        # Known multi-word phrases to keep together
        known_phrases = [
            "research associate", "research engineer", "project associate",
            "project assistant", "medical device", "medical technology",
            "healthcare ai", "healthcare technology", "embedded systems",
            "biomedical engineer", "product manager", "machine learning",
            "computer vision", "deep learning", "data scientist",
            "graduate engineer", "research intern", "clinical research",
            "r&d engineer", "full stack", "backend developer",
        ]

        tokens = []
        remaining = query_lower

        # Extract known phrases first
        for phrase in sorted(known_phrases, key=len, reverse=True):
            if phrase in remaining:
                tokens.append(phrase)
                remaining = remaining.replace(phrase, " ").strip()

        # Split remaining by spaces
        for word in remaining.split():
            word = word.strip()
            if word and len(word) > 1:
                tokens.append(word)

        return tokens if tokens else [query]

    def _expand_query(self, query: str) -> list[str]:
        """Expand query with synonyms.

        Returns the original query plus any synonym matches.
        """
        terms = [query]
        query_lower = query.lower()

        # Check each synonym key
        for key, synonyms in SYNONYMS.items():
            if key in query_lower:
                terms.extend(synonyms)

        # Also check if query matches any synonym value
        for key, synonyms in SYNONYMS.items():
            for syn in synonyms:
                if syn in query_lower:
                    terms.append(key)
                    break

        # Deduplicate while preserving order
        seen = set()
        unique_terms = []
        for term in terms:
            if term.lower() not in seen:
                seen.add(term.lower())
                unique_terms.append(term)

        return unique_terms

    def _score_job(self, job: dict, search_terms: list[str]) -> tuple[int, list[str]]:
        """Score a job based on which fields match which terms.

        Higher weight fields contribute more to the score.
        Includes collection matching for domain relevance.

        Returns:
            Tuple of (total_score, score_breakdown_list).
        """
        score = 0
        breakdown: list[str] = []

        title_lower = job.get("title", "").lower()
        company_lower = job.get("company", "").lower()
        location_lower = job.get("location", "").lower()
        description_lower = job.get("description", "").lower()
        combined = f"{title_lower} {description_lower}"

        for term in search_terms:
            term_lower = term.lower()

            # Title match (highest weight)
            if term_lower in title_lower:
                score += FIELD_WEIGHTS["title"]
                breakdown.append(f"+{FIELD_WEIGHTS['title']} title:{term}")

            # Company match
            if term_lower in company_lower:
                score += FIELD_WEIGHTS["company"]
                breakdown.append(f"+{FIELD_WEIGHTS['company']} company:{term}")

            # Location match
            if term_lower in location_lower:
                score += FIELD_WEIGHTS["location"]
                breakdown.append(f"+{FIELD_WEIGHTS['location']} location:{term}")

            # Description match
            if term_lower in description_lower:
                score += FIELD_WEIGHTS["description"]
                breakdown.append(f"+{FIELD_WEIGHTS['description']} description:{term}")

            # Collection match — boost if term matches a collection's keywords
            for collection_def in COLLECTIONS:
                if term_lower in collection_def.name.lower():
                    for kw in collection_def.keywords:
                        if kw.lower() in combined:
                            score += FIELD_WEIGHTS["collection"]
                            breakdown.append(f"+{FIELD_WEIGHTS['collection']} collection:{collection_def.name}")
                            break
                    break
                for kw in collection_def.keywords:
                    if term_lower == kw.lower() and kw.lower() in combined:
                        score += FIELD_WEIGHTS["collection"]
                        breakdown.append(f"+{FIELD_WEIGHTS['collection']} collection:{collection_def.name}")
                        break

        # Freshness bonus
        date_posted = job.get("date_posted", "")
        if date_posted:
            try:
                posted = datetime.strptime(date_posted, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                days_old = (datetime.now(timezone.utc) - posted).days
                if days_old <= 3:
                    score += 3
                    breakdown.append("+3 freshness")
                elif days_old <= 7:
                    score += 2
                    breakdown.append("+2 freshness")
                elif days_old <= 14:
                    score += 1
                    breakdown.append("+1 freshness")
            except (ValueError, TypeError):
                pass

        return score, breakdown

    def _compute_facets(self, scored_jobs: list[dict]) -> dict:
        """Compute faceted filter counts from search results.

        Returns top companies, locations, platforms, and matching collections.
        """
        company_counts: dict[str, int] = {}
        location_counts: dict[str, int] = {}
        platform_counts: dict[str, int] = {}
        collection_counts: dict[str, int] = {}

        for job in scored_jobs:
            # Company facet
            company = job.get("company", "").strip()
            if company:
                company_counts[company] = company_counts.get(company, 0) + 1

            # Location facet
            location = job.get("location", "").strip()
            if location:
                location_counts[location] = location_counts.get(location, 0) + 1

            # Platform facet
            platform = job.get("source_platform", "").strip()
            if platform:
                platform_counts[platform] = platform_counts.get(platform, 0) + 1

            # Collection facet — check which collections this job belongs to
            combined = f"{job.get('title', '')} {job.get('description', '')}".lower()
            for collection_def in COLLECTIONS:
                for kw in collection_def.keywords:
                    if kw.lower() in combined:
                        collection_counts[collection_def.name] = collection_counts.get(collection_def.name, 0) + 1
                        break

        # Sort by count descending, take top 10
        def top_n(counts: dict, n: int = 10) -> list[dict]:
            sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            return [{"name": k, "count": v} for k, v in sorted_items[:n]]

        return {
            "top_companies": top_n(company_counts),
            "top_locations": top_n(location_counts),
            "top_platforms": top_n(platform_counts, 5),
            "top_collections": top_n(collection_counts),
        }

    def _format_result(self, job: dict) -> dict:
        """Format a scored job for the search response."""
        return {
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "job_url": job.get("job_url", ""),
            "date_posted": job.get("date_posted", ""),
            "source_platform": job.get("source_platform", ""),
            "description": job.get("description", "")[:200],
            "search_score": job.get("_search_score", 0),
            "score_breakdown": job.get("_score_breakdown", []),
        }
