"""
AI planning layer for PawPal+.
Three responsibilities:
  1. parse_tasks_from_text  — convert natural language into structured Task dicts
  2. generate_ai_schedule   — use Gemini to produce an ordered plan with reasoning
  3. review_schedule        — agentic self-review: Gemini checks its own output

Uses the Google Gemini API (free tier: gemini-1.5-flash).
"""

import json
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

_configured = False


def _ensure_configured():
    global _configured
    if not _configured:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY not set. Add it to your .env file."
            )
        genai.configure(api_key=api_key)
        _configured = True


def _extract_json(text: str):
    """Strip markdown fences and parse JSON from a Gemini response."""
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def _call(system: str, user: str) -> str:
    """Single-turn Gemini call. Returns the response text."""
    _ensure_configured()
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system,
    )
    response = model.generate_content(user)
    return response.text


# ── 1. Natural-language → Task dicts ────────────────────────────────────────

PARSE_SYSTEM = """You are a pet care assistant that extracts tasks from natural language.
Return a JSON array. Each element must have exactly these keys:
  "title"     : short descriptive name (string)
  "duration"  : estimated minutes (positive integer)
  "priority"  : one of "low", "medium", "high"
  "frequency" : one of "daily", "weekly", "monthly", "as_needed"

Rules:
- If duration is not stated, estimate a realistic value.
- If frequency is not stated, infer it from context (walks → daily, baths → weekly, etc.).
- If priority is not stated, infer it (feeding/meds → high, grooming → medium, enrichment → low).
- Return ONLY valid JSON. No explanation, no markdown, no extra keys."""


def parse_tasks_from_text(text: str, pet_name: str) -> list[dict]:
    """
    Convert a natural-language description into a list of task dicts.
    Returns an empty list on any failure so the UI can degrade gracefully.
    """
    if not text.strip():
        return []

    try:
        raw = _call(
            PARSE_SYSTEM,
            f"Pet name: {pet_name}\n\nDescribe tasks: {text}",
        )
        result = _extract_json(raw)
        return result if isinstance(result, list) else []
    except Exception:
        return []


# ── 2. AI schedule generation ────────────────────────────────────────────────

SCHEDULE_SYSTEM = """You are an expert pet care scheduler.
Given a list of tasks and time constraints, produce an optimized daily plan.

Return a JSON object with exactly these keys:
  "scheduled_titles" : array of task titles in execution order (only tasks that fit in the time budget)
  "reasoning"        : 2-3 sentences explaining why you ordered and included/excluded tasks
  "advice"           : 1-2 sentences of practical pet care advice for today
  "warnings"         : array of strings listing any concerns (empty array if none)

Rules:
- High-priority tasks always go first.
- Never schedule a task whose duration would push the cumulative total over available time.
- Return ONLY valid JSON. No extra text."""


def generate_ai_schedule(
    tasks: list[dict],
    owner_name: str,
    pet_name: str,
    time_available: int,
) -> dict:
    """
    Ask Gemini to order and select tasks within the given time budget.
    Returns a dict with keys: scheduled_titles, reasoning, advice, warnings.
    Falls back to an error dict on failure.
    """
    fallback = {
        "scheduled_titles": [],
        "reasoning": "AI scheduling unavailable.",
        "advice": "",
        "warnings": ["Could not reach AI scheduler."],
    }

    if not tasks:
        fallback["reasoning"] = "No tasks provided."
        return fallback

    try:
        user_msg = (
            f"Owner: {owner_name}\n"
            f"Pet: {pet_name}\n"
            f"Available time: {time_available} minutes\n\n"
            f"Tasks:\n{json.dumps(tasks, indent=2)}"
        )
        result = _extract_json(_call(SCHEDULE_SYSTEM, user_msg))
        result.setdefault("scheduled_titles", [])
        result.setdefault("reasoning", "")
        result.setdefault("advice", "")
        result.setdefault("warnings", [])
        return result
    except Exception:
        return fallback


# ── 3. Agentic self-review ───────────────────────────────────────────────────

REVIEW_SYSTEM = """You are a critical reviewer of pet care schedules.
Examine the schedule for logical problems, safety issues, and missed priorities.

Return a JSON object with exactly these keys:
  "score"       : integer 1-10 rating the schedule quality
  "issues"      : array of strings describing problems found (empty if none)
  "suggestions" : array of strings with concrete improvements (empty if none)
  "approved"    : boolean - true if the schedule is acceptable as-is

Be concise. Return ONLY valid JSON. No extra text."""


def review_schedule(
    scheduled_tasks: list[dict],
    owner_name: str,
    time_available: int,
) -> dict:
    """
    Agentic self-check: Gemini reviews a finalized schedule for issues.
    Returns a dict with keys: score, issues, suggestions, approved.
    """
    fallback = {
        "score": 0,
        "issues": ["Review unavailable."],
        "suggestions": [],
        "approved": False,
    }

    if not scheduled_tasks:
        return {"score": 5, "issues": [], "suggestions": ["No tasks to review."], "approved": True}

    total_time = sum(t.get("duration", 0) for t in scheduled_tasks)

    try:
        user_msg = (
            f"Owner: {owner_name}\n"
            f"Available time: {time_available} minutes\n"
            f"Scheduled time: {total_time} minutes\n\n"
            f"Scheduled tasks:\n{json.dumps(scheduled_tasks, indent=2)}"
        )
        result = _extract_json(_call(REVIEW_SYSTEM, user_msg))
        result.setdefault("score", 5)
        result.setdefault("issues", [])
        result.setdefault("suggestions", [])
        result.setdefault("approved", False)
        return result
    except Exception:
        return fallback
