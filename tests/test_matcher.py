"""Unit tests for the compute_match() function in matcher/matcher.py."""

import math

from matcher.matcher import compute_match


class TestComputeMatchEdgeCases:
    """Tests for edge cases: empty/None inputs."""

    def test_empty_description_returns_zero(self):
        result = compute_match("", ["python", "java"])
        assert result == {"score": 0, "matched_skills": []}

    def test_none_description_returns_zero(self):
        result = compute_match(None, ["python", "java"])
        assert result == {"score": 0, "matched_skills": []}

    def test_empty_skills_returns_zero(self):
        result = compute_match("We need a python developer", [])
        assert result == {"score": 0, "matched_skills": []}

    def test_none_skills_returns_zero(self):
        result = compute_match("We need a python developer", None)
        assert result == {"score": 0, "matched_skills": []}

    def test_both_empty_returns_zero(self):
        result = compute_match("", [])
        assert result == {"score": 0, "matched_skills": []}


class TestComputeMatchScoring:
    """Tests for score calculation logic."""

    def test_all_skills_matched_returns_100(self):
        description = "We need python and java developers"
        skills = ["python", "java"]
        result = compute_match(description, skills)
        assert result["score"] == 100
        assert set(result["matched_skills"]) == {"python", "java"}

    def test_no_skills_matched_returns_zero(self):
        description = "We need a marketing specialist"
        skills = ["python", "java", "docker"]
        result = compute_match(description, skills)
        assert result["score"] == 0
        assert result["matched_skills"] == []

    def test_partial_match_uses_floor(self):
        # 1 out of 3 = 33.33... -> floor = 33
        description = "Looking for python experience"
        skills = ["python", "java", "docker"]
        result = compute_match(description, skills)
        assert result["score"] == 33
        assert result["matched_skills"] == ["python"]

    def test_two_of_three_match_uses_floor(self):
        # 2 out of 3 = 66.66... -> floor = 66
        description = "We need python and docker skills"
        skills = ["python", "java", "docker"]
        result = compute_match(description, skills)
        assert result["score"] == 66
        assert set(result["matched_skills"]) == {"python", "docker"}

    def test_score_is_integer(self):
        description = "python java docker kubernetes"
        skills = ["python", "java", "docker", "kubernetes", "react", "angular", "vue"]
        result = compute_match(description, skills)
        assert isinstance(result["score"], int)
        # 4/7 = 57.14... -> floor = 57
        assert result["score"] == 57


class TestComputeMatchCaseInsensitive:
    """Tests for case-insensitive matching."""

    def test_uppercase_description_matches(self):
        description = "PYTHON AND JAVA DEVELOPERS NEEDED"
        skills = ["python", "java"]
        result = compute_match(description, skills)
        assert result["score"] == 100
        assert set(result["matched_skills"]) == {"python", "java"}

    def test_mixed_case_skills_match(self):
        description = "we use python and docker"
        skills = ["Python", "Docker"]
        result = compute_match(description, skills)
        assert result["score"] == 100
        assert set(result["matched_skills"]) == {"Python", "Docker"}

    def test_multi_word_skill_case_insensitive(self):
        description = "Experience with Machine Learning required"
        skills = ["machine learning"]
        result = compute_match(description, skills)
        assert result["score"] == 100
        assert result["matched_skills"] == ["machine learning"]


class TestComputeMatchReturnFormat:
    """Tests for return value format."""

    def test_returns_dict_with_score_and_matched_skills(self):
        result = compute_match("python developer", ["python"])
        assert "score" in result
        assert "matched_skills" in result
        assert isinstance(result["score"], int)
        assert isinstance(result["matched_skills"], list)

    def test_matched_skills_preserves_original_case(self):
        description = "we need Python and Docker"
        skills = ["Python", "Docker", "Java"]
        result = compute_match(description, skills)
        # matched_skills should contain the original skill strings
        assert "Python" in result["matched_skills"]
        assert "Docker" in result["matched_skills"]
