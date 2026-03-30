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

## 📸 Demo

<a href="/course_images/ai110/pawpal_screenshot.png" target="_blank"><img src='/course_images/ai110/pawpal_screenshot.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

> To add your screenshot: run `streamlit run app.py`, take a screenshot, save it as `pawpal_screenshot.png` in your project folder, and update the path above.

## Features

- **Owner & pet setup** — register an owner with a daily time budget and any number of pets
- **Task management** — add tasks per pet with title, duration, priority, scheduled time, and recurrence
- **Time-sorted schedule** — daily plan ordered chronologically with budget enforcement
- **Priority color-coding** — 🔴 High / 🟡 Medium / 🟢 Low at a glance
- **Conflict detection** — flags tasks sharing the same start time with actionable warnings
- **Recurring tasks** — daily/weekly tasks auto-generate their next occurrence on completion
- **Next available slot** — finds the earliest free time slot for a new task
- **Priority-first scheduling** — optional schedule sorted by priority then time
- **JSON persistence** — save and reload all pets and tasks between sessions

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
