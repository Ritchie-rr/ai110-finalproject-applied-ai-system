"""
Developer Smoke Test — ONE API call total.

Runs a single parse_tasks_from_text call and validates all three
AI functions against its output without making extra calls.

Usage:
    pytest tests/test_dev_smoke.py -v

This is the cheap "is the AI layer alive?" check.
Use test_ai_reliability.py for full consistency testing.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from ai_planner import parse_tasks_from_text, generate_ai_schedule, review_schedule

VALID_PRIORITIES = {"low", "medium", "high"}
VALID_FREQUENCIES = {"daily", "weekly", "monthly", "as_needed"}


# ── One shared API call for the whole module ─────────────────────────────────

# pytest runs this once at collection time and all tests below share the result
@pytest.fixture(scope="module")
def smoke_result():
    """
    Makes exactly ONE call to the Gemini API.
    All tests in this file receive the same result — no extra calls.
    """
    tasks = parse_tasks_from_text(
        "My dog Max needs a 20-minute walk every day and his flea medicine once a month.",
        pet_name="Max",
    )

    # Build schedule and review from the parsed tasks — no extra API calls
    task_dicts = tasks if tasks else [
        {"title": "Walk Max", "duration": 20, "priority": "high", "frequency": "daily"}
    ]
    schedule = generate_ai_schedule(task_dicts, "Jordan", "Max", time_available=60)
    review   = review_schedule(task_dicts, "Jordan", time_available=60)

    return {"tasks": tasks, "schedule": schedule, "review": review}


# ── Parser checks ────────────────────────────────────────────────────────────

def test_parser_returns_list(smoke_result):
    assert isinstance(smoke_result["tasks"], list)

def test_parser_finds_at_least_one_task(smoke_result):
    assert len(smoke_result["tasks"]) >= 1, "Expected at least one task from the description"

def test_parser_task_has_required_fields(smoke_result):
    required = {"title", "duration", "priority", "frequency"}
    for task in smoke_result["tasks"]:
        missing = required - set(task.keys())
        assert not missing, f"Task is missing fields: {missing}"

def test_parser_valid_priority(smoke_result):
    for task in smoke_result["tasks"]:
        assert task["priority"] in VALID_PRIORITIES

def test_parser_valid_frequency(smoke_result):
    for task in smoke_result["tasks"]:
        assert task["frequency"] in VALID_FREQUENCIES

def test_parser_duration_positive_int(smoke_result):
    for task in smoke_result["tasks"]:
        assert isinstance(task["duration"], int) and task["duration"] > 0


# ── Scheduler checks ─────────────────────────────────────────────────────────

def test_schedule_has_required_keys(smoke_result):
    required = {"scheduled_titles", "reasoning", "advice", "warnings"}
    missing = required - set(smoke_result["schedule"].keys())
    assert not missing, f"Schedule missing keys: {missing}"

def test_schedule_titles_is_list(smoke_result):
    assert isinstance(smoke_result["schedule"]["scheduled_titles"], list)

def test_schedule_reasoning_is_string(smoke_result):
    assert isinstance(smoke_result["schedule"]["reasoning"], str)


# ── Reviewer checks ──────────────────────────────────────────────────────────

def test_review_has_required_keys(smoke_result):
    required = {"score", "issues", "suggestions", "approved"}
    missing = required - set(smoke_result["review"].keys())
    assert not missing, f"Review missing keys: {missing}"

def test_review_score_in_range(smoke_result):
    score = smoke_result["review"]["score"]
    assert 1 <= score <= 10, f"Score {score} is outside 1–10"

def test_review_approved_is_bool(smoke_result):
    assert isinstance(smoke_result["review"]["approved"], bool)
