"""
AI planning layer for PawPal+.
Three responsibilities:
  1. parse_tasks_from_text  — convert natural language into structured Task dicts
  2. generate_ai_schedule   — use Gemini to produce an ordered plan with reasoning
  3. review_schedule        — agentic self-review: Gemini checks its own output

Uses the Gemini REST API directly via requests (no SDK — avoids DLL issues on Windows).
Model: gemini-1.5-flash-8b (free tier, 1000 req/day).
"""

import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


def _get_key() -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise EnvironmentError("GEMINI_API_KEY not set. Add it to your .env file.")
    return key


def _call(system: str, user: str, retries: int = 3) -> str:
    """
    Single-turn Gemini call via REST with automatic retry on 429/503.
    Uses requests so no SDK or DLL dependencies are needed.
    """
    import time
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"parts": [{"text": user}]}],
        "generationConfig": {"temperature": 0.2},
    }
    for attempt in range(retries):
        resp = requests.post(
            GEMINI_URL,
            params={"key": _get_key()},
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        if resp.status_code in (429, 503) and attempt < retries - 1:
            time.sleep(10 * (attempt + 1))  # 10s, 20s, 30s
            continue
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def _extract_json(text: str):
    """
    Extract JSON from a Gemini response even when the model adds preamble
    text or wraps output in markdown code fences.

    Strategy (tried in order):
    1. Direct parse.
    2. Code-fence extraction — content inside ``` blocks.
    3. Bracket scan — find first [ or { and last ] or }.
    """
    text = text.strip()

    # 1. Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Code-fence extraction
    if "```" in text:
        for block in text.split("```"):
            block = block.strip()
            if block.startswith("json"):
                block = block[4:].strip()
            try:
                return json.loads(block)
            except json.JSONDecodeError:
                continue

    # 3. Bracket scan — handles "Here are the tasks: [...]" preamble
    for open_ch, close_ch in [("[", "]"), ("{", "}")]:
        start = text.find(open_ch)
        end = text.rfind(close_ch)
        if start != -1 and end > start:
            try:
                return json.loads(text[start: end + 1])
            except json.JSONDecodeError:
                continue

    raise ValueError(f"No JSON found in response: {text[:300]}")


# ── 1. Natural-language → Task dicts ────────────────────────────────────────

PARSE_SYSTEM = """You are a pet care assistant that extracts tasks from natural language.
Return a JSON array. Each element must have exactly these keys:
  "title"     : short descriptive name (string)
  "duration"  : estimated minutes (positive integer)
  "priority"  : one of "low", "medium", "high"
  "frequency" : one of "daily", "weekly", "monthly", "as_needed"

Rules:
- If duration is not stated, estimate a realistic value.
- If frequency is not stated, infer it from context (walks -> daily, baths -> weekly, etc.).
- If priority is not stated, infer it (feeding/meds -> high, grooming -> medium, enrichment -> low).
- Return ONLY valid JSON. No explanation, no markdown, no extra keys."""


def parse_tasks_from_text(text: str, pet_name: str) -> tuple[list[dict], str]:
    """
    Convert a natural-language description into a list of task dicts.
    Returns (tasks, error). On success error is "". On failure tasks is [].
    """
    if not text.strip():
        return [], "Input was empty."

    try:
        raw = _call(PARSE_SYSTEM, f"Pet name: {pet_name}\n\nDescribe tasks: {text}")
        result = _extract_json(raw)
        if not isinstance(result, list):
            return [], f"Gemini returned a {type(result).__name__} instead of a list. Raw: {raw[:200]}"
        if len(result) == 0:
            return [], f"Gemini returned an empty list. Raw: {raw[:200]}"
        return result, ""
    except Exception as e:
        return [], str(e)


# ── 2. AI schedule generation ────────────────────────────────────────────────

SCHEDULE_SYSTEM = """You are an expert pet care scheduler building a single-day plan.
Only schedule tasks with frequency "daily" or "as_needed" — weekly and monthly tasks do not happen today.

Return a JSON object with exactly these keys:
  "scheduled_titles" : array of task titles in execution order (only daily/as_needed tasks that fit in the time budget)
  "reasoning"        : 2-3 sentences explaining why you ordered and included/excluded tasks
  "advice"           : 1-2 sentences of practical pet care advice for today
  "warnings"         : array of strings for tasks skipped due to time (empty array if none)

Rules:
- High-priority tasks always go first.
- Never schedule a task whose duration would push the cumulative total over available time.
- Do NOT include weekly or monthly tasks in scheduled_titles.
- Return ONLY valid JSON. No extra text."""


def generate_ai_schedule(
    tasks: list[dict],
    owner_name: str,
    pet_name: str,
    time_available: int,
) -> dict:
    """
    Ask Gemini to order and select tasks within the given time budget.
    Returns dict with keys: scheduled_titles, reasoning, advice, warnings.
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
    except Exception as e:
        fallback["warnings"] = [str(e)]
        return fallback


# ── 3. Agentic self-review ───────────────────────────────────────────────────

REVIEW_SYSTEM = """You are reviewing a single-day pet care schedule.
Your job is to evaluate ONLY the tasks that were actually provided and scheduled.

Rules:
- Do NOT penalize the schedule for tasks the owner did not mention.
- Do NOT suggest adding new tasks — only evaluate what is there.
- Flag real problems with the provided tasks only: wrong order, time overflow, or a high-priority task that was skipped when it could have fit.
- If the schedule looks reasonable for what was given, approve it.

Return a JSON object with exactly these keys:
  "score"       : integer 1-10 (judge only what was scheduled, not what is missing)
  "issues"      : array of strings for real problems with the given schedule (empty if none)
  "suggestions" : array of strings for improvements to the given tasks only (empty if none)
  "approved"    : boolean - true if the schedule is reasonable for the tasks provided

Be concise. Return ONLY valid JSON. No extra text."""


def review_schedule(
    scheduled_tasks: list[dict],
    owner_name: str,
    time_available: int,
) -> dict:
    """
    Agentic self-check: Gemini reviews a finalized schedule for issues.
    Returns dict with keys: score, issues, suggestions, approved.
    """
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
    except Exception as e:
        return {"score": 0, "issues": [str(e)], "suggestions": [], "approved": False}
