# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
3 tasks it can do are enter owner/pet info, add/edit tasks, and generate/view a daily plan. 

UML:
    Owner class holds pet info and availible time, and passes tasks to a Scheduler that applies priority and time contrsaints. The sceduler will output a daily plan and an ordered talk list and plain language reasoning for each choice. 


- What classes did you include, and what responsibilities did you assign to each?
    Owner: profile and time budget
    Pet: stores species and prefrences.
    Task: holds title duration and priority
    Scheduler: selects and orders tasks into a Dailyplan with reason


**b. Design changes**

- Did your design change during implementation?
    Yes, there was changes during implementation.
- If yes, describe at least one change and why you made it.
    I added a frequency field to Task with timedelta calculations so the scheduler could handle recurring tasks (daily/weekly/monthly) and automatically calculate when tasks are due again after completion
    

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?'
    The scheduler considers: available time, task priority frequency and scheduled time to avoid double booking.

- How did you decide which constraints mattered most?
    Time and priority were the primary two constrains becuase a busy owner has a limited amount of mintues and therefore must focus on critcal care first.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
  The scheduler uses a greedy algorithm instead of searching for a globally optimal schedule that maximizes total task completion across all priority levels.
  
- Why is that tradeoff reasonable for this scenario?
    The scheduler's main focus is to get the most important tasks done first so it is a sacrifice that needs to be made.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
    AI was used for UML design in brainstorming, refactoring code to improve readability, adding advanced features with tests, and implementing best practice.
- What kinds of prompts or questions were most helpful?
    Questions about increasing readability or performance were very helpful in better the code.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
    When AI suggested using float('inf') and boolean tuples in sort_by_time() I asked for a more readable version which used constants instead

- How did you evaluate or verify what the AI suggested?
    Running main.py served as a tester even before the pytest which allowed me to see if things were going as planned

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
  Task completion and next_due_date calculation (timedelta), task addition to pets, sorting by time, filtering by priority, time conflict detection (same-time scheduling), and duration conflict detection (exceeding available time).
  
- Why were these tests important?
    These tests allowed me to verify if the core logic worked correctly so then I could add more complex features later on.

**b. Confidence**

- How confident are you that your scheduler works correctly?
  Decently confident for regular cases because comprehensive tests in test_pawpal.py and verification runs in main.py cover the main behaviors.
  
- What edge cases would you test next if you had more time?
    Invalid time formats like "25:00" or tasks across multiple days
---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

    The fact That I was able to start from scratch and build something that was working and I could actually understand.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

    i would make the website look more unique and add more visuals as well.
**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

    I learned that taking things one step at a time is great.
