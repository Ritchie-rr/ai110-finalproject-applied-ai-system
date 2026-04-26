# PawPal+ — AI-Powered Pet Care Scheduler

---

## Original Project

PawPal+ started as a Module 2 project focused on helping busy pet owners manage care tasks for multiple pets. Users could manually enter tasks with details like title, duration, priority, and frequency. The system then used a greedy algorithm to generate an optimized daily schedule, fitting in high-priority tasks first based on the owner's available time.

The original system featured conflict detection, recurring due-date tracking, and plain-text scheduling explanations. However, it lacked AI capabilities and required users to manually fill out a form for every single task.

---

## Title and Summary

**PawPal+ — AI-Powered Pet Care Scheduler**

PawPal+ helps busy pet owners plan their day by turning a plain-English description of their pet's needs into a structured, prioritized care schedule. Once the schedule is made, the AI reviews its own plan to catch any potential problems. It supports any number of pets and adapts to the owner's actual available time, whether they have 10 minutes or 8 hours to spare.

This matters because pet care is easy to forget or mismanage when life gets busy. This system removes the friction of manual data entry while adding an intelligent layer that catches mistakes a simple algorithm would miss, such as scheduling only one feeding session for a dog that needs two.

---

## Architecture Overview

The system has two parallel workflows that share the same data store:

**Manual workflow** — The owner fills out a form to add tasks and clicks a button to run the deterministic greedy scheduler built in `pawpal_system.py.` This path requires no API key and always works.

**AI workflow** —The owner describes their pet's needs in plain English. That text goes to Gemini via a direct REST call in `ai_planner.py`, which extracts structured task objects. The owner reviews and confirms them, and then Gemini generates an ordered schedule with natural-language reasoning. Finally, Gemini reviews its own schedule to score it, flag issues, and suggest improvements. This three-step loop of parsing, scheduling, and self-reviewing makes the system agentic.

The full diagram lives in `SYSTEM_DIAGRAM.md`.

---

## What the App Does

### Manual Mode
- Enter owner info (name, time available) and pet info (name, species)
- Add care tasks manually: title, duration, priority (low / medium / high), and frequency (daily / weekly / monthly / as-needed)
- View and filter tasks by status, priority, and frequency
- Generate a daily schedule using a greedy priority-first algorithm
- See conflict warnings when tasks overlap in time or exceed the available time budget
- Read plain-text reasoning for every scheduling decision

### AI Assistant Mode
PawPal+ adds three AI-powered steps on top of the manual workflow:

**Step 1 — Natural language task entry**
The owner types a plain-English description of what their pet needs. Gemini reads it and extracts a structured list of tasks, including estimated durations, inferred priorities, and correct frequencies. The owner can then review and confirm these tasks before they are added to the list.

**Step 2 — AI-generated schedule**
Gemini produces an ordered daily plan with a natural-language explanation of why tasks were ordered the way they were. It also provides practical pet-care advice for the day and includes warnings about anything that looks problematic.

**Step 3 — Agentic self-review**
Gemini reviews its own output. It scores the schedule from 1-10, flags issues like missed feedings or health gaps, and suggests concrete improvements. This creates an agentic workflow where the AI checks its own work without needing a prompt from the user.

---

## AI Features Used

| Feature | How it appears in PawPal+ |
|---|---|
| **Agentic Workflow** | Gemini plans a schedule (Step 2), then reviews and critiques its own plan (Step 3) without human input between those two steps |
| **Reliability / Testing System** | `tests/test_ai_reliability.py` runs the same prompts multiple times and asserts outputs are always structurally valid, logically consistent, and resilient to bad input |

---

## Project Structure

```
ai110-finalproject-applied-ai-system/
├── app.py                        # Streamlit UI (Manual + AI tabs)
├── pawpal_system.py              # Core data model: Task, Pet, Owner, Scheduler
├── ai_planner.py                 # Gemini REST API layer (parse, schedule, review)
├── requirements.txt              # All dependencies
├── .env                          # API key (never committed to git)
├── SYSTEM_DIAGRAM.md             # Visual architecture diagram
├── tests/
│   ├── test_pawpal.py            # Unit tests for scheduling logic
│   ├── extratests.py             # Extended unit tests
│   ├── test_ai_reliability.py   # AI reliability and consistency tests
│   └── test_dev_smoke.py        # Single-call smoke test for fast dev checks
└── README.md
```

---

## Setup Instructions

### 1. Open the project folder

```bash
cd "final-project/ai110-finalproject-applied-ai-system"
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

> The `.env` file is listed in `.gitignore` and will never be committed to version control.

### 5. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` in your browser.

---

## Sample Interactions

### Example 1 — Natural language task parsing

**Input typed by user:**
> "Bruno is a golden retriever who needs a 30-minute walk every morning — that's the most important thing. He eats twice a day, about 5 minutes each. His flea and tick medicine is monthly and really important. Weekly bath takes 45 minutes. And a 15-minute play session daily, low priority."

**AI output (parsed tasks):**

