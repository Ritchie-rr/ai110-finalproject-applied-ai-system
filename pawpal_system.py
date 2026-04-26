from dataclasses import dataclass, field
from enum import Enum
from datetime import date, timedelta


class Priority(Enum):
    """Priority levels for tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Frequency(Enum):
    """Frequency of task repetition."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    AS_NEEDED = "as_needed"


@dataclass
class Task:
    """Represents a single pet care activity."""
    title: str
    duration: int                          # in minutes
    priority: str                          # "low", "medium", "high"
    frequency: str = "daily"               # "daily", "weekly", "monthly", "as_needed"
    completion_status: bool = False        # has task been completed today?
    notes: str = ""
    last_completed: date = None            # tracks when task was last completed
    scheduled_time: str = None             # time in HH:MM format (e.g., "09:00")
    next_due_date: date = None             # when this task will be due next

    def mark_complete(self):
        """Mark this task as completed and record the date."""
        self.completion_status = True
        self.last_completed = date.today()
        # Calculate next due date based on frequency using timedelta
        self.next_due_date = self._calculate_next_due_date()

    def _calculate_next_due_date(self) -> date:
        """Calculate when this task will be due next using timedelta.
        
        Uses Python's timedelta to accurately add days:
        - Daily tasks: today + 1 day
        - Weekly tasks: today + 7 days
        - Monthly tasks: today + 30 days
        - As-needed tasks: no automatic due date (None)
        """
        if self.frequency == Frequency.DAILY.value:
            return date.today() + timedelta(days=1)
        elif self.frequency == Frequency.WEEKLY.value:
            return date.today() + timedelta(days=7)
        elif self.frequency == Frequency.MONTHLY.value:
            return date.today() + timedelta(days=30)
        else:  # as_needed
            return None  # no automatic due date

    def mark_incomplete(self):
        """Mark this task as not completed."""
        self.completion_status = False

    def to_dict(self) -> dict:
        """Serialize to a plain dict for passing to the AI planner."""
        return {
            "title": self.title,
            "duration": self.duration,
            "priority": self.priority,
            "frequency": self.frequency,
            "completed": self.completion_status,
            "notes": self.notes,
        }

    def __repr__(self) -> str:
        status = "✓" if self.completion_status else "○"
        return f"{status} {self.title} ({self.duration}min) [{self.priority}]"


@dataclass
class Pet:
    """Stores pet details and manages their associated tasks."""
    name: str
    species: str
    preferences: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task: Task):
        """Remove a task from this pet's task list."""
        if task in self.tasks:
            self.tasks.remove(task)

    def get_incomplete_tasks(self) -> list[Task]:
        """Get all incomplete tasks for this pet."""
        return [task for task in self.tasks if not task.completion_status]

    def __repr__(self) -> str:
        return f"Pet({self.name}, {self.species}, {len(self.tasks)} tasks)"


