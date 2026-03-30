from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


# --- Helpers ---

def make_task(title="Walk", time="09:00", priority="medium", duration=20, frequency="one-time"):
    return Task(
        title=title,
        duration_minutes=duration,
        priority=priority,
        scheduled_time=time,
        frequency=frequency,
        due_date=date.today(),
    )


def make_owner_with_pet():
    owner = Owner(name="Jordan", available_minutes_per_day=120)
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    return owner, pet


# --- Task Completion ---

def test_mark_complete_changes_status():
    """Calling mark_complete() sets is_complete to True."""
    task = make_task()
    assert task.is_complete is False
    task.mark_complete()
    assert task.is_complete is True


# --- Task Addition ---

def test_add_task_increases_count():
    """Adding a task to a Pet increases its task count."""
    _, pet = make_owner_with_pet()
    assert len(pet.get_tasks()) == 0
    pet.add_task(make_task("Walk"))
    assert len(pet.get_tasks()) == 1
    pet.add_task(make_task("Feed"))
    assert len(pet.get_tasks()) == 2


# --- Sorting ---

def test_sort_by_time_returns_chronological_order():
    """Tasks added out of order are returned sorted by scheduled_time."""
    owner, pet = make_owner_with_pet()
    pet.add_task(make_task("Evening feed", time="18:00"))
    pet.add_task(make_task("Morning walk", time="07:30"))
    pet.add_task(make_task("Medication", time="08:00"))

    scheduler = Scheduler(owner)
    sorted_tasks = scheduler.sort_by_time(pet.get_tasks())

    times = [t.scheduled_time for t in sorted_tasks]
    assert times == sorted(times), f"Expected sorted times, got {times}"


# --- Recurrence ---

def test_daily_task_creates_next_occurrence_after_complete():
    """Marking a daily task complete creates a new task for the following day."""
    owner, pet = make_owner_with_pet()
    today = date.today()
    task = Task(
        title="Morning walk",
        duration_minutes=20,
        priority="high",
        scheduled_time="07:30",
        frequency="daily",
        due_date=today,
    )
    pet.add_task(task)

    scheduler = Scheduler(owner)
    next_task = scheduler.mark_task_complete(task)

    assert next_task is not None, "Expected a follow-up task for a daily task"
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.is_complete is False
    assert next_task.title == task.title


def test_onetime_task_returns_no_next_occurrence():
    """Marking a one-time task complete does not create a follow-up."""
    owner, pet = make_owner_with_pet()
    task = make_task(frequency="one-time")
    pet.add_task(task)

    scheduler = Scheduler(owner)
    next_task = scheduler.mark_task_complete(task)

    assert next_task is None


# --- Conflict Detection ---

def test_detect_conflicts_flags_same_time():
    """Two tasks at the same scheduled_time should produce a conflict warning."""
    owner, pet = make_owner_with_pet()
    pet.add_task(make_task("Walk", time="09:00"))
    pet.add_task(make_task("Vet", time="09:00"))

    scheduler = Scheduler(owner)
    warnings = scheduler.detect_conflicts(pet.get_tasks())

    assert len(warnings) == 1
    assert "09:00" in warnings[0]


def test_detect_conflicts_no_warning_when_times_differ():
    """Tasks at different times should produce no conflict warnings."""
    owner, pet = make_owner_with_pet()
    pet.add_task(make_task("Walk", time="08:00"))
    pet.add_task(make_task("Vet", time="09:00"))

    scheduler = Scheduler(owner)
    warnings = scheduler.detect_conflicts(pet.get_tasks())

    assert warnings == []