| Title | Duration | Priority | Frequency |
|---|---|---|---|
| Walk Bruno | 30 min | high | daily |
| Feed Bruno | 5 min | high | daily |
| Administer flea medicine | 5 min | high | monthly |
| Bathe Bruno | 45 min | medium | weekly |
| Play with Bruno | 15 min | low | daily |

The AI correctly inferred that the walk was high priority from "most important", that flea medicine was high priority from "really important", and that the bath was medium since no emphasis was placed on it.

---

### Example 2 — AI-generated schedule

**Context:** 5 tasks above, 90-minute time budget *(demo default — owner sets this to whatever time they actually have)*

**AI output:**
- Scheduled order: Feed Bruno → Administer flea medicine → Walk Bruno → Bathe Bruno
- Play with Bruno was excluded (cumulative time would exceed budget)

**Reasoning from Gemini:**
> "All high-priority tasks (feeding, flea medicine, and walking) were scheduled first to ensure Bruno's health and safety needs are met. The bath was added as a medium-priority weekly task that fits within the remaining time. The play session was excluded due to the 90-minute time constraint."

**Advice:**
> "Make sure Bruno has fresh water available throughout the day, especially after his walk."

---

### Example 3 — Agentic self-review catching a real problem

**Context:** Same schedule from Example 2

**AI review output:**
- Score: **3 / 10**
- Approved: **No**
- Issues found:
  - "Only one feeding session is scheduled daily, which is insufficient for most dogs and a significant health oversight."
  - "Weekly bathing is generally too frequent and can strip natural oils from a dog's skin."
  - "A single 30-minute walk may be insufficient for a golden retriever's exercise needs."
- Suggestions:
  - Add a second daily feeding session
  - Reduce bath frequency to monthly or as-needed
  - Consider splitting the walk into two shorter sessions

This example shows the agentic loop working — Gemini scheduled only one feeding because the task list only had one feeding entry, then caught its own oversight in the review step and flagged it as a health problem.

---

## Design Decisions

**Why single-day planning only?**
Weekly and monthly tasks (like baths and flea medicine) do not happen every day, so including them in the daily time budget would make the schedule misleading. The AI schedule only places `daily` and `as_needed` tasks into today's plan. Weekly and monthly tasks are still stored in the task list and visible in the Manual Setup tab — they just do not compete for today's 90 minutes. This keeps the schedule honest and easy to act on.

**Why does the self-review only judge what was given?**
An early version of the review prompt penalized the schedule for things the owner never mentioned — like missing dental care or nail trims. That was not useful feedback; it was the AI inventing requirements. The review prompt was updated to only evaluate the tasks that were actually provided and scheduled. If the owner did not mention teeth brushing, the review has no business flagging it. The review's job is to catch real problems in the given plan: wrong priority order, time overflow, or a high-priority task that was skipped when it could have fit.

**Why Gemini over other models?**
Gemini has a free REST API with no SDK required. Using the REST API directly (via `requests`) avoided a DLL compatibility issue with the Gemini Python SDK on Windows, making the app work on more machines without setup headaches.

**Why keep the manual scheduler alongside the AI?**
The greedy algorithm in `pawpal_system.py` is a reliable fallback that works with no API key and no internet connection. It also makes the AI's value clear by contrast. You can run both and compare the reasoning quality.

**Why a three-step agentic loop instead of one big prompt?**
Splitting parse, schedule, and review into three separate calls means each prompt is focused and the JSON outputs are small and predictable. One large prompt asking Gemini to do all three at once would produce less reliable structured output and be harder to debug.

**Why show the self-review score to the user?**
Transparency. Pet care has real health consequences. Showing the owner that the AI scored its own plan and flagged issues gives them the information they need to make a better decision — rather than blindly trusting the schedule.

**Trade-offs made:**
- The daily-only filter means owners have to remember that weekly/monthly tasks exist separately. A future improvement would be a clear "upcoming this week" section next to the daily plan.
- Each step is a separate API call (3 calls per full workflow), which uses more quota than a single call but produces far cleaner outputs.
- The reliability tests hit the real API and cost quota, so they are marked `@pytest.mark.api` and skipped by default in fast test runs.
- Session state in Streamlit resets on page refresh, so there is no persistence between browser sessions. A future version could add a local database.

---

## Testing Summary

### Results at a glance

| Test suite | Tests | Passed | Failed | API calls used |
|---|---|---|---|---|
| `test_pawpal.py` — core scheduler logic | 13 | 13 | 0 | 0 |
| `extratests.py` — edge cases | 42 | 42 | 0 | 0 |
| `test_dev_smoke.py` — AI layer smoke test | 12 | 12 | 0 | 1 |
| **Total** | **67** | **67** | **0** | **1** |

**67 out of 67 tests passed. 1 API call used for the full AI layer verification.**

The self-review gives every schedule a quality score from 1–10. In testing, well-formed daily plans with correct priorities scored between 7–9. Plans that mixed daily and weekly tasks into one time budget scored 3–4 — which is what caught the design flaw and led to the single-day-only decision.

---

### How each layer is verified

