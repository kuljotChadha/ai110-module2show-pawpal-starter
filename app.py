import os
from datetime import date

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Your daily pet care planner")

DATA_FILE = "data.json"
PRIORITY_ICON = {"high": "🔴", "medium": "🟡", "low": "🟢"}

# ---------------------------------------------------------------------------
# Session state — persist Owner across reruns, load from JSON if available
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    if os.path.exists(DATA_FILE):
        try:
            st.session_state.owner = Owner.load_from_json(DATA_FILE)
        except Exception:
            st.session_state.owner = None
    else:
        st.session_state.owner = None

# ---------------------------------------------------------------------------
# Sidebar — Owner & Pet setup
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Setup")

    owner_name = st.text_input(
        "Your name",
        value=st.session_state.owner.name if st.session_state.owner else "Jordan",
    )
    available_mins = st.number_input(
        "Daily time budget (minutes)",
        min_value=10,
        max_value=480,
        value=st.session_state.owner.available_minutes_per_day if st.session_state.owner else 120,
        step=10,
    )

    if st.button("Save owner"):
        st.session_state.owner = Owner(
            name=owner_name, available_minutes_per_day=int(available_mins)
        )
        st.success(f"Owner '{owner_name}' saved!")

    if st.session_state.owner:
        st.divider()
        st.subheader("Add a pet")
        pet_name = st.text_input("Pet name", key="pet_name")
        species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"], key="pet_species")
        if st.button("Add pet"):
            if pet_name.strip():
                st.session_state.owner.add_pet(Pet(name=pet_name.strip(), species=species))
                st.session_state.owner.save_to_json(DATA_FILE)
                st.success(f"Added {pet_name}!")
            else:
                st.warning("Please enter a pet name.")

        st.divider()
        if st.button("💾 Save all data"):
            st.session_state.owner.save_to_json(DATA_FILE)
            st.success("Saved to data.json!")

        if os.path.exists(DATA_FILE) and st.button("🗑 Clear saved data"):
            os.remove(DATA_FILE)
            st.session_state.owner = None
            st.rerun()

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
if not st.session_state.owner:
    st.info("Enter your name and daily time budget in the sidebar, then click **Save owner** to get started.")
    st.stop()

owner: Owner = st.session_state.owner

if not owner.pets:
    st.info("Add at least one pet in the sidebar to continue.")
    st.stop()

# ---------------------------------------------------------------------------
# Add tasks
# ---------------------------------------------------------------------------
st.subheader("Add a task")

col1, col2 = st.columns(2)
with col1:
    pet_options = [p.name for p in owner.pets]
    selected_pet_name = st.selectbox("For pet", pet_options, key="task_pet")
with col2:
    task_title = st.text_input("Task title", value="Morning walk", key="task_title")

col3, col4, col5 = st.columns(3)
with col3:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20, key="task_dur")
with col4:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2, key="task_priority")
with col5:
    scheduler_tmp = Scheduler(owner)
    suggested_slot = scheduler_tmp.find_next_available_slot(int(duration))
    scheduled_time = st.text_input("Time (HH:MM)", value=suggested_slot, key="task_time")
    st.caption(f"Suggested next free slot: {suggested_slot}")

frequency = st.selectbox("Frequency", ["one-time", "daily", "weekly"], key="task_freq")

if st.button("Add task"):
    pet = next((p for p in owner.pets if p.name == selected_pet_name), None)
    if pet and task_title.strip():
        pet.add_task(Task(
            title=task_title.strip(),
            duration_minutes=int(duration),
            priority=priority,
            scheduled_time=scheduled_time,
            frequency=frequency,
            due_date=date.today(),
        ))
        owner.save_to_json(DATA_FILE)
        st.success(f"Task '{task_title}' added to {selected_pet_name}!")
    else:
        st.warning("Please enter a task title.")

# ---------------------------------------------------------------------------
# Current tasks per pet
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Tasks by pet")

for pet in owner.pets:
    with st.expander(f"{pet.name} ({pet.species}) — {len(pet.tasks)} task(s)", expanded=True):
        if not pet.tasks:
            st.caption("No tasks yet.")
        else:
            for task in pet.tasks:
                status_icon = "✅" if task.is_complete else "⬜"
                priority_icon = PRIORITY_ICON.get(task.priority, "")
                st.markdown(
                    f"{status_icon} {priority_icon} **{task.title}** | "
                    f"{task.scheduled_time} | {task.duration_minutes} min | "
                    f"{task.priority} | {task.frequency}"
                )

# ---------------------------------------------------------------------------
# Generate schedule
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Generate today's schedule")

schedule_mode = st.radio(
    "Schedule mode",
    ["By time (chronological)", "By priority then time"],
    horizontal=True,
)

if st.button("Build schedule"):
    scheduler = Scheduler(owner)

    if schedule_mode == "By priority then time":
        schedule = scheduler.build_priority_schedule()
    else:
        schedule = scheduler.build_schedule()

    conflicts = scheduler.detect_conflicts(schedule)
    if conflicts:
        for c in conflicts:
            st.warning(f"⚠️ {c}")

    if not schedule:
        st.info("No pending tasks fit within your time budget.")
    else:
        total_mins = sum(t.duration_minutes for t in schedule)
        st.success(
            f"Scheduled {len(schedule)} task(s) — "
            f"{total_mins} / {owner.available_minutes_per_day} min used"
        )

        rows = []
        for task in schedule:
            pet_name = next((p.name for p in owner.pets if task in p.tasks), "?")
            rows.append({
                "Time": task.scheduled_time,
                "Task": task.title,
                "Pet": pet_name,
                "Priority": f"{PRIORITY_ICON.get(task.priority, '')} {task.priority}",
                "Duration (min)": task.duration_minutes,
                "Recurring": task.frequency,
            })
        st.table(rows)

        if conflicts:
            st.error(
                "Action needed: two or more tasks share the same start time. "
                "Adjust their scheduled times to resolve conflicts."
            )

# ---------------------------------------------------------------------------
# Mark task complete
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Mark a task complete")

all_pending = [
    (p.name, t) for p in owner.pets for t in p.tasks if not t.is_complete
]

if not all_pending:
    st.caption("No pending tasks.")
else:
    task_labels = [
        f"{PRIORITY_ICON.get(t.priority, '')} {pname} — {t.title} @ {t.scheduled_time}"
        for pname, t in all_pending
    ]
    selected_label = st.selectbox("Select task", task_labels, key="complete_task")
    if st.button("Mark complete"):
        idx = task_labels.index(selected_label)
        _, selected_task = all_pending[idx]
        scheduler = Scheduler(owner)
        next_task = scheduler.mark_task_complete(selected_task)
        owner.save_to_json(DATA_FILE)
        st.success(f"'{selected_task.title}' marked complete!")
        if next_task:
            st.info(f"Next occurrence scheduled: {next_task.title} on {next_task.due_date}")
