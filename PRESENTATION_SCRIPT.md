# Presentation Script — PawPal+ Demo

---

## Opening (30 seconds)

"This is PawPal+. It started as a Module 2 project where I built a pet care scheduler — you filled out a form, it generated a plan. It worked, but it was slow and rigid. For the final project I asked: what if you could just describe your pet's day in plain English and let AI handle the rest? That's what this does — and it doesn't just make a plan, it checks its own work."

---

## Demo Input 1 — Standard day, one dog

**Type this into the text box:**

> Maya is a 2-year-old husky who needs a 45-minute run every morning — that's her most important activity. She eats twice a day, about 10 minutes each meal. She gets her heartworm pill once a month, which is critical. She also needs a 20-minute brush-out every day because she sheds a lot.

**Talk through each step as you click:**

**Step 1 — Parse**
*Click "Parse Tasks with AI"*
> "I typed that in plain English. No form, no dropdowns. Watch what it pulls out."

Point to the table that appears:
> "It got all four tasks. It knew the run was high priority because I said 'most important.' It caught that the heartworm pill was critical and marked it high. It figured out the brush is daily just from context. I didn't tell it any of that explicitly."

*Click "Add All to Task List"*

**Step 2 — Schedule**
*Click "Generate AI Schedule"*
> "Now it builds today's plan. Notice it only schedules daily tasks — the heartworm pill is monthly so it won't crowd today's time budget."

Point to the reasoning box:
> "This is what separates it from a simple algorithm. It explains why it made these choices. A greedy algorithm would just sort by priority — this one gives you a reason."

**Step 3 — Self-Review**
*Click "Run Self-Review"*
> "This is the agentic part. The AI just reviewed its own schedule — without me asking it to evaluate anything. It scores the plan and flags real problems."

Point to the score and any issues:
> "If it finds something wrong with what it scheduled, it tells you here. It's not just generating output and moving on — it's checking its own work."

---

## Demo Input 2 — Stress test: tight time budget

**Before this input — change the time available to 30 minutes**

**Type this into the text box:**

> Rex is a senior beagle who needs his arthritis medication every morning, takes 5 minutes. He needs a slow 30-minute walk daily — very important for his joints. He also needs a 20-minute physical therapy exercise session daily, high priority. He gets a bath every two weeks.

**Talk through it:**

**Step 1 — Parse**
*Click "Parse Tasks with AI"*
> "Three daily tasks, one bi-weekly bath. Let's see how it handles 30 minutes."

*Click "Add All to Task List"*

**Step 2 — Schedule**
*Click "Generate AI Schedule"*
> "Only 30 minutes. Something has to get cut. Watch how it decides."

Point to what got left out:
> "It kept the medication and the walk — the two highest priority items. The physical therapy didn't fit. And it tells you exactly why something was dropped."

**Step 3 — Self-Review**
*Click "Run Self-Review"*
> "Now here's what makes this a reliability system, not just a scheduler. The AI is reviewing a plan where a high-priority task got cut. Does it catch that?"

Point to the issues:
> "It flagged the missing physical therapy. It didn't just accept the schedule because it fit the time budget — it noticed that cutting a high-priority health task is a real problem and told the owner."

---

## Closing (20 seconds)

> "So what you just saw was: natural language in, structured plan out, and the AI reviewing its own decisions. The agentic loop isn't just a feature — it's what makes the output trustworthy. You're not just getting a schedule, you're getting a schedule that has been checked."

---

## If they ask about reliability / testing

> "I have 67 automated tests. 55 cover the scheduling logic with no API — priority ordering, time conflicts, recurring due dates. 12 more verify the AI layer with a single API call: correct JSON structure, valid priorities and frequencies, sensible score ranges. The AI also produces a confidence score between 1 and 10 on every plan it generates, so the user always knows how much to trust the output."

---

## Quick reference — what each step shows

| Step | AI feature demonstrated |
|---|---|
| Parse Tasks | Natural language understanding, structured output |
| Generate Schedule | Agentic planning with reasoning |
| Self-Review | Agentic self-check, confidence scoring, reliability |
