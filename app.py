import os
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler, DailyPlan, Priority, Frequency
from datetime import date
import pandas as pd

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")
st.title("🐾 PawPal+")

# ── Session state ────────────────────────────────────────────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = None
if "pet" not in st.session_state:
    st.session_state.pet = None
if "plan" not in st.session_state:
    st.session_state.plan = None
if "ai_parsed_tasks" not in st.session_state:
    st.session_state.ai_parsed_tasks = []
if "ai_schedule_result" not in st.session_state:
    st.session_state.ai_schedule_result = None
if "ai_review_result" not in st.session_state:
    st.session_state.ai_review_result = None
if "demo_nl" not in st.session_state:
    st.session_state.demo_nl = ""

# ── Shared: Owner & Pet setup (used by both tabs) ────────────────────────────
st.subheader("Owner & Pet Info")
col1, col2, col3, col4 = st.columns(4)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
with col2:
    time_available = st.number_input("Time available (min)", min_value=10, max_value=480, value=60)
with col3:
    pet_name = st.text_input("Pet name", value="Mochi")
with col4:
    species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Save Owner & Pet"):
    pet = Pet(name=pet_name, species=species)
    owner = Owner(name=owner_name, time_available=int(time_available))
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.session_state.pet = pet
    st.session_state.plan = None
    st.session_state.ai_schedule_result = None
    st.session_state.ai_review_result = None
    st.success(f"Saved! {owner_name} with pet {pet_name} ({species})")

if st.session_state.owner:
    st.caption(f"Current owner: {st.session_state.owner}")

st.divider()