class DailyPlan:
    """Represents a scheduled daily plan for pet care."""
    def __init__(self):
        self.scheduled_tasks: list[Task] = []
        self.total_time: int = 0
        self.reasoning: dict[str, str] = {}  # task title -> reason

    def add_task(self, task: Task, reason: str = ""):
        """Add a task to the plan with optional reasoning."""
        self.scheduled_tasks.append(task)
        self.total_time += task.duration
        if reason:
            self.reasoning[task.title] = reason

    def display(self) -> str:
        """Return a formatted string representation of the plan."""
        if not self.scheduled_tasks:
            return "No tasks scheduled."

        lines = ["=== Daily Pet Care Plan ==="]
        for i, task in enumerate(self.scheduled_tasks, 1):
            lines.append(f"{i}. {task.title}")
            lines.append(f"   ├─ Duration: {task.duration} min")
            lines.append(f"   ├─ Priority: {task.priority}")
            lines.append(f"   └─ Frequency: {task.frequency}")
        lines.append(f"\nTotal Time: {self.total_time} minutes")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert the plan to a dictionary."""
        return {
            "scheduled_tasks": [
                {
                    "title": task.title,
                    "duration": task.duration,
                    "priority": task.priority,
                    "frequency": task.frequency,
                    "completed": task.completion_status,
                    "notes": task.notes,
                }
                for task in self.scheduled_tasks
            ],
            "total_time": self.total_time,
            "reasoning": self.reasoning,
        }


class Owner:
    """Manages pets and provides access to all their tasks."""
    def __init__(self, name: str, time_available: int, preferences: list[str] = None):
        self.name = name
        self.time_available = time_available  # in minutes
        self.preferences: list[str] = preferences or []
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet):
        """Add a pet to the owner's list."""
        self.pets.append(pet)

    def remove_pet(self, pet: Pet):
        """Remove a pet from the owner's list."""
        if pet in self.pets:
            self.pets.remove(pet)

    def add_task(self, pet: Pet, task: Task):
        """Add a task to a specific pet."""
        if pet in self.pets:
            pet.add_task(task)

    def get_all_tasks(self) -> list[Task]:
        """Retrieve all tasks from all pets."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def get_incomplete_tasks(self) -> list[Task]:
        """Get all incomplete tasks across all pets."""
        incomplete = []
        for pet in self.pets:
            incomplete.extend(pet.get_incomplete_tasks())
        return incomplete

    def __repr__(self) -> str:
        return f"Owner({self.name}, {len(self.pets)} pets, {self.time_available}min available)"


class Scheduler:
    """The "brain" that retrieves, organizes, and manages tasks across pets."""
    def __init__(self, owner: Owner):
        self.owner = owner

    def _is_due(self, task: Task, today: date = None) -> bool:
        """Check if a task is due based on its frequency and last completion date.
        
        Algorithm: Examines task frequency and compares days since last completion.
        
        Args:
            task: The Task to evaluate
            today: Reference date (default: today)
            
        Returns:
            bool: True if task is due today, False otherwise
            
        Logic:
            - DAILY: Always due (every day)
            - WEEKLY: Due if >= 7 days since last completion
            - MONTHLY: Due if >= 30 days since last completion
            - AS_NEEDED: Always due (no automatic schedule)
            
        Example:
            >>> task_daily = Task('Feed', 5, 'daily', frequency='daily')
            >>> scheduler._is_due(task_daily)  # True, daily tasks always due
            >>> task_weekly = Task('Vet Check', 30, 'high', frequency='weekly', last_completed=date(2026,3,23))
            >>> scheduler._is_due(task_weekly, date(2026, 3, 30))  # True, 7 days passed
        """
        today = today or date.today()
        
        if task.frequency == Frequency.DAILY.value:
            return True
        if task.frequency == Frequency.WEEKLY.value:
            return task.last_completed is None or (today - task.last_completed).days >= 7
        if task.frequency == Frequency.MONTHLY.value:
            return task.last_completed is None or (today - task.last_completed).days >= 30
        return True  # as_needed tasks are always due

    def get_due_tasks(self, today: date = None) -> list[Task]:
        """Retrieve all incomplete tasks that are due today.
        
        Pure filtering operation: examines all incomplete tasks and returns only
        those whose frequency schedule indicates they are due on the given date.
        Used as input to generate_plan() for intelligent daily scheduling.
        
        Args:
            today: Reference date for checking due dates (default: today)
            
        Returns:
            list[Task]: All incomplete tasks whose frequency indicates they're due
            
        Example:
            >>> plan = scheduler.generate_plan()
            >>> # Internally calls: due_tasks = scheduler.get_due_tasks()
            >>> due_tasks = scheduler.get_due_tasks()
            >>> len(due_tasks)  # Number of tasks that need scheduling today
        """
        today = today or date.today()
        return [t for t in self.owner.get_incomplete_tasks() if self._is_due(t, today)]

    def filter_by_priority(self, priority: str) -> list[Task]:
        """Filter all incomplete tasks by priority level.
        
        Utility method for viewing tasks by priority without scheduling.
        Useful for dashboards, reporting, and priority-based task review.
        
        Args:
            priority: Priority level as string ("low", "medium", "high")
                      Suggest: use Priority enum values for type safety
                      
        Returns:
            list[Task]: All incomplete tasks matching the specified priority
            
        Example:
            >>> high_priority = scheduler.filter_by_priority("high")
            >>> for task in high_priority:
            ...     print(f"Urgent: {task.title}")  # Show urgent tasks
            >>> medium_task_count = len(scheduler.filter_by_priority("medium"))
        """
        return [t for t in self.owner.get_incomplete_tasks() if t.priority == priority]

    def sort_by_time(self, tasks: list[Task] = None) -> list[Task]:
        """
        Sort tasks by their scheduled_time attribute in HH:MM format.
        
        Returns tasks sorted chronologically:
        1. Scheduled tasks (earliest first)
        2. Unscheduled tasks (no scheduled_time)
        
        IMPROVEMENTS over original:
        - Uses explicit constants (SCHEDULED, UNSCHEDULED) for readability
        - Caches time conversions to avoid repeated parsing
        - Uses explicit unpacking instead of map()
        - More Pythonic and maintainable
        
        Example:
            sorted_tasks = scheduler.sort_by_time(owner_tasks)
        """
        if tasks is None:
            tasks = self.owner.get_incomplete_tasks()
        
        # Constants for tuple sorting (clearer intent than True/False)
        SCHEDULED = 0
        UNSCHEDULED = 1
        MAX_TIME = 1440  # 24 hours in minutes (sentinel value instead of inf)
        
        def time_to_sort_key(task: Task) -> tuple:
            """Convert task's scheduled_time to sortable tuple.
            
            Returns: (priority, minutes_since_midnight)
            - Priority 0: scheduled tasks (sorted by time)
            - Priority 1: unscheduled tasks (at end)
            """
            if not task.scheduled_time:
                return (UNSCHEDULED, MAX_TIME)
            
            try:
                # Explicit unpacking is more readable than map()
                hour, minute = task.scheduled_time.split(':')
                total_minutes = int(hour) * 60 + int(minute)
                return (SCHEDULED, total_minutes)
            except (ValueError, TypeError):
                # Invalid format or None - treat as unscheduled
                return (UNSCHEDULED, MAX_TIME)
        
        return sorted(tasks, key=time_to_sort_key)

    def detect_conflicts(self, plan: DailyPlan) -> list[str]:
        """Detect which tasks exceed available time and return conflict messages."""
        conflicts = []
        total = 0
        for task in plan.scheduled_tasks:
            total += task.duration
            if total > self.owner.time_available:
                conflicts.append(f"'{task.title}' exceeds available time ({total}min > {self.owner.time_available}min)")
        return conflicts

    def detect_time_conflicts(self, tasks: list[Task] = None) -> list[str]:
        """
        Lightweight conflict detection: identify if two tasks are scheduled at the same time.
        
        Returns a list of warning messages without crashing.
        Works across all pets - detects overlaps regardless of pet ownership.
        
        Example:
            conflicts = scheduler.detect_time_conflicts()
            if conflicts:
                for warning in conflicts:
                    print(f"⚠️  {warning}")
        """
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        
        conflicts = []
        
        # Filter to only tasks with scheduled_time
        scheduled_tasks = [t for t in tasks if t.scheduled_time is not None]
        
        if not scheduled_tasks:
            return conflicts  # No scheduled tasks, no conflicts
        
        # Group tasks by scheduled_time
        time_groups: dict[str, list[Task]] = {}
        for task in scheduled_tasks:
            if task.scheduled_time not in time_groups:
                time_groups[task.scheduled_time] = []
            time_groups[task.scheduled_time].append(task)
        
        # Check for conflicts: if multiple tasks at same time
        for time_slot, tasks_at_time in time_groups.items():
            if len(tasks_at_time) > 1:
                task_titles = [t.title for t in tasks_at_time]
                task_list = ", ".join(f"'{title}'" for title in task_titles)
                conflicts.append(f"⏰ TIME CONFLICT at {time_slot}: {task_list} are scheduled simultaneously")
        
        return conflicts

    def generate_plan(self) -> DailyPlan:
        """Generate an optimized daily plan based on time constraints and priorities.
        
        Core Scheduling Algorithm (Greedy):
        
        1. Retrieve all tasks due today via get_due_tasks()
        2. Sort tasks by: (priority_order, duration)
           - High priority → Medium priority → Low priority
           - Within priority tier: shorter tasks before longer ones
        3. Fit tasks into available time in sorted order
           - If task fits within remaining time: add to plan
           - If insufficient time: skip task, record reason
        4. Return plan with scheduled tasks and reasoning
        
        Trade-off Justification:
        Uses O(n log n) greedy algorithm instead of globally optimal bin-packing.
        Real-world pet owners need instant daily plans; optimal scheduling would
        require exponential time (NP-hard) and is overkill for pet care.
        
        Returns:
            DailyPlan: Scheduled tasks, total time used, and reasoning for each decision
            
        Example:
            >>> plan = scheduler.generate_plan()
            >>> print(f"Scheduled {len(plan.scheduled_tasks)} tasks")
            >>> print(scheduler.explain_plan(plan))
        """
        plan = DailyPlan()
        
        # Get all incomplete tasks that are due today
        all_tasks = self.get_due_tasks()
        
        if not all_tasks:
            return plan
        
        # Sort tasks by priority using the Priority enum: high > medium > low, then by duration
        priority_order = {Priority.HIGH.value: 0, Priority.MEDIUM.value: 1, Priority.LOW.value: 2}
        sorted_tasks = sorted(
            all_tasks,
            key=lambda t: (priority_order.get(t.priority, 3), t.duration)
        )
        
        # Fit tasks into available time
        remaining_time = self.owner.time_available
        for task in sorted_tasks:
            if remaining_time >= task.duration:
                plan.add_task(task, reason=f"Priority: {task.priority}")
                remaining_time -= task.duration
            else:
                if remaining_time > 0:
                    plan.reasoning[task.title] = f"Insufficient time (need {task.duration}min, have {remaining_time}min)"
        
        return plan

    def explain_plan(self, plan: DailyPlan) -> str:
        """Generate a detailed textual explanation of scheduling decisions.
        
        Transparency tool: shows owner why tasks were included or excluded.
        Helps users understand scheduler logic and build trust in the system.
        
        Args:
            plan: DailyPlan object to explain (typically from generate_plan())
            
        Returns:
            str: Multi-line explanation including:
                 - Owner name and available time
                 - Number of scheduled tasks
                 - Time remaining or overage warning
                 - Individual task breakdown with priorities and reasons
                 
        Example:
            >>> plan = scheduler.generate_plan()
            >>> explanation = scheduler.explain_plan(plan)
            >>> print(explanation)
            Plan for Sarah
            Available time: 120 minutes
            Scheduled tasks: 3
            Total time used: 85 minutes
            ✓ Time remaining: 35 minutes
            
            Task breakdown:
              • Feed Max: 10min (high)
              • Walk Max: 30min (high) Priority: high
              • Grooming: 45min (medium) Priority: medium
        """
        if not plan.scheduled_tasks:
            return f"No tasks could be scheduled. {self.owner.name} has {self.owner.time_available} minutes available."
        
        lines = [
            f"Plan for {self.owner.name}",
            f"Available time: {self.owner.time_available} minutes",
            f"Scheduled tasks: {len(plan.scheduled_tasks)}",
            f"Total time used: {plan.total_time} minutes",
            ""
        ]
        
        if plan.total_time > self.owner.time_available:
            lines.append(f"⚠ Warning: Plan exceeds available time by {plan.total_time - self.owner.time_available} minutes")
        else:
            lines.append(f"✓ Time remaining: {self.owner.time_available - plan.total_time} minutes")
        
        lines.append("\nTask breakdown:")
        for task in plan.scheduled_tasks:
            reason = plan.reasoning.get(task.title, "")
            lines.append(f"  • {task.title}: {task.duration}min ({task.priority}) {reason}")
        
        return "\n".join(lines)
