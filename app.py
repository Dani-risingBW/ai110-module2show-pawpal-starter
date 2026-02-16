import streamlit as st
from pawpal_system import Owner, Pet, Task, ScheduledTask, Scheduler, Priority

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

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    task = Task(
        id=None,
        title=task_title,
        duration_minutes=int(duration),
        priority=Priority.from_str(priority),
    )
    pet.add_task(task)

if pet.tasks:
    st.write("Current tasks:")
    st.table(
        [
            {
                "title": t.title,
                "duration_minutes": t.duration_minutes,
                "priority": t.priority.value,
            }
            for t in pet.tasks
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    scheduled = scheduler.schedule_tasks(owner=owner)
    if scheduled:
        st.write("Schedule:")
        st.table(
            [
                {
                    "title": s.task.title,
                    "start_time": s.start_time.strftime("%Y-%m-%d %H:%M"),
                    "end_time": s.end_time.strftime("%H:%M"),
                    "priority": s.task.priority.value,
                }
                for s in scheduled
            ]
        )
        st.markdown("### Explanation")
        for line in scheduler.explain_schedule(scheduled):
            st.write(f"- {line}")
    else:
        st.info("No tasks available to schedule.")
