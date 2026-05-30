"""Unit tests for the filter engine module."""

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

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


class TestBuildQuerySourceType:
    """Tests for source_type filter criteria (Requirement 4.1)."""

    def test_source_type_jobhive_case_insensitive(self):
        """source_type='jobhive' produces case-insensitive exact match regex."""
        criteria = FilterCriteria(source_type="jobhive")
        result = build_query(criteria)
        assert result == {"source_type": {"$regex": "^jobhive$", "$options": "i"}}

    def test_source_type_jobspy_case_insensitive(self):
        """source_type='jobspy' produces case-insensitive exact match regex."""
        criteria = FilterCriteria(source_type="jobspy")
        result = build_query(criteria)
        assert result == {"source_type": {"$regex": "^jobspy$", "$options": "i"}}

    def test_source_type_mixed_case(self):
        """source_type with mixed case is passed through (regex handles matching)."""
        criteria = FilterCriteria(source_type="JobHive")
        result = build_query(criteria)
        assert result == {"source_type": {"$regex": "^JobHive$", "$options": "i"}}

    def test_source_type_empty_string_ignored(self):
        """Empty source_type is treated as no filter."""
        criteria = FilterCriteria(source_type="")
        assert build_query(criteria) == {}

    def test_source_type_none_ignored(self):
        """None source_type is treated as no filter."""
        criteria = FilterCriteria(source_type=None)
        assert build_query(criteria) == {}


class TestBuildQuerySourcePlatform:
    """Tests for source_platform filter criteria (Requirements 4.2, 4.3)."""

    def test_source_platform_ats_umbrella_returns_in_query(self):
        """source_platform='ats' returns $in with all 5 ATS platforms (Requirement 4.3)."""
        criteria = FilterCriteria(source_platform="ats")
        result = build_query(criteria)
        expected_platforms = ["greenhouse", "lever", "ashby", "workday", "successfactors"]
        assert result == {"source_platform": {"$in": expected_platforms}}

    def test_source_platform_ats_case_insensitive_trigger(self):
        """source_platform='ATS' (uppercase) also triggers the umbrella $in query."""
        criteria = FilterCriteria(source_platform="ATS")
        result = build_query(criteria)
        expected_platforms = ["greenhouse", "lever", "ashby", "workday", "successfactors"]
        assert result == {"source_platform": {"$in": expected_platforms}}

    def test_source_platform_ats_mixed_case(self):
        """source_platform='Ats' (mixed case) also triggers the umbrella $in query."""
        criteria = FilterCriteria(source_platform="Ats")
        result = build_query(criteria)
        expected_platforms = ["greenhouse", "lever", "ashby", "workday", "successfactors"]
        assert result == {"source_platform": {"$in": expected_platforms}}

    def test_source_platform_linkedin_regex(self):
        """source_platform='linkedin' produces case-insensitive exact match regex."""
        criteria = FilterCriteria(source_platform="linkedin")
        result = build_query(criteria)
        assert result == {"source_platform": {"$regex": "^linkedin$", "$options": "i"}}

    def test_source_platform_greenhouse_regex(self):
        """source_platform='greenhouse' produces case-insensitive exact match regex."""
        criteria = FilterCriteria(source_platform="greenhouse")
        result = build_query(criteria)
        assert result == {"source_platform": {"$regex": "^greenhouse$", "$options": "i"}}

    def test_source_platform_workday_regex(self):
        """source_platform='workday' produces case-insensitive exact match regex."""
        criteria = FilterCriteria(source_platform="workday")
        result = build_query(criteria)
        assert result == {"source_platform": {"$regex": "^workday$", "$options": "i"}}

    def test_source_platform_empty_string_ignored(self):
        """Empty source_platform is treated as no filter."""
        criteria = FilterCriteria(source_platform="")
        assert build_query(criteria) == {}

    def test_source_platform_none_ignored(self):
        """None source_platform is treated as no filter."""
        criteria = FilterCriteria(source_platform=None)
        assert build_query(criteria) == {}


