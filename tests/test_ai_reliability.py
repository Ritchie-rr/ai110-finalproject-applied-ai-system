"""
AI Reliability Test Suite for PawPal+
======================================
These tests verify that Claude's responses are consistently structured,
logically sound, and resilient to edge-case inputs.

Because they call the real Anthropic API they are marked @pytest.mark.api.

Run all tests:
    pytest tests/test_ai_reliability.py -v

Run without hitting the API (skip these tests):
    pytest -m "not api"

Run only API tests:
    pytest -m api -v
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from ai_planner import parse_tasks_from_text, generate_ai_schedule, review_schedule

pytestmark = pytest.mark.api  # tag every test in this file

# ── Constants ────────────────────────────────────────────────────────────────

VALID_PRIORITIES = {"low", "medium", "high"}
VALID_FREQUENCIES = {"daily", "weekly", "monthly", "as_needed"}
RUNS = 3  # number of times to repeat consistency checks

SAMPLE_INPUT = (
    "My dog Max needs a 30-minute walk every day and a bath once a week. "
    "He also needs his heartworm medicine monthly — that's very important."
)
PET_NAME = "Max"
OWNER_NAME = "Jordan"
TIME_AVAILABLE = 60


# ── Helpers ──────────────────────────────────────────────────────────────────

def _has_required_task_fields(task: dict) -> tuple[bool, set]:
    required = {"title", "duration", "priority", "frequency"}
    missing = required - set(task.keys())
    return len(missing) == 0, missing


# ── 1. Task parsing — structural guarantees ──────────────────────────────────

class TestTaskParsingStructure:
    """Every call must return a well-formed list of task dicts."""

    def test_returns_list(self):
        result = parse_tasks_from_text(SAMPLE_INPUT, PET_NAME)
        assert isinstance(result, list), "Must return a list"

    def test_returns_at_least_one_task(self):
        result = parse_tasks_from_text(SAMPLE_INPUT, PET_NAME)
        assert len(result) >= 1, f"Expected ≥1 task, got {len(result)}"

    def test_all_tasks_have_required_fields(self):
        tasks = parse_tasks_from_text(SAMPLE_INPUT, PET_NAME)
        for task in tasks:
            ok, missing = _has_required_task_fields(task)
            assert ok, f"Task missing fields {missing}: {task}"

    def test_priority_values_are_valid(self):
        tasks = parse_tasks_from_text(SAMPLE_INPUT, PET_NAME)
        for task in tasks:
            assert task["priority"] in VALID_PRIORITIES, (
                f"Invalid priority '{task['priority']}' — must be one of {VALID_PRIORITIES}"
            )

    def test_frequency_values_are_valid(self):
        tasks = parse_tasks_from_text(SAMPLE_INPUT, PET_NAME)
        for task in tasks:
            assert task["frequency"] in VALID_FREQUENCIES, (
                f"Invalid frequency '{task['frequency']}' — must be one of {VALID_FREQUENCIES}"
            )

    def test_duration_is_positive_integer(self):
        tasks = parse_tasks_from_text(SAMPLE_INPUT, PET_NAME)
        for task in tasks:
            assert isinstance(task["duration"], int), (
                f"Duration must be int, got {type(task['duration']).__name__}"
            )
            assert task["duration"] > 0, (
                f"Duration must be positive, got {task['duration']}"
            )

    def test_title_is_non_empty_string(self):
        tasks = parse_tasks_from_text(SAMPLE_INPUT, PET_NAME)
        for task in tasks:
            assert isinstance(task["title"], str) and task["title"].strip(), (
                f"Title must be a non-empty string, got: {task['title']!r}"
            )


# ── 2. Task parsing — consistency across multiple runs ───────────────────────

class TestTaskParsingConsistency:
    """The same prompt run RUNS times should produce structurally valid output each time."""

    def test_always_returns_valid_structure(self):
        for run in range(RUNS):
            tasks = parse_tasks_from_text(SAMPLE_INPUT, PET_NAME)
            assert isinstance(tasks, list), f"Run {run}: expected list"
            for task in tasks:
                ok, missing = _has_required_task_fields(task)
                assert ok, f"Run {run}: task missing {missing}"

    def test_medicine_detected_as_high_priority_majority(self):
        """
        Heartworm medicine is explicitly flagged as 'very important' —
        it should be parsed as high priority in the majority of runs.
        """
        med_priorities = []
        for _ in range(RUNS):
            tasks = parse_tasks_from_text(SAMPLE_INPUT, PET_NAME)
            med = next(
                (t for t in tasks if "medicine" in t["title"].lower()
                 or "med" in t["title"].lower() or "heartworm" in t["title"].lower()),
                None,
            )
            if med:
                med_priorities.append(med["priority"])

        if med_priorities:
            high_ratio = med_priorities.count("high") / len(med_priorities)
            assert high_ratio >= 0.5, (
                f"Medicine should be high priority in ≥50% of runs. Got: {med_priorities}"
            )

    def test_walk_detected_as_daily_majority(self):
        """'Every day' should consistently map to frequency='daily'."""
        walk_freqs = []
        for _ in range(RUNS):
            tasks = parse_tasks_from_text(SAMPLE_INPUT, PET_NAME)
            walk = next(
                (t for t in tasks if "walk" in t["title"].lower()), None
            )
            if walk:
                walk_freqs.append(walk["frequency"])

        if walk_freqs:
            daily_ratio = walk_freqs.count("daily") / len(walk_freqs)
            assert daily_ratio >= 0.66, (
                f"Walk should be daily in ≥66% of runs. Got: {walk_freqs}"
            )

    def test_bath_detected_as_weekly_majority(self):
        """'Once a week' should consistently map to frequency='weekly'."""
        bath_freqs = []
        for _ in range(RUNS):
            tasks = parse_tasks_from_text(SAMPLE_INPUT, PET_NAME)
            bath = next(
                (t for t in tasks if "bath" in t["title"].lower()), None
            )
            if bath:
                bath_freqs.append(bath["frequency"])

        if bath_freqs:
            weekly_ratio = bath_freqs.count("weekly") / len(bath_freqs)
            assert weekly_ratio >= 0.66, (
                f"Bath should be weekly in ≥66% of runs. Got: {bath_freqs}"
            )


# ── 3. Scheduling logic ──────────────────────────────────────────────────────

class TestSchedulingLogic:
    """AI scheduling decisions must be logically sound."""

    def test_schedule_returns_required_fields(self):
        tasks = [{"title": "Walk", "duration": 20, "priority": "high", "frequency": "daily"}]
        result = generate_ai_schedule(tasks, OWNER_NAME, PET_NAME, TIME_AVAILABLE)
        required = {"scheduled_titles", "reasoning", "advice", "warnings"}
        missing = required - set(result.keys())
        assert not missing, f"Schedule missing fields: {missing}"

    def test_high_priority_small_task_always_scheduled(self):
        """A 5-min high-priority task must fit when 60 min is available."""
        tasks = [
            {"title": "Feed Max", "duration": 5, "priority": "high", "frequency": "daily"},
            {"title": "Deep conditioning treatment", "duration": 90, "priority": "low", "frequency": "monthly"},
        ]
        result = generate_ai_schedule(tasks, OWNER_NAME, PET_NAME, TIME_AVAILABLE)
        scheduled_lower = [t.lower() for t in result.get("scheduled_titles", [])]
        assert any("feed" in t for t in scheduled_lower), (
            "5-min high-priority task must be scheduled when 60 min is available"
        )

    def test_task_exceeding_budget_not_scheduled(self):
        """A single task longer than available time must not be included."""
        tasks = [
            {"title": "All-day grooming spa", "duration": 200, "priority": "low", "frequency": "monthly"},
        ]
        result = generate_ai_schedule(tasks, OWNER_NAME, PET_NAME, 30)
        scheduled_lower = [t.lower() for t in result.get("scheduled_titles", [])]
        assert not any("grooming" in t or "spa" in t for t in scheduled_lower), (
            "200-min task must not be scheduled when only 30 min is available"
        )

    def test_scheduled_titles_is_list(self):
        tasks = [{"title": "Walk", "duration": 20, "priority": "high", "frequency": "daily"}]
        result = generate_ai_schedule(tasks, OWNER_NAME, PET_NAME, TIME_AVAILABLE)
        assert isinstance(result["scheduled_titles"], list)

    def test_warnings_is_list(self):
        tasks = [{"title": "Walk", "duration": 20, "priority": "high", "frequency": "daily"}]
        result = generate_ai_schedule(tasks, OWNER_NAME, PET_NAME, TIME_AVAILABLE)
        assert isinstance(result["warnings"], list)

    def test_reasoning_is_non_empty_string(self):
        tasks = [{"title": "Walk", "duration": 20, "priority": "high", "frequency": "daily"}]
        result = generate_ai_schedule(tasks, OWNER_NAME, PET_NAME, TIME_AVAILABLE)
        assert isinstance(result["reasoning"], str) and result["reasoning"].strip()


# ── 4. Self-review (agentic check) ───────────────────────────────────────────

class TestSelfReview:
    """The review step must return a valid, sensible assessment."""

    def test_review_returns_required_fields(self):
        tasks = [{"title": "Walk", "duration": 20, "priority": "high", "frequency": "daily"}]
        result = review_schedule(tasks, OWNER_NAME, TIME_AVAILABLE)
        required = {"score", "issues", "suggestions", "approved"}
        missing = required - set(result.keys())
        assert not missing, f"Review missing fields: {missing}"

    def test_score_in_valid_range(self):
        tasks = [{"title": "Walk", "duration": 20, "priority": "high", "frequency": "daily"}]
        result = review_schedule(tasks, OWNER_NAME, TIME_AVAILABLE)
        assert 1 <= result["score"] <= 10, (
            f"Score {result['score']} is outside valid range 1–10"
        )

    def test_approved_is_boolean(self):
        tasks = [{"title": "Walk", "duration": 20, "priority": "high", "frequency": "daily"}]
        result = review_schedule(tasks, OWNER_NAME, TIME_AVAILABLE)
        assert isinstance(result["approved"], bool)

    def test_overloaded_schedule_gets_low_score_or_not_approved(self):
        """
        A schedule that exceeds available time should be flagged:
        either score ≤ 5 or approved = False.
        """
        tasks = [
            {"title": "Walk", "duration": 120, "priority": "high", "frequency": "daily"},
            {"title": "Grooming", "duration": 90, "priority": "medium", "frequency": "weekly"},
        ]
        result = review_schedule(tasks, OWNER_NAME, time_available=30)
        flagged = (result["score"] <= 5) or (not result["approved"])
        assert flagged, (
            f"Overloaded schedule should be flagged. Got score={result['score']}, "
            f"approved={result['approved']}"
        )

    def test_good_schedule_gets_reasonable_score(self):
        """A single short high-priority task should score reasonably well."""
        tasks = [{"title": "Feed Max", "duration": 5, "priority": "high", "frequency": "daily"}]
        result = review_schedule(tasks, OWNER_NAME, TIME_AVAILABLE)
        assert result["score"] >= 5, (
            f"Simple valid schedule should score ≥5, got {result['score']}"
        )


# ── 5. Edge-case resilience ──────────────────────────────────────────────────

class TestEdgeCases:
    """The system must never crash on unusual inputs."""

    def test_empty_text_returns_list(self):
        result = parse_tasks_from_text("", PET_NAME)
        assert isinstance(result, list)

    def test_whitespace_only_returns_list(self):
        result = parse_tasks_from_text("   \n\t  ", PET_NAME)
        assert isinstance(result, list)

    def test_nonsense_input_returns_list(self):
        result = parse_tasks_from_text("asdfghjkl 12345 !@#$%", PET_NAME)
        assert isinstance(result, list)

    def test_very_long_input_returns_list(self):
        long_text = "My dog needs a walk. " * 50
        result = parse_tasks_from_text(long_text, PET_NAME)
        assert isinstance(result, list)

    def test_empty_task_list_schedule_returns_dict(self):
        result = generate_ai_schedule([], OWNER_NAME, PET_NAME, TIME_AVAILABLE)
        assert isinstance(result, dict)

    def test_zero_time_available_returns_dict(self):
        tasks = [{"title": "Walk", "duration": 30, "priority": "high", "frequency": "daily"}]
        result = generate_ai_schedule(tasks, OWNER_NAME, PET_NAME, 0)
        assert isinstance(result, dict)

    def test_empty_task_list_review_returns_dict(self):
        result = review_schedule([], OWNER_NAME, TIME_AVAILABLE)
        assert isinstance(result, dict)
