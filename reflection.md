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

- No changes yet — skeleton committed, implementation pending.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints: (1) the owner's daily time budget — tasks are added to the schedule only if the running total of minutes stays within the available limit; (2) scheduled time — tasks are sorted chronologically so the plan reads like a real day; (3) completion status — already-completed tasks are excluded from the daily schedule. Priority (low/medium/high) is stored on each task and surfaced in the UI, but the current scheduler fills the day by time-order rather than strictly by priority, keeping the plan predictable for the owner.

**b. Tradeoffs**

The conflict detector flags any two tasks that share the exact same `scheduled_time` string (e.g., both at "15:00"). It does **not** check for overlapping durations — two tasks at 14:50 and 15:00 with 30-minute durations would silently overlap. This tradeoff keeps the logic simple and fast (a single dictionary scan) while still catching the most common mistake (accidentally double-booking a time slot). For a first version serving a single pet owner with coarse scheduling, exact-match detection is a reasonable baseline.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used across every phase: generating the initial Mermaid UML from brainstormed class descriptions, producing Python dataclass skeletons, fleshing out method logic (especially the `timedelta` recurrence pattern and `sorted()` lambda), drafting pytest test functions, and writing docstrings. The most effective prompts were specific and file-referenced — e.g., "based on these skeletons, how should Scheduler retrieve all tasks from Owner's pets?" — rather than open-ended "build me an app" prompts.

**b. Judgment and verification**

The AI initially suggested making `Scheduler` methods `@staticmethod` since they could technically operate without `self`. This was rejected because the scheduler's whole purpose is to be bound to a specific `Owner` — making it stateless would push that binding responsibility onto every call site and make the class harder to extend later. The suggestion was verified by tracing how `build_schedule` and `filter_tasks` both depend on `self.owner`, confirming the instance binding was correct.

---

## 4. Testing and Verification

**a. What you tested**

Seven behaviors were tested: task completion status change, pet task count after addition, chronological sort order, daily recurrence (next task created for tomorrow), one-time task produces no follow-up, conflict detection flags duplicate times, and conflict detection produces no warning when times differ. These tests matter because they cover the core contract of each class — if any of them break, the scheduler's output cannot be trusted.

**b. Confidence**

⭐⭐⭐⭐ (4/5). The happy paths and most common edge cases are covered. Next tests would target: a pet with zero tasks (empty schedule), budget exactly equal to total task duration (boundary condition), weekly recurrence producing correct +7-day date, and overlapping durations that the current conflict detector misses.

---

## 6. Prompt Comparison (Bonus Challenge 5)

**Task:** Implement the weekly task rescheduling logic — when a weekly task is marked complete, create a new task due exactly 7 days later.

**Prompt used:** "Given a Task dataclass with a `due_date: date` field and a `frequency` of 'weekly', write a `reschedule()` method that returns a new Task instance with `due_date = due_date + 7 days` and `is_complete = False`. Use Python's `timedelta`."

**Claude (Sonnet)** returned a clean `if/elif` branch inside `reschedule()` using `timedelta(weeks=1)` and a dataclass copy pattern. It also noted the edge case where `due_date` might be `None` and suggested `self.due_date or date.today()` as a safe fallback — which was adopted as-is.

**GPT-4o** produced the same core logic but wrapped it in a helper method `_next_date()` and used `timedelta(days=7)` instead of `timedelta(weeks=1)`. The extra helper added indirection without benefit for a single-use calculation.

**Winner: Claude.** The `timedelta(weeks=1)` form is more readable and communicates intent directly. The `None`-guard suggestion was also more Pythonic than GPT-4o's approach of raising a `ValueError`. For utility methods like this, the simpler, more self-documenting solution is the better one.

---

## 5. Reflection

**a. What went well**

The clean separation between `pawpal_system.py` (pure logic, no UI) and `app.py` (pure UI, no business logic) made both easier to build and test independently. The Scheduler's `mark_task_complete` method delegating recurrence back through the owner's pet list was a satisfying design — the UI only has to call one method and the whole chain (complete → reschedule → attach to pet) happens automatically.

**b. What you would improve**

The current session state is in-memory only — all pets and tasks reset on page reload. A next iteration would add JSON persistence so data survives between sessions. The conflict detector would also be upgraded to check overlapping durations, not just identical start times.

**c. Key takeaway**

AI tools are most useful when you already have a clear design — they accelerate implementation but rarely improve architecture on their own. Acting as the "lead architect" meant setting the class boundaries first, then letting AI fill in the method bodies. Accepting every AI suggestion without that prior structure would have produced working but poorly organised code that's hard to test or extend.