class TestBuildQueryCombinedSourceFilters:
    """Tests for combined source_type + source_platform + existing filters (Requirement 4.4, 4.6)."""

    def test_source_type_and_source_platform_combined(self):
        """source_type + source_platform produces $and with both conditions."""
        criteria = FilterCriteria(source_type="jobhive", source_platform="greenhouse")
        result = build_query(criteria)
        assert "$and" in result
        conditions = result["$and"]
        assert len(conditions) == 2
        assert {"source_type": {"$regex": "^jobhive$", "$options": "i"}} in conditions
        assert {"source_platform": {"$regex": "^greenhouse$", "$options": "i"}} in conditions

    def test_source_type_and_source_platform_ats_combined(self):
        """source_type + source_platform='ats' produces $and with type regex and $in."""
        criteria = FilterCriteria(source_type="jobhive", source_platform="ats")
        result = build_query(criteria)
        assert "$and" in result
        conditions = result["$and"]
        assert len(conditions) == 2
        assert {"source_type": {"$regex": "^jobhive$", "$options": "i"}} in conditions
        expected_platforms = ["greenhouse", "lever", "ashby", "workday", "successfactors"]
        assert {"source_platform": {"$in": expected_platforms}} in conditions

    def test_source_type_and_location_combined(self):
        """source_type + location produces $and with both conditions."""
        criteria = FilterCriteria(source_type="jobhive", location="Bangalore")
        result = build_query(criteria)
        assert "$and" in result
        conditions = result["$and"]
        assert len(conditions) == 2
        assert {"source_type": {"$regex": "^jobhive$", "$options": "i"}} in conditions
        assert {"location": {"$regex": "Bangalore", "$options": "i"}} in conditions

    def test_source_platform_and_location_combined(self):
        """source_platform + location produces $and with both conditions."""
        criteria = FilterCriteria(source_platform="linkedin", location="Mumbai")
        result = build_query(criteria)
        assert "$and" in result
        conditions = result["$and"]
        assert len(conditions) == 2
        assert {"source_platform": {"$regex": "^linkedin$", "$options": "i"}} in conditions
        assert {"location": {"$regex": "Mumbai", "$options": "i"}} in conditions

    def test_source_type_source_platform_and_location_all_combined(self):
        """source_type + source_platform + location produces $and with all three."""
        criteria = FilterCriteria(
            source_type="jobhive", source_platform="workday", location="Delhi"
        )
        result = build_query(criteria)
        assert "$and" in result
        conditions = result["$and"]
        assert len(conditions) == 3
        assert {"source_type": {"$regex": "^jobhive$", "$options": "i"}} in conditions
        assert {"source_platform": {"$regex": "^workday$", "$options": "i"}} in conditions
        assert {"location": {"$regex": "Delhi", "$options": "i"}} in conditions

    def test_all_filters_including_new_source_fields(self):
        """All criteria including source_type and source_platform combined."""
        criteria = FilterCriteria(
            source="indeed",
            location="Mumbai",
            company="TCS",
            keyword="engineer",
            job_type="full-time",
            date_from="2024-01-01",
            date_to="2024-12-31",
            search_term="Backend Developer",
            source_type="jobspy",
            source_platform="indeed",
        )
        result = build_query(criteria)
        assert "$and" in result
        conditions = result["$and"]
        # source + source_type + source_platform + job_type + search_term + location + company + keyword + date_range = 9
        assert len(conditions) == 9


class TestBuildQueryBackwardCompatibility:
    """Tests for backward compatibility of existing source filter (Requirement 4.6)."""

    def test_existing_source_filter_unchanged(self):
        """The existing 'source' filter still works as case-insensitive exact match."""
        criteria = FilterCriteria(source="LinkedIn")
        result = build_query(criteria)
        assert result == {"source": {"$regex": "^LinkedIn$", "$options": "i"}}

    def test_source_filter_with_new_source_platform_coexist(self):
        """Old 'source' filter and new 'source_platform' can coexist in $and."""
        criteria = FilterCriteria(source="LinkedIn", source_platform="linkedin")
        result = build_query(criteria)
        assert "$and" in result
        conditions = result["$and"]
        assert len(conditions) == 2
        assert {"source": {"$regex": "^LinkedIn$", "$options": "i"}} in conditions
        assert {"source_platform": {"$regex": "^linkedin$", "$options": "i"}} in conditions

    def test_source_filter_with_source_type_coexist(self):
        """Old 'source' filter and new 'source_type' can coexist in $and."""
        criteria = FilterCriteria(source="indeed", source_type="jobspy")
        result = build_query(criteria)
        assert "$and" in result
        conditions = result["$and"]
        assert len(conditions) == 2
        assert {"source": {"$regex": "^indeed$", "$options": "i"}} in conditions
        assert {"source_type": {"$regex": "^jobspy$", "$options": "i"}} in conditions


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


