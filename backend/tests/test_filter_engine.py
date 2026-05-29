"""Unit tests for the filter engine module."""

import pytest

from app.models.job import FilterCriteria
from app.services.filter_engine import build_query


class TestBuildQueryEmpty:
    """Tests for empty/no criteria scenarios."""

    def test_all_none_returns_empty_dict(self):
        criteria = FilterCriteria()
        assert build_query(criteria) == {}

    def test_all_empty_strings_returns_empty_dict(self):
        criteria = FilterCriteria(
            source="",
            location="",
            company="",
            keyword="",
            job_type="",
            date_from="",
            date_to="",
            search_term="",
        )
        assert build_query(criteria) == {}

    def test_none_values_ignored(self):
        criteria = FilterCriteria(source=None, location=None)
        assert build_query(criteria) == {}


class TestBuildQuerySingleCriteria:
    """Tests for individual filter criteria."""

    def test_source_exact_match_case_insensitive(self):
        criteria = FilterCriteria(source="LinkedIn")
        result = build_query(criteria)
        assert result == {"source": {"$regex": "^LinkedIn$", "$options": "i"}}

    def test_job_type_exact_match_case_insensitive(self):
        criteria = FilterCriteria(job_type="Full-Time")
        result = build_query(criteria)
        assert result == {"job_type": {"$regex": "^Full\\-Time$", "$options": "i"}}

    def test_search_term_exact_match_case_insensitive(self):
        criteria = FilterCriteria(search_term="Python Developer")
        result = build_query(criteria)
        assert result == {
            "search_term": {"$regex": "^Python\\ Developer$", "$options": "i"}
        }

    def test_location_substring_case_insensitive(self):
        criteria = FilterCriteria(location="Bangalore")
        result = build_query(criteria)
        assert result == {"location": {"$regex": "Bangalore", "$options": "i"}}

    def test_company_substring_case_insensitive(self):
        criteria = FilterCriteria(company="Google")
        result = build_query(criteria)
        assert result == {"company": {"$regex": "Google", "$options": "i"}}

    def test_keyword_or_on_title_and_description(self):
        criteria = FilterCriteria(keyword="python")
        result = build_query(criteria)
        assert result == {
            "$or": [
                {"title": {"$regex": "python", "$options": "i"}},
                {"description": {"$regex": "python", "$options": "i"}},
            ]
        }

    def test_date_from_only(self):
        criteria = FilterCriteria(date_from="2024-01-01")
        result = build_query(criteria)
        assert result == {"date_posted": {"$gte": "2024-01-01"}}

    def test_date_to_only(self):
        criteria = FilterCriteria(date_to="2024-12-31")
        result = build_query(criteria)
        assert result == {"date_posted": {"$lte": "2024-12-31"}}

    def test_date_range_both(self):
        criteria = FilterCriteria(date_from="2024-01-01", date_to="2024-06-30")
        result = build_query(criteria)
        assert result == {
            "date_posted": {"$gte": "2024-01-01", "$lte": "2024-06-30"}
        }


class TestBuildQuerySpecialCharacters:
    """Tests for regex escaping of special characters."""

    def test_location_with_special_chars(self):
        criteria = FilterCriteria(location="New York (NY)")
        result = build_query(criteria)
        assert result == {
            "location": {"$regex": "New\\ York\\ \\(NY\\)", "$options": "i"}
        }

    def test_company_with_dot(self):
        criteria = FilterCriteria(company="A.B.C Corp")
        result = build_query(criteria)
        assert result == {
            "company": {"$regex": "A\\.B\\.C\\ Corp", "$options": "i"}
        }

    def test_keyword_with_plus(self):
        criteria = FilterCriteria(keyword="C++")
        result = build_query(criteria)
        assert result == {
            "$or": [
                {"title": {"$regex": "C\\+\\+", "$options": "i"}},
                {"description": {"$regex": "C\\+\\+", "$options": "i"}},
            ]
        }


class TestBuildQueryMultipleCriteria:
    """Tests for combining multiple criteria with AND logic."""

    def test_two_criteria_combined_with_and(self):
        criteria = FilterCriteria(source="linkedin", location="Bangalore")
        result = build_query(criteria)
        assert "$and" in result
        conditions = result["$and"]
        assert len(conditions) == 2
        assert {"source": {"$regex": "^linkedin$", "$options": "i"}} in conditions
        assert {"location": {"$regex": "Bangalore", "$options": "i"}} in conditions

    def test_all_criteria_combined(self):
        criteria = FilterCriteria(
            source="indeed",
            location="Mumbai",
            company="TCS",
            keyword="engineer",
            job_type="full-time",
            date_from="2024-01-01",
            date_to="2024-12-31",
            search_term="Backend Developer",
        )
        result = build_query(criteria)
        assert "$and" in result
        conditions = result["$and"]
        # source + job_type + search_term + location + company + keyword + date_range = 7
        assert len(conditions) == 7

    def test_mixed_none_and_values(self):
        criteria = FilterCriteria(
            source="naukri",
            location=None,
            company="Infosys",
            keyword=None,
            job_type=None,
            date_from=None,
            date_to=None,
            search_term=None,
        )
        result = build_query(criteria)
        assert "$and" in result
        conditions = result["$and"]
        assert len(conditions) == 2
