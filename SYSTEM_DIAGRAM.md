# PawPal+ System Diagram

## Data Flow

```mermaid
flowchart TD
    A([👤 User]) -->|Describes pet care in plain English| B[AI Parser\nai_planner.py · parse_tasks_from_text]
    A -->|OR fills out manual form| C

    B -->|Returns structured task list| D{{"👤 Human Review\n(confirm or discard parsed tasks)"}}
    D -->|Confirmed| C[(Task Store\npawpal_system.py\nOwner · Pet · Task)]
    D -->|Discarded| A

    C -->|Incomplete tasks + time budget| E[AI Scheduler\nai_planner.py · generate_ai_schedule]
    C -->|Fallback / Manual tab| F[Greedy Scheduler\npawpal_system.py · Scheduler.generate_plan]

    E -->|Ordered plan + reasoning + advice| G[AI Self-Reviewer\nai_planner.py · review_schedule]
    G -->|Score · issues · suggestions| H{{"👤 Human Review\n(read score and fix issues)"}}
    F -->|Ordered plan + explanation| H

    H -->|Displayed in browser| I([📅 Final Daily Schedule])
```

---

## Component Breakdown

| Component | File | Role |
|---|---|---|
| **Streamlit UI** | `app.py` | Renders all inputs and outputs in the browser |
| **AI Parser** | `ai_planner.py` | Converts natural language → structured `Task` dicts using Gemini |
| **Task Store** | `pawpal_system.py` | Holds `Owner`, `Pet`, and `Task` objects in memory |
| **AI Scheduler** | `ai_planner.py` | Asks Gemini to order tasks within the time budget, with reasoning |
| **Greedy Scheduler** | `pawpal_system.py` | Deterministic fallback — always schedules high-priority tasks first |
| **AI Self-Reviewer** | `ai_planner.py` | Gemini checks its own schedule and returns a quality score + issues |

---

## Where Humans Are Involved

```
Step 1 — After AI Parser
  User sees a table of parsed tasks and must click "Add All" to confirm.
  They can discard and retype if the AI misunderstood anything.

Step 2 — After AI Self-Reviewer
  User reads the score (1–10), any flagged issues, and suggestions.
  They decide whether to act on the feedback or keep the schedule as-is.
```

---

## Where Testing Is Involved

```mermaid
flowchart LR
    T1[test_pawpal.py\nextratests.py] -->|Unit tests — no API needed| C2[Task Store Logic\nscheduling · due dates · conflicts]
    T2[test_ai_reliability.py] -->|API tests — runs 3× per prompt| B2[AI Parser]
    T2 -->|Asserts valid JSON structure| E2[AI Scheduler]
    T2 -->|Checks score range + logic| G2[AI Self-Reviewer]
```

| Test File | What it checks | API needed? |
|---|---|---|
| `tests/test_pawpal.py` | Core scheduling logic, task completion, conflict detection | No |
| `tests/extratests.py` | Extended edge cases for the data model | No |
| `tests/test_ai_reliability.py` | AI outputs are always valid JSON, logically consistent, and stable across repeated runs | Yes (Gemini free tier) |