# Feature: jobcopilot-v1.1-upgrade, Property 5: Source Filter Correctness
# Validates: Requirements 4.1, 4.2, 4.3

from hypothesis import given, settings, assume
from hypothesis import strategies as st


ATS_PLATFORMS = ["greenhouse", "lever", "ashby", "workday", "successfactors"]


class TestSourceFilterCorrectnessProperty:
    """Property test: Source Filter Correctness.

    For any source_type or source_platform filter value (including the special
    "ats" umbrella value), the query produced by build_query SHALL contain the
    correct MongoDB condition matching only records with the specified criterion.

    **Validates: Requirements 4.1, 4.2, 4.3**
    """

    @settings(max_examples=100)
    @given(
        source_type=st.sampled_from(["jobspy", "jobhive", "JOBSPY", "JobHive"])
    )
    def test_source_type_filter_produces_regex_condition(self, source_type: str):
        """When source_type is set, the query contains a case-insensitive regex
        condition that matches exactly the given source_type value."""
        criteria = FilterCriteria(source_type=source_type)
        query = build_query(criteria)

        # Query should have a source_type condition with regex for exact match
        assert "source_type" in query
        condition = query["source_type"]
        assert "$regex" in condition
        assert "$options" in condition
        assert condition["$options"] == "i"
        # The regex should be anchored for exact match
        assert condition["$regex"].startswith("^")
        assert condition["$regex"].endswith("$")
        # The regex should contain the escaped source_type value
        import re
        expected_regex = f"^{re.escape(source_type)}$"
        assert condition["$regex"] == expected_regex

    @settings(max_examples=100)
    @given(
        source_platform=st.sampled_from(["linkedin", "indeed", "greenhouse", "workday"])
    )
    def test_source_platform_filter_produces_regex_condition(self, source_platform: str):
        """When source_platform is set to a specific platform (not 'ats'),
        the query contains a case-insensitive regex condition for exact match."""
        criteria = FilterCriteria(source_platform=source_platform)
        query = build_query(criteria)

        # Query should have a source_platform condition with regex
        assert "source_platform" in query
        condition = query["source_platform"]
        assert "$regex" in condition
        assert "$options" in condition
        assert condition["$options"] == "i"
        # The regex should be anchored for exact match
        assert condition["$regex"].startswith("^")
        assert condition["$regex"].endswith("$")
        import re
        expected_regex = f"^{re.escape(source_platform)}$"
        assert condition["$regex"] == expected_regex

    @settings(max_examples=100)
    @given(
        ats_value=st.sampled_from(["ats", "ATS"])
    )
    def test_ats_umbrella_filter_produces_in_condition(self, ats_value: str):
        """When source_platform is 'ats' (case-insensitive), the query contains
        a $in condition with exactly the 5 ATS platforms."""
        criteria = FilterCriteria(source_platform=ats_value)
        query = build_query(criteria)

        # Query should have a source_platform condition with $in
        assert "source_platform" in query
        condition = query["source_platform"]
        assert "$in" in condition
        # The $in list should contain exactly the 5 ATS platforms
        in_list = condition["$in"]
        assert set(in_list) == set(ATS_PLATFORMS)
        assert len(in_list) == 5


# Feature: jobcopilot-v1.1-upgrade, Property 6: Filter Composition AND Logic


def _count_expected_conditions(criteria: FilterCriteria) -> int:
    """Count the number of conditions build_query should produce for given criteria.

    Each non-None/non-empty field adds one condition, except date_from and date_to
    which together produce a single date_posted condition.
    """
    count = 0
    # Fields that each produce one condition when truthy
    single_fields = [
        criteria.source,
        criteria.location,
        criteria.company,
        criteria.keyword,
        criteria.job_type,
        criteria.search_term,
        criteria.source_type,
        criteria.source_platform,
    ]
    for field_val in single_fields:
        if field_val:
            count += 1

    # date_from and date_to together produce at most one condition
    if criteria.date_from or criteria.date_to:
        count += 1

    return count