tab_manual, tab_ai = st.tabs(["Manual Setup", "🤖 AI Assistant"])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Manual Setup (original workflow)
# ════════════════════════════════════════════════════════════════════════════
with tab_manual:

    # --- Add Tasks ---
    st.subheader("Tasks")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col4:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "monthly", "as_needed"], index=0)

    if st.button("Add task"):
        if st.session_state.owner is None:
            st.warning("Save an owner and pet first.")
        else:
            task = Task(
                title=task_title,
                duration=int(duration),
                priority=priority,
                frequency=frequency,
            )
            st.session_state.owner.add_task(st.session_state.pet, task)
            st.success(f"Added: {task_title} ({frequency})")

    if st.session_state.pet and st.session_state.pet.tasks:
        st.write("### View & Manage Tasks")

        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.radio("Status", ["All", "Incomplete", "Completed"], horizontal=True)
        with col2:
            sort_by = st.radio("Sort by", ["Priority", "Duration", "Time Scheduled"], horizontal=True)
        with col3:
            priority_filter = st.multiselect(
                "Priority", ["low", "medium", "high"], default=["low", "medium", "high"]
            )

        filtered_tasks = st.session_state.pet.tasks
        if status_filter == "Incomplete":
            filtered_tasks = st.session_state.pet.get_incomplete_tasks()
        elif status_filter == "Completed":
            filtered_tasks = [t for t in filtered_tasks if t.completion_status]

        filtered_tasks = [t for t in filtered_tasks if t.priority in priority_filter]

        if sort_by == "Duration":
            filtered_tasks = sorted(filtered_tasks, key=lambda t: t.duration, reverse=True)
        elif sort_by == "Priority":
            priority_order = {"high": 0, "medium": 1, "low": 2}
            filtered_tasks = sorted(filtered_tasks, key=lambda t: priority_order.get(t.priority, 3))
        elif sort_by == "Time Scheduled":
            scheduler = Scheduler(owner=st.session_state.owner)
            filtered_tasks = scheduler.sort_by_time(filtered_tasks)

        if filtered_tasks:
            st.success(f"✓ Found {len(filtered_tasks)} task(s)")

            task_data = []
            for task in filtered_tasks:
                priority_badge = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.priority, "⚪")
                status_badge = "✅" if task.completion_status else "⭕"
                last_completed = str(task.last_completed) if task.last_completed else "Never"
                next_due = str(task.next_due_date) if task.next_due_date else "No due date"
                task_data.append({
                    "Status": status_badge,
                    "Task": task.title,
                    "Duration (min)": task.duration,
                    "Priority": f"{priority_badge} {task.priority.upper()}",
                    "Frequency": task.frequency.upper(),
                    "Last Completed": last_completed,
                    "Next Due": next_due,
                })

            df = pd.DataFrame(task_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            with st.expander("🔄 Update Task Status"):
                st.caption("Toggle completion status for any task:")
                for task in filtered_tasks:
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        new_status = st.checkbox(
                            "Done", value=task.completion_status, key=f"task_status_{id(task)}"
                        )
                        if new_status != task.completion_status:
                            if new_status:
                                task.mark_complete()
                                st.session_state.plan = None
                            else:
                                task.mark_incomplete()
                                st.session_state.plan = None
                    with col2:
                        st.write(f"**{task.title}** ({task.duration}min)")
        else:
            st.info("No tasks match the current filters.")
    else:
        st.info("No tasks yet. Add one above.")

    st.divider()

    # --- Generate Schedule ---
    st.subheader("🔧 Build Schedule")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("▶️ Generate Daily Schedule", use_container_width=True):
            if st.session_state.owner is None:
                st.warning("Save an owner and pet first.")
            elif not st.session_state.pet.tasks:
                st.warning("Add at least one task before generating a schedule.")
            else:
                scheduler = Scheduler(owner=st.session_state.owner)
                st.session_state.plan = scheduler.generate_plan()
                st.success("✅ Schedule generated successfully!")

    with col2:
        if st.session_state.owner:
            scheduler = Scheduler(owner=st.session_state.owner)
            due_tasks = scheduler.get_due_tasks()
            st.metric("Tasks Due", len(due_tasks))
        else:
            st.write("*Set owner*")

    with col3:
        if st.session_state.owner:
            time_remaining = st.session_state.owner.time_available
            if st.session_state.plan:
                time_remaining -= st.session_state.plan.total_time
            st.metric("Available", f"{time_remaining}m")
        else:
            st.write("*Set owner*")

    if st.session_state.plan:
        scheduler = Scheduler(owner=st.session_state.owner)

        conflicts = scheduler.detect_conflicts(st.session_state.plan)
        time_conflicts = scheduler.detect_time_conflicts(st.session_state.plan.scheduled_tasks)

        if conflicts or time_conflicts:
            st.warning("⚠️ **Scheduling Issues Detected**", icon="⚠️")
            issue_data = []
            if time_conflicts:
                for c in time_conflicts:
                    issue_data.append({"Severity": "High - Time Overlap", "Issue": c})
            if conflicts:
                for c in conflicts:
                    issue_data.append({"Severity": "Medium - Time Exceeded", "Issue": c})
            st.dataframe(pd.DataFrame(issue_data), use_container_width=True, hide_index=True)

            with st.expander("💡 How to resolve these issues"):
                if conflicts:
                    st.write("**Time Capacity Exceeded:**")
                    st.write(f"- Your owner has {st.session_state.owner.time_available} min available")
                    st.write(f"- Current plan requires {st.session_state.plan.total_time} min")
                    st.write("- **Action:** Remove or defer lower-priority tasks")
                if time_conflicts:
                    st.write("**Tasks Scheduled at Same Time:**")
                    st.write("- **Action:** Reschedule tasks to different time slots")
        else:
            st.success("✅ All tasks fit within available time!", icon="✅")

        st.divider()
        st.subheader("📅 Your Daily Pet Care Plan")
        if st.session_state.plan.scheduled_tasks:
            plan_data = []
            cumulative_time = 0
            for idx, task in enumerate(st.session_state.plan.scheduled_tasks, 1):
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.priority, "⚪")
                cumulative_time += task.duration
                plan_data.append({
                    "#": idx,
                    "Task": task.title,
                    "Duration (min)": task.duration,
                    "Priority": f"{priority_icon} {task.priority.upper()}",
                    "Frequency": task.frequency.upper(),
                    "Cumulative Time": cumulative_time,
                })
            st.dataframe(pd.DataFrame(plan_data), use_container_width=True, hide_index=True)
        else:
            st.info("No tasks scheduled for today.")

        st.divider()
        st.markdown("### 📋 Scheduling Reasoning")
        explanation = scheduler.explain_plan(st.session_state.plan)
        st.info(explanation)

        st.divider()
        st.subheader("📊 Schedule Summary")
        scheduler = Scheduler(owner=st.session_state.owner)
        due_tasks = scheduler.get_due_tasks()
        high_priority = scheduler.filter_by_priority("high")
        remaining_time = st.session_state.owner.time_available - st.session_state.plan.total_time

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎯 Tasks Scheduled", len(st.session_state.plan.scheduled_tasks),
                      delta=f"of {len(st.session_state.pet.tasks)} total")
        with col2:
            st.metric("⏱️ Total Time", f"{st.session_state.plan.total_time} min",
                      delta=f"of {st.session_state.owner.time_available} available")
        with col3:
            delta_text = (f"{remaining_time} min" if remaining_time >= 0
                          else f"⚠️ Over by {abs(remaining_time)} min")
            st.metric("⏳ Time Remaining", f"{remaining_time} min", delta=delta_text)
        with col4:
            st.metric("🔴 High Priority Due", len(high_priority),
                      delta="tasks to prioritize" if high_priority else "no urgent tasks")


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — AI Assistant
# ════════════════════════════════════════════════════════════════════════════
with tab_ai:

    # ── API key guard ────────────────────────────────────────────────────────
    if not os.getenv("GEMINI_API_KEY"):
        st.error("GEMINI_API_KEY not found. Add it to your .env file to use AI features.")
        st.code("GEMINI_API_KEY=your-key-here", language="bash")
    else:
        from ai_planner import parse_tasks_from_text, generate_ai_schedule, review_schedule

        # ── Demo loader ──────────────────────────────────────────────────────
        DEMO_NL = (
            "Bruno is a 3-year-old golden retriever who needs a 30-minute walk every morning — "
            "that's the most important part of his day. He also eats twice a day (breakfast and dinner), "
            "which takes about 5 minutes each time. Once a week he needs a full bath and brush-out, "
            "which takes around 45 minutes. His flea and tick medicine is monthly and only takes 2 minutes "
            "to apply, but it's really important not to forget it. He also loves a 15-minute play session "
            "with his ball in the backyard every day — low priority but good for his mood."
        )

        with st.expander("🎯 Load Demo — see the full agentic flow with one click"):
            st.caption(
                "Loads a pre-built scenario: owner Alex, dog Bruno, 90-minute time budget "
                "(just a demo default — you can change it to any amount of time). "
                "Supports multiple pets; add more after saving the first."
            )
            if st.button("Load Demo Data", use_container_width=True):
                demo_pet = Pet(name="Bruno", species="dog")
                demo_owner = Owner(name="Alex", time_available=90)
                demo_owner.add_pet(demo_pet)
                st.session_state.owner = demo_owner
                st.session_state.pet = demo_pet
                st.session_state.plan = None
                st.session_state.ai_parsed_tasks = []
                st.session_state.ai_schedule_result = None
                st.session_state.ai_review_result = None
                st.session_state.demo_nl = DEMO_NL
                st.success("Demo loaded! Owner: Alex · Pet: Bruno (dog) · 90 min budget. Now follow Steps 1–3 below.")

        st.divider()

        if st.session_state.owner is None:
            st.info("Set up an owner and pet above first, or load the demo above.")
        else:
            # ── Step 1: Natural language task entry ──────────────────────────
            st.subheader("Step 1 — Describe your pet's tasks")
            st.caption(
                "Type naturally — Gemini will extract structured tasks for you. "
                "Example: *'Max needs a 30-min walk daily and a bath every week. "
                "He takes heartworm medicine monthly — that's important.'*"
            )

            default_nl = st.session_state.get("demo_nl", "")
            nl_input = st.text_area(
                "What care does your pet need?",
                value=default_nl,
                height=120,
                placeholder="Describe tasks in plain English...",
            )

            if st.button("🔍 Parse Tasks with AI"):
                if not nl_input.strip():
                    st.warning("Enter a description first.")
                else:
                    with st.spinner("Gemini is reading your description..."):
                        parsed, parse_error = parse_tasks_from_text(
                            nl_input, st.session_state.pet.name
                        )
                    if parsed:
                        st.session_state.ai_parsed_tasks = parsed
                        st.success(f"Found {len(parsed)} task(s). Review them below.")
                    else:
                        st.error(f"Could not extract tasks. Reason: {parse_error}")

            # Show parsed tasks for review before adding
            if st.session_state.ai_parsed_tasks:
                st.write("#### Parsed Tasks — review before adding")
                parsed_df = pd.DataFrame(st.session_state.ai_parsed_tasks)
                st.dataframe(parsed_df, use_container_width=True, hide_index=True)

                col_confirm, col_clear = st.columns([1, 1])
                with col_confirm:
                    if st.button("✅ Add All to Task List", use_container_width=True):
                        added = 0
                        for t in st.session_state.ai_parsed_tasks:
                            task = Task(
                                title=t.get("title", "Untitled"),
                                duration=int(t.get("duration", 10)),
                                priority=t.get("priority", "medium"),
                                frequency=t.get("frequency", "daily"),
                            )
                            st.session_state.owner.add_task(st.session_state.pet, task)
                            added += 1
                        st.session_state.ai_parsed_tasks = []
                        st.session_state.ai_schedule_result = None
                        st.session_state.ai_review_result = None
                        st.success(f"Added {added} task(s) to {st.session_state.pet.name}'s list.")
                with col_clear:
                    if st.button("🗑️ Discard", use_container_width=True):
                        st.session_state.ai_parsed_tasks = []

            st.divider()

            # ── Step 2: AI schedule generation ──────────────────────────────
            st.subheader("Step 2 — Generate AI Schedule")

            tasks_for_schedule = st.session_state.pet.tasks if st.session_state.pet else []

            if not tasks_for_schedule:
                st.info("No tasks yet. Use Step 1 above or add tasks manually in the Manual Setup tab.")
            else:
                st.caption(
                    f"{len(tasks_for_schedule)} task(s) available · "
                    f"{st.session_state.owner.time_available} min budget"
                )

                if st.button("🤖 Generate AI Schedule", use_container_width=True):
                    task_dicts = [t.to_dict() for t in tasks_for_schedule if not t.completion_status]
                    if not task_dicts:
                        st.warning("All tasks are already marked complete.")
                    else:
                        with st.spinner("Claude is building your schedule..."):
                            result = generate_ai_schedule(
                                task_dicts,
                                st.session_state.owner.name,
                                st.session_state.pet.name,
                                st.session_state.owner.time_available,
                            )
                        st.session_state.ai_schedule_result = result
                        st.session_state.ai_review_result = None

                if st.session_state.ai_schedule_result:
                    result = st.session_state.ai_schedule_result
                    scheduled_titles = result.get("scheduled_titles", [])

                    if scheduled_titles:
                        task_map = {t.title: t for t in tasks_for_schedule}
                        sched_rows = []
                        cum = 0
                        for i, title in enumerate(scheduled_titles, 1):
                            t = task_map.get(title)
                            dur = t.duration if t else "?"
                            pri = t.priority if t else "?"
                            if isinstance(dur, int):
                                cum += dur
                            icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(pri, "⚪")
                            sched_rows.append({
                                "#": i,
                                "Task": title,
                                "Duration (min)": dur,
                                "Priority": f"{icon} {pri.upper()}" if isinstance(pri, str) else pri,
                                "Cumulative Time": cum,
                            })
                        st.write("#### 📅 AI-Generated Schedule")
                        st.dataframe(pd.DataFrame(sched_rows), use_container_width=True, hide_index=True)
                    else:
                        st.warning("No tasks could be scheduled within the time budget.")

                    col_r, col_a = st.columns(2)
                    with col_r:
                        st.write("**Why this order?**")
                        st.info(result.get("reasoning", "No reasoning provided."))
                    with col_a:
                        st.write("**Today's advice**")
                        st.success(result.get("advice", "No advice provided."))

                    warnings = result.get("warnings", [])
                    if warnings:
                        st.write("**Warnings**")
                        for w in warnings:
                            st.warning(w)

                    st.divider()

                    # ── Step 3: Agentic self-review ──────────────────────────
                    st.subheader("Step 3 — AI Self-Review")
                    st.caption(
                        "Claude checks its own schedule for problems — "
                        "missed priorities, time overflows, or gaps in care."
                    )

                    if st.button("🔎 Run Self-Review", use_container_width=True):
                        task_map = {t.title: t for t in tasks_for_schedule}
                        sched_task_dicts = [
                            task_map[title].to_dict()
                            for title in scheduled_titles
                            if title in task_map
                        ]
                        with st.spinner("Claude is reviewing the schedule..."):
                            review = review_schedule(
                                sched_task_dicts,
                                st.session_state.owner.name,
                                st.session_state.owner.time_available,
                            )
                        st.session_state.ai_review_result = review

                    if st.session_state.ai_review_result:
                        review = st.session_state.ai_review_result
                        score = review.get("score", 0)
                        approved = review.get("approved", False)
                        issues = review.get("issues", [])
                        suggestions = review.get("suggestions", [])

                        score_color = "🟢" if score >= 8 else "🟡" if score >= 5 else "🔴"
                        approval_text = "✅ Approved" if approved else "❌ Needs revision"

                        col_s, col_ap = st.columns(2)
                        with col_s:
                            st.metric("Schedule Quality Score", f"{score_color} {score} / 10")
                        with col_ap:
                            st.metric("Review Verdict", approval_text)

                        if issues:
                            st.write("**Issues found**")
                            for issue in issues:
                                st.error(f"• {issue}")
                        else:
                            st.success("No issues found.")

                        if suggestions:
                            st.write("**Suggestions**")
                            for s in suggestions:
                                st.info(f"💡 {s}")
