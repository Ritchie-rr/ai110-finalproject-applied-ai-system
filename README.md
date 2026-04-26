# PawPal+ — AI-Powered Pet Care Scheduler

PawPal+ is a Streamlit application that helps busy pet owners plan their daily pet care. It combines a deterministic scheduling engine with an agentic AI layer powered by Claude (Anthropic) to let owners describe their pet's needs in plain English, receive an intelligently ordered schedule, and get an automatic quality review of that schedule.

---

## What the app does

### Manual Mode
- Enter owner info (name, time available) and pet info (name, species)
- Add care tasks manually: title, duration, priority (low / medium / high), and frequency (daily / weekly / monthly / as-needed)
- View and filter tasks by status, priority, and frequency
- Generate a daily schedule using a greedy priority-first algorithm
- See conflict warnings when tasks overlap in time or exceed the available time budget
- Read plain-text reasoning for every scheduling decision

### AI Assistant Mode (new)
PawPal+ adds three AI-powered steps on top of the manual workflow:

**Step 1 — Natural language task entry**
Instead of filling out a form, the owner types a plain-English description of what their pet needs. Claude reads the description and extracts a structured list of tasks — with estimated durations, inferred priorities, and correct frequencies — that the owner can review and confirm before they are added to the task list.

> Example input: *"Max needs a 30-minute walk every day. He gets a bath once a week, and his heartworm medicine once a month — that one is very important."*
>
> Output: three structured tasks with title, duration, priority, and frequency fields filled in automatically.

**Step 2 — AI-generated schedule**
Once tasks exist, the owner clicks one button and Claude produces an ordered daily plan. Unlike the deterministic greedy algorithm, Claude's schedule comes with:
- A natural-language explanation of why tasks were ordered the way they were
- Practical pet-care advice for the day
- Warnings about anything that looks problematic

**Step 3 — Agentic self-review**
After generating the schedule, Claude reviews its own output. It scores the schedule from 1–10, flags any issues (missed high-priority tasks, time overflows, nutrition or health gaps), and suggests concrete improvements. This is the "check your own work" step that makes the workflow agentic.

---

## AI features used

| Feature | How it appears in PawPal+ |
|---|---|
| **Agentic Workflow** | Claude plans a schedule (Step 2), then reviews and critiques its own plan (Step 3) without human input between those two steps |
| **Reliability / Testing System** | `tests/test_ai_reliability.py` runs the same prompts multiple times and asserts that outputs are always structurally valid, logically consistent, and resilient to bad input |

---

## Project structure

```
ai110-module2show-pawpal-starter/
├── app.py                        # Streamlit UI (Manual + AI tabs)
├── pawpal_system.py              # Core data model: Task, Pet, Owner, Scheduler
├── ai_planner.py                 # Claude API layer (parse, schedule, review)
├── requirements.txt              # All dependencies
├── .env                          # API key (never committed to git)
├── tests/
│   ├── test_pawpal.py            # Unit tests for scheduling logic
│   ├── extratests.py             # Extended unit tests
│   └── test_ai_reliability.py   # AI reliability and consistency tests
└── README.md
```

---

## How to run

### 1. Clone or open the project

```bash
cd "Project 2/ai110-module2show-pawpal-starter"
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows (Command Prompt)
.venv\Scripts\activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Gemini API key

Open `.env` and replace the placeholder:

```
GEMINI_API_KEY=your-actual-key-here
```

Get a **free** key at [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey). No billing required for the free tier.

> If you already used Gemini in another project (e.g. DocuBot), you can copy the same `GEMINI_API_KEY` value — it works across projects.

> The `.env` file is listed in `.gitignore` and will never be committed to version control.

### 5. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` in your browser.

---

## How to run the tests

### Unit tests (no API key required)

These test the core scheduling logic — task creation, priority ordering, conflict detection, and due-date calculations.

```bash
pytest tests/test_pawpal.py -v
pytest tests/extratests.py -v
```

### AI reliability tests (requires API key)

These tests call the real Gemini API and verify that the model's outputs are always:
- Structurally correct (required JSON fields always present)
- Logically sound (high-priority tasks scheduled first, oversized tasks excluded)
- Consistent across multiple runs (same input → same frequencies and priorities ≥66% of the time)
- Resilient to edge cases (empty input, nonsense text, zero time budget)

```bash
# Run all AI reliability tests
pytest tests/test_ai_reliability.py -v

# Run only AI tests across the whole suite
pytest -m api -v

# Run everything except AI tests (fast, no API cost)
pytest -m "not api" -v
```

The AI tests are marked `@pytest.mark.api` so you can include or exclude them explicitly.

---

## Workflow walkthrough

1. **Fill in owner and pet info** at the top of the page and click **Save Owner & Pet**.
2. Switch to the **🤖 AI Assistant** tab.
3. Type a plain-English description of your pet's care needs and click **🔍 Parse Tasks with AI**.
4. Review the extracted tasks in the table. Click **✅ Add All to Task List** to confirm them.
5. Click **🤖 Generate AI Schedule** to get an ordered plan with reasoning and advice.
6. Click **🔎 Run Self-Review** to have Claude check its own schedule and score it.
7. Optionally switch to the **Manual Setup** tab to add or edit tasks by hand and run the deterministic scheduler.

---

## Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI |
| `google-generativeai` | Gemini API client (free tier) |
| `python-dotenv` | Load API key from `.env` |
| `pandas` | Table display |
| `pytest` | Unit and reliability testing |