# Strategy for non-empty filter field values
_non_empty_text = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z"), blacklist_characters="\x00"),
    min_size=1,
    max_size=30,
)

# Strategy for optional filter field (either None or a non-empty string)
_optional_field = st.one_of(st.none(), _non_empty_text)

# Strategy for source_platform including the special "ats" umbrella value
_optional_source_platform = st.one_of(
    st.none(),
    st.sampled_from(["linkedin", "indeed", "naukri", "google", "workday", "greenhouse", "lever", "ashby", "successfactors", "ats"]),
)

# Strategy for source_type
_optional_source_type = st.one_of(
    st.none(),
    st.sampled_from(["jobspy", "jobhive"]),
)

# Strategy for date strings (YYYY-MM-DD format)
_optional_date = st.one_of(
    st.none(),
    st.dates().map(lambda d: d.isoformat()),
)


@st.composite
def filter_criteria_with_multiple_fields(draw):
    """Generate FilterCriteria with at least 2 non-None fields set."""
    criteria = FilterCriteria(
        source=draw(_optional_field),
        location=draw(_optional_field),
        company=draw(_optional_field),
        keyword=draw(_optional_field),
        job_type=draw(_optional_field),
        date_from=draw(_optional_date),
        date_to=draw(_optional_date),
        search_term=draw(_optional_field),
        source_type=draw(_optional_source_type),
        source_platform=draw(_optional_source_platform),
    )
    # Ensure at least 2 conditions will be generated
    assume(_count_expected_conditions(criteria) >= 2)
    return criteria


class TestFilterCompositionANDLogicProperty:
    """Property 6: Filter Composition AND Logic.

    Validates: Requirements 4.4

    For any combination of filter criteria with 2+ fields set,
    the query uses $and to combine them, the number of conditions
    matches the number of active criteria, and each condition
    corresponds to one of the set criteria fields.
    """

    @given(criteria=filter_criteria_with_multiple_fields())
    @settings(max_examples=100)
    def test_multi_criteria_uses_and_with_correct_count(self, criteria: FilterCriteria):
        """When multiple criteria are set, the query contains $and with matching condition count."""
        query = build_query(criteria)
        expected_count = _count_expected_conditions(criteria)

        # With 2+ conditions, query must use $and
        assert "$and" in query, f"Expected $and in query for {expected_count} conditions, got: {query}"

        # The number of conditions in $and must match the number of non-None criteria
        conditions = query["$and"]
        assert len(conditions) == expected_count, (
            f"Expected {expected_count} conditions in $and, got {len(conditions)}"
        )

    @given(criteria=filter_criteria_with_multiple_fields())
    @settings(max_examples=100)
    def test_each_and_condition_corresponds_to_a_set_field(self, criteria: FilterCriteria):
        """Each condition in $and corresponds to one of the set criteria fields."""
        query = build_query(criteria)
        conditions = query["$and"]

        # Collect the MongoDB field names referenced in each condition
        referenced_fields = set()
        for cond in conditions:
            # Each condition is a dict with one key (the field or $or)
            keys = list(cond.keys())
            assert len(keys) == 1, f"Expected single-key condition, got: {cond}"
            referenced_fields.add(keys[0])

        # Build expected field set based on which criteria are set
        expected_fields = set()
        if criteria.source:
            expected_fields.add("source")
        if criteria.location:
            expected_fields.add("location")
        if criteria.company:
            expected_fields.add("company")
        if criteria.keyword:
            expected_fields.add("$or")  # keyword uses $or on title/description
        if criteria.job_type:
            expected_fields.add("job_type")
        if criteria.search_term:
            expected_fields.add("search_term")
        if criteria.source_type:
            expected_fields.add("source_type")
        if criteria.source_platform:
            expected_fields.add("source_platform")
        if criteria.date_from or criteria.date_to:
            expected_fields.add("date_posted")

        assert referenced_fields == expected_fields, (
            f"Expected fields {expected_fields}, got {referenced_fields}"
        )