**Automated unit tests (no API)**
55 tests cover the scheduling engine with zero API calls: task creation, priority ordering, time conflict detection, recurring due-date calculations, and multi-pet task management. These run in under 1 second and can be run any time.

**AI smoke test (1 API call)**
12 tests share a single Gemini call using pytest's `scope="module"` fixture. They verify that all three AI functions (parse, schedule, review) return the correct JSON structure, valid enum values, and sensible types. Run this before a demo to confirm the API key and model are working.

**AI self-review confidence scoring**
Every schedule Gemini produces gets scored 1–10 by a second Gemini call that reviews the first one's output. This is built-in confidence scoring — if the score is below 5 or `approved` is false, the UI shows the issues so the owner can decide whether to act on the plan or revise it.

**Error logging**
Every AI function catches exceptions and returns a structured error message rather than crashing. The UI displays the exact error text (e.g., "429 Too Many Requests" or "No JSON found in response") so failures are visible and diagnosable, not silent.

---

### What didn't work at first and how it was fixed

- **SDK DLL block** — The `google-generativeai` SDK was blocked by a Windows Application Control policy. Fixed by switching to direct REST calls with `requests`, which has no native dependencies.
- **Wrong model names** — `gemini-1.5-flash` and `gemini-1.5-flash-8b` returned 404. Fixed by querying the ListModels API endpoint to find exactly which models were available on the key.
- **Rate limits during testing** — Rapid repeated test runs hit 429 errors. Fixed by adding retry logic with exponential backoff (10s, 20s, 30s delays) inside `_call()`.
- **Overly harsh self-review** — Early prompts penalized the schedule for tasks the owner never mentioned (dental care, nail trims, extra walks). Fixed by rewriting the review prompt to only evaluate what was provided, not what is missing.
- **Weekly tasks in the daily budget** — The scheduler was including weekly baths and monthly medicine in the 90-minute daily plan, which was misleading. Fixed by updating the schedule prompt to only include `daily` and `as_needed` tasks.

---

### What I learned from testing

Gemini is highly consistent on structure — required JSON fields are always present and enum values are always valid. It is less consistent on specific inferences across repeated runs (a daily walk comes back as `daily` about 80% of the time, occasionally as `as_needed`). This is why the reliability tests use a 66% threshold rather than 100% — AI outputs are probabilistic, not deterministic, and tests need to account for that.

---

## Reflection

**What this project taught me about AI:**
The most important thing I learned is that AI is most useful when it is given a narrow, well-defined job. When I tried to give Gemini one big prompt to parse tasks, schedule them, and review them all at once, the output was not working so I had to split the work up and make each input clear. Prompt engineering is not about writing more words; it is about writing more precise boundaries.

The agentic self-review step was the most surprising part to build. I expected Gemini to mostly approve its own schedules, but it consistently flagged real problems. For example, like the fact that one feeding entry per day does not mean one feeding per day is enough for a dog. The AI brought in external knowledge (what dogs actually need) that was never in the input. That is genuinely useful and something a simple algorithm could never do.

**What this project taught me about problem-solving:**
Real systems break in ways that have nothing to do with your code — Windows DLL policies, API model names that change between documentation versions, per-minute rate limits that only show up when you are testing too fast. Learning to diagnose those kinds of failures (reading actual error messages, querying the API's own ListModels endpoint to find the truth) is just as important as writing the logic itself.

I also learned to design for failure from the start. Every AI call in this project has a fallback, a retry, and a visible error message. That made debugging faster and made the demo more reliable — if one call fails, the app tells you exactly why instead of silently returning an empty list.

---

## How to Run the Tests

### Unit tests (no API key required)

```bash
pytest tests/test_pawpal.py -v
pytest tests/extratests.py -v
```

### Quick AI smoke test (1 API call)

```bash
pytest tests/test_dev_smoke.py -v
```

### Full AI reliability suite (many API calls — use sparingly)

```bash
pytest tests/test_ai_reliability.py -v

# Skip all API tests for a fast run
pytest -m "not api" -v
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI |
| `requests` | Gemini REST API calls (no SDK needed) |
| `python-dotenv` | Load API key from `.env` |
| `pandas` | Table display |
| `pytest` | Unit and reliability testing |

---

## Portfolio Reflection

This project shows that I approach AI engineering the same way I approach any real problem. I start with what actually needs to work, not what looks impressive, prioritizing practicality.  When the AI reviewer was penalizing schedules for things the user never mentioned, I didn't accept it, I diagnosed the prompt, identified the exact rule that was causing the bad behavior, and rewrote it with a clear boundary. Every problem in this project had a real cause and a real fix, and I found both.

What this project says about me as an AI engineer is that I treat AI as a tool with failure modes, not magic. I built fallbacks for when the API goes down, retry logic for rate limits, error messages that surface the actual reason something failed so that I could learn from the errors and make fixes. I also made deliberate decisions about where AI belongs and where it doesn't: the scheduling logic stays deterministic so the app works without an internet connection, and the AI is layered on top to add reasoning and natural language, not to replace something that was already reliable.

## Video of Explanation
https://www.loom.com/share/03a8311dfb8549529ab3bd8d045e967d
