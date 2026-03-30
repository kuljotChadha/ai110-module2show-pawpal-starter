# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Agent Mode Usage

Several bonus features were implemented using Agent Mode (multi-step AI-assisted implementation across files):

- **Next available slot** — Agent Mode was used to design `Scheduler.find_next_available_slot()`: it scans from 07:00 in 30-minute increments, checks occupied times across all pets, and returns the first free slot. The agent also updated `app.py` to pre-fill the time input with the suggested slot.
- **JSON persistence** — Agent Mode orchestrated changes across both `pawpal_system.py` (adding `to_dict`/`from_dict` to `Task` and `Pet`, and `save_to_json`/`load_from_json` to `Owner`) and `app.py` (loading from `data.json` on startup, auto-saving on every mutation).
- **Priority-based scheduling** — Agent Mode added `build_priority_schedule()` to `Scheduler` and wired a radio toggle in the UI so the user can switch between chronological and priority-first modes.

## Smarter Scheduling

PawPal+ goes beyond a simple task list with these built-in algorithms:

- **Time-sorted schedule** — tasks are ordered chronologically (HH:MM) so the daily plan reads like a real timeline.
- **Daily budget enforcement** — the scheduler only adds tasks until the owner's available minutes are used up; lower-priority tasks that don't fit are silently deferred.
- **Recurring task automation** — marking a `daily` or `weekly` task complete automatically generates the next occurrence with the correct due date using Python's `timedelta`.
- **Conflict detection** — the scheduler scans for tasks with identical scheduled times and returns plain-language warnings rather than crashing.
- **Filtering** — tasks can be filtered by pet name and/or completion status, making it easy to see what's still pending for a specific pet.

## Testing PawPal+

Run the automated test suite with:

```bash
python -m pytest
```

Tests cover:

- **Task completion** — `mark_complete()` correctly flips `is_complete` to `True`
- **Task addition** — adding a task to a `Pet` increases its task count
- **Sorting correctness** — tasks are returned in chronological order
- **Recurrence logic** — marking a daily task complete creates a new task for the following day
- **Conflict detection** — the Scheduler correctly flags two tasks at the same time

**Confidence level: ⭐⭐⭐⭐ (4/5)** — core behaviors are verified; overlap-duration conflicts and edge cases (empty pets, budget of 0) would be the next test targets.

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
