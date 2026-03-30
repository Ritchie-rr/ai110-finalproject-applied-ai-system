from dataclasses import dataclass, field


@dataclass
class Pet:
    name: str
    species: str
    preferences: list[str] = field(default_factory=list)


@dataclass
class Task:
    title: str
    duration: int          # in minutes
    priority: str          # "low", "medium", "high"
    notes: str = ""


class DailyPlan:
    def __init__(self):
        self.scheduled_tasks: list[Task] = []
        self.total_time: int = 0
        self.reasoning: str = ""

    def display(self):
        pass

    def to_dict(self):
        pass


class Owner:
    def __init__(self, name: str, time_available: int, preferences: list[str] = None):
        self.name = name
        self.time_available = time_available  # in minutes
        self.preferences: list[str] = preferences or []
        self.pet: Pet = None
        self.tasks: list[Task] = []

    def add_task(self, task: Task):
        pass


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.tasks: list[Task] = []

    def generate_plan(self) -> DailyPlan:
        pass

    def explain_plan(self, plan: DailyPlan) -> str:
        pass
