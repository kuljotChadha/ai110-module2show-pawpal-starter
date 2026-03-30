from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from typing import Optional


@dataclass
class Task:
    """Represents a single pet care activity."""

    title: str
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    scheduled_time: str = "09:00"  # HH:MM format
    description: str = ""
    frequency: str = "one-time"  # "one-time", "daily", "weekly"
    is_complete: bool = False
    due_date: Optional[date] = None

    def mark_complete(self) -> None:
        """Mark this task as complete."""
        self.is_complete = True

    def reschedule(self) -> Optional["Task"]:
        """Create the next occurrence for a recurring task. Returns None for one-time tasks."""
        if self.frequency == "one-time":
            return None
        base = self.due_date or date.today()
        if self.frequency == "daily":
            next_date = base + timedelta(days=1)
        else:  # weekly
            next_date = base + timedelta(weeks=1)
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            scheduled_time=self.scheduled_time,
            description=self.description,
            frequency=self.frequency,
            is_complete=False,
            due_date=next_date,
        )

    def to_dict(self) -> dict:
        """Serialise to a JSON-safe dictionary."""
        d = asdict(self)
        d["due_date"] = self.due_date.isoformat() if self.due_date else None
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Deserialise from a dictionary."""
        if data.get("due_date"):
            data["due_date"] = date.fromisoformat(data["due_date"])
        return cls(**data)


@dataclass
class Pet:
    """Stores pet details and owns its list of care tasks."""

    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet."""
        self.tasks.remove(task)

    def get_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        return list(self.tasks)

    def to_dict(self) -> dict:
        """Serialise to a JSON-safe dictionary."""
        return {"name": self.name, "species": self.species, "tasks": [t.to_dict() for t in self.tasks]}

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """Deserialise from a dictionary."""
        tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        return cls(name=data["name"], species=data["species"], tasks=tasks)


@dataclass
class Owner:
    """Manages one or more pets and tracks daily time availability."""

    name: str
    available_minutes_per_day: int = 120
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all pets."""
        all_tasks: list[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks

    def save_to_json(self, filepath: str) -> None:
        """Persist the owner, all pets, and all tasks to a JSON file."""
        data = {
            "name": self.name,
            "available_minutes_per_day": self.available_minutes_per_day,
            "pets": [p.to_dict() for p in self.pets],
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_json(cls, filepath: str) -> "Owner":
        """Load an Owner (with all pets and tasks) from a JSON file."""
        with open(filepath) as f:
            data = json.load(f)
        pets = [Pet.from_dict(p) for p in data.get("pets", [])]
        return cls(
            name=data["name"],
            available_minutes_per_day=data["available_minutes_per_day"],
            pets=pets,
        )


class Scheduler:
    """Retrieves, organises, and manages tasks across an owner's pets."""

    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def build_schedule(self) -> list[Task]:
        """Return today's pending tasks sorted by time, respecting the owner's daily budget."""
        pending = [t for t in self.owner.get_all_tasks() if not t.is_complete]
        sorted_tasks = self.sort_by_time(pending)
        schedule: list[Task] = []
        minutes_used = 0
        for task in sorted_tasks:
            if minutes_used + task.duration_minutes <= self.owner.available_minutes_per_day:
                schedule.append(task)
                minutes_used += task.duration_minutes
        return schedule

    def build_priority_schedule(self) -> list[Task]:
        """Return today's pending tasks sorted by priority first, then by time.

        High-priority tasks are always scheduled before medium, then low — within
        each priority band tasks are ordered chronologically.
        """
        pending = [t for t in self.owner.get_all_tasks() if not t.is_complete]
        sorted_tasks = sorted(
            pending,
            key=lambda t: (self.PRIORITY_ORDER.get(t.priority, 9), t.scheduled_time),
        )
        schedule: list[Task] = []
        minutes_used = 0
        for task in sorted_tasks:
            if minutes_used + task.duration_minutes <= self.owner.available_minutes_per_day:
                schedule.append(task)
                minutes_used += task.duration_minutes
        return schedule

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted chronologically by scheduled_time (HH:MM)."""
        return sorted(tasks, key=lambda t: t.scheduled_time)

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        status: Optional[bool] = None,
    ) -> list[Task]:
        """Filter tasks by pet name and/or completion status.

        Args:
            pet_name: If given, only return tasks belonging to this pet.
            status: If given, only return tasks where is_complete equals this value.
        """
        result: list[Task] = []
        for pet in self.owner.pets:
            if pet_name and pet.name.lower() != pet_name.lower():
                continue
            for task in pet.get_tasks():
                if status is not None and task.is_complete != status:
                    continue
                result.append(task)
        return result

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Return warning strings for any two tasks scheduled at the same time."""
        seen: dict[str, Task] = {}
        warnings: list[str] = []
        for task in tasks:
            if task.scheduled_time in seen:
                other = seen[task.scheduled_time]
                warnings.append(
                    f"Conflict at {task.scheduled_time}: '{other.title}' and '{task.title}' overlap."
                )
            else:
                seen[task.scheduled_time] = task
        return warnings

    def find_next_available_slot(self, duration_minutes: int) -> str:
        """Return the earliest HH:MM slot that fits a task of the given duration.

        Scans from 07:00 in 30-minute increments and returns the first slot not
        already occupied by a scheduled task.
        """
        booked_times = {t.scheduled_time for t in self.owner.get_all_tasks() if not t.is_complete}
        start_hour, start_minute = 7, 0
        for _ in range(48):  # scan up to midnight (48 × 30 min)
            slot = f"{start_hour:02d}:{start_minute:02d}"
            if slot not in booked_times:
                return slot
            start_minute += 30
            if start_minute >= 60:
                start_minute = 0
                start_hour += 1
            if start_hour >= 24:
                break
        return "23:30"  # fallback if somehow fully booked

    def mark_task_complete(self, task: Task) -> Optional[Task]:
        """Mark a task complete and, for recurring tasks, add the next occurrence to the pet.

        Returns the newly created follow-up Task, or None for one-time tasks.
        """
        task.mark_complete()
        next_task = task.reschedule()
        if next_task:
            for pet in self.owner.pets:
                if task in pet.tasks:
                    pet.add_task(next_task)
                    break
        return next_task
