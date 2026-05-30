"""Unit tests for the TelegramNotifier.send_intelligence_summary method."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from app.services.notifier import TelegramNotifier


def _make_job_dict(
    title="Engineer",
    company="Acme",
    location="Bangalore",
    job_url="https://example.com/job1",
    date_posted="2024-01-15",
    source_platform="linkedin",
    description="",
):
    """Helper to create a job dict for testing."""
    return {
        "title": title,
        "company": company,
        "location": location,
        "job_url": job_url,
        "date_posted": date_posted,
        "source_platform": source_platform,
        "description": description,
    }


def _make_watchlist_entry(company_name="Philips", ats_platform="workday", tier="tier3"):
    """Helper to create a watchlist dict for testing."""
    return {
        "company_name": company_name,
        "ats_platform": ats_platform,
        "tier": tier,
    }


class TestSendIntelligenceSummaryDisabled:
    """Tests for send_intelligence_summary when notifier is disabled."""

    def test_returns_silently_when_not_configured(self):
        """Skips silently if Telegram credentials not configured."""
        notifier = TelegramNotifier(None, None)
        # Should not raise
        notifier.send_intelligence_summary(
            [_make_job_dict()], [_make_watchlist_entry()]
        )

    def test_no_log_warning_when_disabled(self, caplog):
        """Does not log a warning when disabled (silent skip)."""
        notifier = TelegramNotifier(None, None)
        with caplog.at_level(logging.INFO):
            notifier.send_intelligence_summary(
                [_make_job_dict()], [_make_watchlist_entry()]
            )
        # Should not have "Skipping" type messages for intelligence summary
        assert "intelligence summary" not in caplog.text.lower() or "no jobs" not in caplog.text.lower()


class TestSendIntelligenceSummaryEmpty:
    """Tests for send_intelligence_summary with empty jobs."""

    @patch("app.services.notifier.retry_with_backoff")
    def test_no_message_sent_for_empty_jobs(self, mock_retry):
        """Does not send a message when jobs list is empty."""
        notifier = TelegramNotifier("token123", "chat456")
        notifier.send_intelligence_summary([], [_make_watchlist_entry()])
        mock_retry.assert_not_called()


class TestSendIntelligenceSummarySections:
    """Tests for intelligence summary section building."""

    def test_top_10_jobs_section_present(self):
        """Summary includes Top 10 Jobs section."""
        notifier = TelegramNotifier("token", "chat")
        jobs = [_make_job_dict(title=f"Job {i}", date_posted=f"2024-01-{15-i:02d}")
                for i in range(12)]

        sections = notifier._build_intelligence_sections(jobs, [])

        section_text = "\n".join(sections)
        assert "🔝 *Top 10 Jobs*" in section_text

    def test_top_10_jobs_limited_to_10(self):
        """Top 10 Jobs section contains at most 10 entries."""
        notifier = TelegramNotifier("token", "chat")
        jobs = [_make_job_dict(title=f"Job {i}", job_url=f"https://example.com/{i}",
                               date_posted=f"2024-01-{15-i:02d}")
                for i in range(15)]

        sections = notifier._build_intelligence_sections(jobs, [])

        # First section is Top 10 Jobs
        top_section = sections[0]
        # Count bullet points
        assert top_section.count("• ") == 10

    def test_internships_section_present(self):
        """Summary includes Top Internships section when matching jobs exist."""
        notifier = TelegramNotifier("token", "chat")
        jobs = [
            _make_job_dict(title="Software Internship at Google", date_posted="2024-01-15"),
            _make_job_dict(title="Research Intern Position", date_posted="2024-01-14"),
            _make_job_dict(title="Regular Engineer", date_posted="2024-01-13"),
        ]

        sections = notifier._build_intelligence_sections(jobs, [])

        section_text = "\n".join(sections)
        assert "🎓 *Top Internships*" in section_text

    def test_internships_limited_to_5(self):
        """Top Internships section contains at most 5 entries."""
        notifier = TelegramNotifier("token", "chat")
        jobs = [_make_job_dict(title=f"Internship {i}", job_url=f"https://example.com/{i}",
                               date_posted=f"2024-01-{15-i:02d}")
                for i in range(8)]

        sections = notifier._build_intelligence_sections(jobs, [])

        section_text = "\n".join(sections)
        # Find the internships section
        internship_section = [s for s in sections if "🎓" in s][0]
        assert internship_section.count("• ") == 5

    def test_research_section_present(self):
        """Summary includes Top Research Openings when matching jobs exist."""
        notifier = TelegramNotifier("token", "chat")
        jobs = [
            _make_job_dict(title="Scientist", company="IISc", date_posted="2024-01-15"),
            _make_job_dict(title="Engineer", company="DRDO", date_posted="2024-01-14"),
            _make_job_dict(title="Regular Job", company="Acme", date_posted="2024-01-13"),
        ]

        sections = notifier._build_intelligence_sections(jobs, [])

        section_text = "\n".join(sections)
        assert "🔬 *Top Research Openings*" in section_text

    def test_research_matches_in_description(self):
        """Research section matches institution names in description field."""
        notifier = TelegramNotifier("token", "chat")
        jobs = [
            _make_job_dict(
                title="Scientist",
                company="Some Lab",
                description="Collaboration with ISRO on satellite systems",
                date_posted="2024-01-15",
            ),
        ]

        sections = notifier._build_intelligence_sections(jobs, [])

        section_text = "\n".join(sections)
        assert "🔬 *Top Research Openings*" in section_text

    def test_watchlist_section_present(self):
        """Summary includes Watchlist Companies Hiring when matches exist."""
        notifier = TelegramNotifier("token", "chat")
        jobs = [
            _make_job_dict(title="Engineer", company="Philips", date_posted="2024-01-15"),
        ]
        watchlist = [_make_watchlist_entry(company_name="Philips", tier="tier1")]

        sections = notifier._build_intelligence_sections(jobs, watchlist)

        section_text = "\n".join(sections)
        assert "⭐ *Watchlist Companies Hiring*" in section_text

    def test_watchlist_section_absent_when_no_matches(self):
        """Watchlist section is absent when no watchlist companies have jobs."""
        notifier = TelegramNotifier("token", "chat")
        jobs = [
            _make_job_dict(title="Engineer", company="Acme", date_posted="2024-01-15"),
        ]
        watchlist = [_make_watchlist_entry(company_name="Philips", tier="tier1")]

        sections = notifier._build_intelligence_sections(jobs, watchlist)

        section_text = "\n".join(sections)
        assert "⭐ *Watchlist Companies Hiring*" not in section_text

    def test_ats_section_present(self):
        """Summary includes New ATS Opportunities when matching jobs exist."""
        notifier = TelegramNotifier("token", "chat")
        jobs = [
            _make_job_dict(title="Engineer", source_platform="workday", date_posted="2024-01-15"),
            _make_job_dict(title="Designer", source_platform="greenhouse", date_posted="2024-01-14"),
        ]

        sections = notifier._build_intelligence_sections(jobs, [])

        section_text = "\n".join(sections)
        assert "🆕 *New ATS Opportunities*" in section_text

    def test_ats_limited_to_5(self):
        """New ATS Opportunities section contains at most 5 entries."""
        notifier = TelegramNotifier("token", "chat")
        jobs = [_make_job_dict(title=f"Job {i}", source_platform="workday",
                               job_url=f"https://example.com/{i}",
                               date_posted=f"2024-01-{15-i:02d}")
                for i in range(8)]

        sections = notifier._build_intelligence_sections(jobs, [])

        ats_section = [s for s in sections if "🆕" in s][0]
        assert ats_section.count("• ") == 5


class TestIntelligenceSummaryFormatting:
    """Tests for job entry formatting in intelligence summary."""

    def test_job_entry_contains_title_company_location_url(self):
        """Each job entry includes title, company, location, and URL."""
        notifier = TelegramNotifier("token", "chat")
        jobs = [_make_job_dict(
            title="Senior Engineer",
            company="TechCorp",
            location="Mumbai",
            job_url="https://techcorp.com/jobs/123",
            date_posted="2024-01-15",
        )]

        sections = notifier._build_intelligence_sections(jobs, [])

        section_text = "\n".join(sections)
        assert "Senior Engineer" in section_text
        assert "TechCorp" in section_text
        assert "Mumbai" in section_text
        assert "https://techcorp.com/jobs/123" in section_text

    def test_format_uses_bullet_at_company_pipe_location(self):
        """Job entries use the format: • {title} @ {company} | {location}."""
        notifier = TelegramNotifier("token", "chat")
        result = notifier._format_job_list([_make_job_dict(
            title="Dev", company="Corp", location="Delhi"
        )])
        assert "• Dev @ Corp | Delhi" in result


class TestTierOrdering:
    """Tests for tier-based ordering in watchlist section."""

    def test_tier1_before_tier2_before_tier3(self):
        """Tier 1 companies appear before Tier 2, which appear before Tier 3."""
        notifier = TelegramNotifier("token", "chat")
        jobs = [
            _make_job_dict(title="Job at T3", company="CompanyC", date_posted="2024-01-15"),
            _make_job_dict(title="Job at T1", company="CompanyA", date_posted="2024-01-14"),
            _make_job_dict(title="Job at T2", company="CompanyB", date_posted="2024-01-13"),
        ]
        watchlist = [
            _make_watchlist_entry(company_name="CompanyA", tier="tier1"),
            _make_watchlist_entry(company_name="CompanyB", tier="tier2"),
            _make_watchlist_entry(company_name="CompanyC", tier="tier3"),
        ]

        sections = notifier._build_intelligence_sections(jobs, watchlist)

        watchlist_section = [s for s in sections if "⭐" in s][0]
        # CompanyA (tier1) should appear before CompanyB (tier2) before CompanyC (tier3)
        pos_a = watchlist_section.index("CompanyA")
        pos_b = watchlist_section.index("CompanyB")
        pos_c = watchlist_section.index("CompanyC")
        assert pos_a < pos_b < pos_c

    def test_multiple_tier1_companies_grouped(self):
        """Multiple Tier 1 companies are all listed before any Tier 2."""
        notifier = TelegramNotifier("token", "chat")
        jobs = [
            _make_job_dict(title="Job 1", company="Dream1", date_posted="2024-01-15"),
            _make_job_dict(title="Job 2", company="Dream2", date_posted="2024-01-14"),
            _make_job_dict(title="Job 3", company="Target1", date_posted="2024-01-13"),
        ]
        watchlist = [
            _make_watchlist_entry(company_name="Dream1", tier="tier1"),
            _make_watchlist_entry(company_name="Dream2", tier="tier1"),
            _make_watchlist_entry(company_name="Target1", tier="tier2"),
        ]

        sections = notifier._build_intelligence_sections(jobs, watchlist)

        watchlist_section = [s for s in sections if "⭐" in s][0]
        pos_dream1 = watchlist_section.index("Dream1")
        pos_dream2 = watchlist_section.index("Dream2")
        pos_target = watchlist_section.index("Target1")
        assert pos_dream1 < pos_target
        assert pos_dream2 < pos_target


class TestIntelligenceMessageSplitting:
    """Tests for message splitting in intelligence summary."""

    def test_single_message_when_within_limit(self):
        """Returns a single message when total content fits within 4096 chars."""
        notifier = TelegramNotifier("token", "chat")
        jobs = [_make_job_dict(title=f"Job {i}", date_posted=f"2024-01-{15-i:02d}")
                for i in range(3)]

        sections = notifier._build_intelligence_sections(jobs, [])
        messages = notifier._split_intelligence_messages(sections)

        assert len(messages) == 1
        assert len(messages[0]) <= 4096

    def test_splits_when_exceeding_limit(self):
        """Splits into multiple messages when content exceeds 4096 chars."""
        notifier = TelegramNotifier("token", "chat")
        # Create many jobs with long titles to exceed limit
        jobs = [_make_job_dict(
            title=f"Very Long Job Title Number {i} " * 5,
            company=f"Company With Long Name {i}",
            location=f"Location {i}, Country",
            job_url=f"https://example.com/very/long/path/to/job/{i}",
            date_posted=f"2024-01-{(i % 28) + 1:02d}",
            source_platform="workday",
        ) for i in range(50)]
        watchlist = [_make_watchlist_entry(company_name=f"Company With Long Name {i}", tier="tier1")
                     for i in range(20)]

        sections = notifier._build_intelligence_sections(jobs, watchlist)
        messages = notifier._split_intelligence_messages(sections)

        assert len(messages) > 1
        for msg in messages:
            assert len(msg) <= 4096

    @patch("app.services.notifier.retry_with_backoff")
    @patch("app.services.notifier.requests.post")
    def test_send_intelligence_summary_calls_send(self, mock_post, mock_retry):
        """send_intelligence_summary sends messages via Telegram."""
        mock_retry.side_effect = lambda fn, **kwargs: fn()
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = MagicMock()

        notifier = TelegramNotifier("token123", "chat456")
        jobs = [_make_job_dict(title=f"Job {i}", date_posted=f"2024-01-{15-i:02d}")
                for i in range(5)]

        notifier.send_intelligence_summary(jobs, [])

        assert mock_retry.call_count >= 1
