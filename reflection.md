# PawPal+ Project Reflection

## 1. System Design

**Core User Actions**

1. **Add a pet** — The owner enters their own info (name, available time per day) and registers a pet (name, species). This sets up the core entities the rest of the app depends on.
2. **Add and edit care tasks** — The owner creates tasks for a pet (e.g., morning walk, feeding, grooming) specifying what it is, how long it takes, when it should happen, its priority level, and how often it recurs (daily, weekly, one-time).
3. **Generate a daily schedule** — The owner requests a plan for the day. The system selects and orders tasks based on time constraints and priority, then displays the schedule with a plain-language explanation of why each task was chosen.
4. **Mark a task as complete** — The owner checks off a task once done. For recurring tasks, the system automatically creates the next occurrence.
5. **View and filter tasks** — The owner can browse tasks filtered by pet, completion status, or time of day to stay on top of what still needs to be done.

**a. Initial design**

The initial design uses four classes. `Task` (a dataclass) holds everything about a single care activity: its title, duration, scheduled time, priority, frequency (one-time/daily/weekly), completion status, and due date. `Pet` (a dataclass) owns a list of Tasks and exposes methods to add, remove, and retrieve them. `Owner` (a dataclass) owns a list of Pets and knows how many minutes per day are available; it provides a single `get_all_tasks()` aggregation method. `Scheduler` is a plain class that takes an Owner and provides the "brain" — it builds a daily schedule, sorts by time, filters by pet or status, detects time conflicts, and delegates task completion (including rescheduling recurring tasks) back to the Task.

**b. Design changes**

During implementation, three methods were added beyond the original skeleton: `build_priority_schedule()` on Scheduler (sorts by priority first, then time, giving owners a second scheduling mode), `find_next_available_slot()` on Scheduler (scans from 07:00 in 30-minute increments to suggest the next free time slot), and `save_to_json()` / `load_from_json()` on Owner (persist all data between sessions). The `Task` class also gained `to_dict()` / `from_dict()` helpers to support JSON serialisation. These additions were driven by the bonus requirements rather than a flaw in the original design.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints: (1) the owner's daily time budget — tasks are added to the schedule only if the running total of minutes stays within the available limit; (2) scheduled time — tasks are sorted chronologically so the plan reads like a real day; (3) completion status — already-completed tasks are excluded from the daily schedule. Priority (low/medium/high) is stored on each task and surfaced in both modes — the standard schedule sorts by time, while the priority schedule sorts high → medium → low first, then by time within each band.

**b. Tradeoffs**

The conflict detector flags any two tasks that share the exact same `scheduled_time` string (e.g., both at "15:00"). It does **not** check for overlapping durations — two tasks at 14:50 and 15:00 with 30-minute durations would silently overlap. This tradeoff keeps the logic simple and fast (a single dictionary scan) while still catching the most common mistake (accidentally double-booking a time slot). For a first version serving a single pet owner with coarse scheduling, exact-match detection is a reasonable baseline.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used across every phase: generating the initial Mermaid UML from brainstormed class descriptions, producing Python dataclass skeletons, fleshing out method logic (especially the `timedelta` recurrence pattern and `sorted()` lambda for time-based sorting), drafting pytest test functions, writing docstrings, and connecting the Streamlit UI to the backend. The most effective prompts were specific and file-referenced — e.g., "based on these skeletons, how should Scheduler retrieve all tasks from Owner's pets?" — rather than open-ended requests. Keeping each chat session focused on one phase (design, implementation, testing) also prevented context drift and kept suggestions relevant.

**b. Judgment and verification**

The AI initially suggested making `Scheduler` methods `@staticmethod` since they could technically operate without `self`. This was rejected because the scheduler's whole purpose is to be bound to a specific `Owner` — making it stateless would push that binding responsibility onto every call site and make the class harder to extend later. The suggestion was verified by tracing how `build_schedule()` and `filter_tasks()` both depend on `self.owner`, confirming the instance binding was correct. A second moment: the AI suggested using `marshmallow` for JSON serialisation. This was rejected in favour of simple `to_dict()` / `from_dict()` class methods — marshmallow adds a dependency and schema layer that is unnecessary for four straightforward dataclasses.

---

## 4. Testing and Verification

**a. What you tested**

Seven behaviours were tested: (1) task completion status change via `mark_complete()`, (2) pet task count increases after `add_task()`, (3) tasks are returned in chronological order by `sort_by_time()`, (4) marking a daily task complete creates a follow-up task due the next day, (5) marking a one-time task complete returns `None` (no follow-up), (6) two tasks at the same time produce a conflict warning, and (7) tasks at different times produce no warnings. These tests matter because they cover the core contract of every class — if any break, the scheduler's output cannot be trusted.

**b. Confidence**

⭐⭐⭐⭐ (4/5). The happy paths and most common edge cases are covered. Next tests would target: a pet with zero tasks (empty schedule), budget exactly equal to total task duration (boundary condition), weekly recurrence producing the correct +7-day date, overlapping-duration conflicts that the current detector misses, and JSON round-trip fidelity (save then load produces identical objects).

---

## 5. Reflection

**a. What went well**

The clean separation between `pawpal_system.py` (pure logic, no UI) and `app.py` (pure UI, no business logic) made both easier to build and test independently. The `Scheduler.mark_task_complete()` method delegating recurrence back through the owner's pet list was a satisfying design — the UI only has to call one method and the whole chain (complete → reschedule → attach to pet) happens automatically. The test suite catching real behaviour (not just structure) gave genuine confidence before wiring up the UI.

**b. What you would improve**

The current session state is in-memory only during a Streamlit session, and while JSON persistence saves between runs, there is no support for multiple owners or user accounts. A next iteration would add a proper data layer (SQLite via `sqlite3` or a lightweight ORM) and upgrade conflict detection to check overlapping durations rather than just identical start times.

**c. Key takeaway**

AI tools are most useful when you already have a clear design — they accelerate implementation but rarely improve architecture on their own. Acting as the "lead architect" meant setting the class boundaries and responsibilities first, then letting AI fill in the method bodies. Accepting every AI suggestion without that prior structure would have produced working but poorly organised code that is hard to test or extend. The most valuable skill was knowing when to push back on a suggestion and why.

---

## 6. Prompt Comparison (Bonus Challenge 5)

**Task:** Implement the weekly task rescheduling logic — when a weekly task is marked complete, create a new task due exactly 7 days later.

**Prompt used:** "Given a Task dataclass with a `due_date: date` field and a `frequency` of 'weekly', write a `reschedule()` method that returns a new Task instance with `due_date = due_date + 7 days` and `is_complete = False`. Use Python's `timedelta`."

**Claude (Sonnet)** returned a clean `if/elif` branch inside `reschedule()` using `timedelta(weeks=1)` and a dataclass copy pattern. It also noted the edge case where `due_date` might be `None` and suggested `self.due_date or date.today()` as a safe fallback — which was adopted as-is.

**GPT-4o** produced the same core logic but wrapped it in a separate helper method `_next_date()` and used `timedelta(days=7)` instead of `timedelta(weeks=1)`. The extra helper added indirection without benefit for a single-use calculation.

**Winner: Claude.** The `timedelta(weeks=1)` form is more readable and communicates intent directly. The `None`-guard suggestion was also more Pythonic than GPT-4o's approach of raising a `ValueError` for a missing date. For utility methods like this, the simpler, more self-documenting solution is better.
