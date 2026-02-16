import streamlit as st
from pawpal_system import Owner, Pet, Task, ScheduledTask, Scheduler, Priority
from datetime import time, date, datetime as dt
import datetime

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

st.markdown("### Owner Availability")
av_col1, av_col2 = st.columns(2)
with av_col1:
    avail_start = st.time_input("Available start", value=time(hour=8, minute=0), key="avail_start")
with av_col2:
    avail_end = st.time_input("Available end", value=time(hour=18, minute=0), key="avail_end")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(id=None, name=owner_name)
if "pet" not in st.session_state:
    st.session_state.pet = Pet(id=None, name=pet_name, species=species)
if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler()

owner = st.session_state.owner
pet = st.session_state.pet
scheduler = st.session_state.scheduler

owner.name = owner_name
pet.name = pet_name
pet.species = species
if pet not in owner.pets:
    owner.add_pet(pet)
owner.preferences["availability"] = {
    "start": avail_start.strftime("%H:%M"),
    "end": avail_end.strftime("%H:%M"),
}

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    set_task_time = st.checkbox("Set task start time", value=False)
    task_time = st.time_input(
        "Task start time",
        value=time(hour=9, minute=0),
        disabled=not set_task_time,
        key="task_start_time",
    )
    recurrence = st.selectbox("Recurrence", ["none", "daily", "weekly"], index=0)

if st.button("Add task"):
    scheduled_time = (
        dt.combine(date.today(), task_time) if set_task_time else None
    )
    recurrence_value = None if recurrence == "none" else recurrence
    task = Task(
        id=None,
        title=task_title,
        duration_minutes=int(duration),
        priority=Priority.from_str(priority),
        scheduled_time=scheduled_time,
        recurrence=recurrence_value,
    )
    pet.add_task(task)

if pet.tasks:
    sorted_tasks = scheduler.sort_by_time(pet.tasks)
    st.success("Tasks ready for scheduling.")
    st.table(
        [
            {
                "title": t.title,
                "scheduled_time": t.scheduled_time.strftime("%Y-%m-%d %H:%M") if t.scheduled_time else "-",
                "duration_minutes": t.duration_minutes,
                "priority": t.priority.value,
                "recurrence": t.recurrence or "-",
                "completed": "yes" if t.completed else "no",
            }
            for t in sorted_tasks
        ]
    )
    st.markdown("### Complete Task")
    incomplete_tasks = [t for t in sorted_tasks if not t.completed]
    if incomplete_tasks:
        labels = [f"{t.title} ({t.priority.value})" for t in incomplete_tasks]
        selected_label = st.selectbox("Select a task", labels, key="complete_task_select")
        if st.button("Complete selected task"):
            selected_index = labels.index(selected_label)
            selected_task = incomplete_tasks[selected_index]
            new_task = scheduler.complete_task(selected_task, owner=owner)
            if new_task:
                st.success(f"Completed '{selected_task.title}'. Next {new_task.recurrence} task added.")
            else:
                st.success(f"Completed '{selected_task.title}'.")
    else:
        st.info("No incomplete tasks to complete.")
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

use_availability = st.checkbox("Use owner availability for schedule start", value=True)
start_dt = None
if not use_availability:
    start_time_input = st.time_input("Schedule start time", value=time(hour=8, minute=0))
    start_dt = dt.combine(date.today(), start_time_input)

if st.button("Generate schedule"):
    scheduled = scheduler.schedule_tasks(owner=owner, start_time=start_dt)
    if scheduled:
        st.success(f"Built schedule with {len(scheduled)} tasks.")
        ordered = sorted(scheduled, key=lambda s: s.start_time)
        st.table(
            [
                {
                    "title": s.task.title,
                    "start_time": s.start_time.strftime("%Y-%m-%d %H:%M"),
                    "end_time": s.end_time.strftime("%H:%M"),
                    "priority": s.task.priority.value,
                }
                for s in ordered
            ]
        )
        if scheduler.last_warnings:
            st.warning("Scheduling conflicts detected:")
            for warning in scheduler.last_warnings:
                st.write(f"- {warning}")
        st.markdown("### Explanation")
        for line in scheduler.explain_schedule(ordered):
            st.write(f"- {line}")
    else:
        st.info("No tasks available to schedule.")
