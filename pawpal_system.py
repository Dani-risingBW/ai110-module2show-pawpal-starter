from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date, time
from enum import Enum
from typing import List, Optional, Dict, Any, Callable


class Priority(str, Enum):
	HIGH = "high"
	MEDIUM = "medium"
	LOW = "low"

	@classmethod
	def from_str(cls, value: Optional[str]) -> "Priority":
		"""Parse a string or Priority into a Priority enum (case-insensitive)."""
		if isinstance(value, cls):
			return value
		if value is None:
			return cls.MEDIUM
		try:
			return cls(str(value).lower())
		except ValueError:
			return cls.MEDIUM


@dataclass
class Owner:
	id: Optional[int]
	name: str
	preferences: Dict[str, Any] = field(default_factory=dict)
	pets: List["Pet"] = field(default_factory=list)
	tasks: List["Task"] = field(default_factory=list)

	def add_pet(self, pet: "Pet") -> None:
		"""Associate a Pet with this Owner."""
		pet.owner_id = self.id
		if pet not in self.pets:
			self.pets.append(pet)

	def add_task(self, task: "Task") -> None:
		"""Add an owner-level task (not attached to a pet)."""
		task.owner_id = self.id
		self.tasks.append(task)

	def get_availability(self) -> Optional[Dict[str, Any]]:
		"""Return the owner's availability settings dict, if any."""
		return self.preferences.get("availability")


@dataclass
class Pet:
	id: Optional[int]
	name: str
	species: Optional[str] = None
	owner_id: Optional[int] = None
	tasks: List["Task"] = field(default_factory=list)

	def describe(self) -> str:
		"""Return a short description of the pet."""
		return f"{self.name} ({self.species})" if self.species else self.name

	def add_task(self, task: "Task") -> None:
		"""Attach a task to this pet."""
		task.pet_id = self.id
		if task not in self.tasks:
			self.tasks.append(task)


@dataclass
class Task:
	id: Optional[int]
	title: str
	duration_minutes: int
	priority: Priority = Priority.MEDIUM
	owner_id: Optional[int] = None
	pet_id: Optional[int] = None
	notes: Optional[str] = None
	description: Optional[str] = None
	scheduled_time: Optional[datetime] = None
	recurrence: Optional[str] = None  # 'daily', 'weekly', etc.
	completed: bool = False

	def __post_init__(self) -> None:
		"""Normalize fields after initialization."""
		# Normalize priority to Priority enum
		try:
			self.priority = Priority.from_str(self.priority)
		except Exception:
			self.priority = Priority.MEDIUM

	def estimate_end(self, start: datetime) -> datetime:
		"""Estimate end time from a start datetime."""
		return start + timedelta(minutes=int(self.duration_minutes))

	def mark_complete(self) -> None:
		"""Mark this task as completed."""
		self.completed = True

	def is_recurring(self) -> bool:
		"""Return True if this task recurs."""
		return bool(self.recurrence)

	def next_occurrence(self) -> Optional[datetime]:
		"""Return the next scheduled occurrence for recurring tasks."""
		if not self.is_recurring() or not self.scheduled_time:
			return None
		if self.recurrence == "daily":
			return self.scheduled_time + timedelta(days=1)
		if self.recurrence == "weekly":
			return self.scheduled_time + timedelta(weeks=1)
		return None


@dataclass
class ScheduledTask:
	id: Optional[int]
	task: Task
	start_time: datetime
	end_time: datetime
	reason: Optional[str] = None
	frequency: Optional[str] = None

	def to_dict(self) -> Dict[str, Any]:
		"""Serialize the scheduled task to a dict."""
		return {
			"id": self.id,
			"task_id": self.task.id,
			"title": self.task.title,
			"start_time": self.start_time.isoformat(),
			"end_time": self.end_time.isoformat(),
			"reason": self.reason,
			"frequency": self.frequency,
			"priority": self.task.priority.value if hasattr(self.task, "priority") else None,
		}

	def validate(self) -> bool:
		"""Validate that end_time is after start_time."""
		if not (self.end_time > self.start_time):
			raise ValueError("ScheduledTask.end_time must be after start_time")
		return True


class Scheduler:
	"""A simple scheduling engine.

	Responsibilities:
	- retrieve tasks for an owner
	- order tasks (by priority, optional rules)
	- assign start/end times respecting simple availability
	- serialize/persist results (placeholder)
	"""

	def __init__(self, rules: Optional[Dict[str, Callable]] = None) -> None:
		"""Initialize the scheduler with optional rules."""
		self.rules = rules or {}
		self.last_warnings: List[str] = []

	def add_rule(self, name: str, rule_fn: Callable) -> None:
		"""Register a scheduling rule."""
		self.rules[name] = rule_fn

	def retrieve_tasks(self, owner: Owner) -> List[Task]:
		"""Collect tasks from an owner and their pets."""
		tasks: List[Task] = []
		tasks.extend(owner.tasks)
		for pet in owner.pets:
			tasks.extend(getattr(pet, "tasks", []))
		return tasks

	def filter_tasks(
		self,
		tasks: List[Task],
		completed: Optional[bool] = None,
		pet_name: Optional[str] = None,
		owner: Optional[Owner] = None,
		pets: Optional[List[Pet]] = None,
	) -> List[Task]:
		"""Filter tasks by completion status and/or pet name.

		If pet_name is provided, tasks are matched using owner/pets info.
		"""
		filtered = tasks

		if completed is not None:
			filtered = [task for task in filtered if task.completed is completed]

		if pet_name:
			pet_pool = pets or (owner.pets if owner else [])
			pet_name_lower = pet_name.strip().lower()
			pet_ids = {
				pet.id for pet in pet_pool
				if pet.id is not None and pet.name.strip().lower() == pet_name_lower
			}
			filtered = [task for task in filtered if task.pet_id in pet_ids] if pet_ids else []

		return filtered

	def schedule_tasks(
		self,
		tasks: Optional[List[Task]] = None,
		owner: Optional[Owner] = None,
		pets: Optional[List[Pet]] = None,
		start_time: Optional[datetime] = None,
	) -> List[ScheduledTask]:
		"""Produce a simple ordered schedule of tasks.

		Simple algorithm:
		- If owner provided and no explicit tasks list, retrieve owner's tasks.
		- Sort tasks by priority (high->low) and longer duration first within same priority.
		- Place tasks sequentially starting at owner's availability start (or 08:00).
		- If a task has `scheduled_time`, place it at that time.
		"""

		if owner and not tasks:
			tasks = self.retrieve_tasks(owner)

		tasks = tasks or []

		# determine start_time from owner availability or default 08:00
		if start_time is None:
			today = date.today()
			default_start = datetime.combine(today, time(hour=8, minute=0))
			start_time = default_start
			if owner:
				av = owner.get_availability()
				if isinstance(av, dict):
					s = av.get("start")
					if isinstance(s, str):
						try:
							h, m = map(int, s.split(":"))
							start_time = datetime.combine(today, time(hour=h, minute=m))
						except Exception:
							pass

		tasks_sorted = self.sort_by_time(tasks)

		scheduled: List[ScheduledTask] = []
		cursor = start_time

		for task in tasks_sorted:
			if task.scheduled_time:
				st = task.scheduled_time
			else:
				st = cursor
			et = task.estimate_end(st)
			s_task = ScheduledTask(id=None, task=task, start_time=st, end_time=et)
			s_task.validate()
			scheduled.append(s_task)
			# advance cursor if placed at or after current cursor
			if st >= cursor:
				cursor = et

		self.last_warnings = self.detect_conflicts(scheduled, owner=owner)
		return scheduled

	def sort_by_time(self, tasks: List[Task]) -> List[Task]:
		"""Return tasks sorted by scheduled time, then unscheduled tasks.

		Unscheduled tasks are ordered after all timed tasks.
		"""
		def scheduled_time_key(t: Task):
			has_time = t.scheduled_time is not None
			return (not has_time, t.scheduled_time or datetime.max)

		return sorted(tasks, key=scheduled_time_key)

	def detect_conflicts(
		self,
		scheduled: List[ScheduledTask],
		owner: Optional[Owner] = None,
	) -> List[str]:
		"""Return non-blocking warning messages for scheduling conflicts.

		Checks overlaps, same-start collisions, invalid durations, and availability.
		"""
		warnings: List[str] = []
		if not scheduled:
			return warnings

		ordered = sorted(scheduled, key=lambda s: s.start_time)
		previous = ordered[0]
		for current in ordered[1:]:
			if current.start_time < previous.end_time:
				warnings.append(
					f"Overlap: '{current.task.title}' starts at {current.start_time.strftime('%H:%M')} "
					f"before '{previous.task.title}' ends at {previous.end_time.strftime('%H:%M')}."
				)
			previous = current

		by_start: Dict[datetime, List[ScheduledTask]] = {}
		for s in scheduled:
			by_start.setdefault(s.start_time, []).append(s)
		for start, group in by_start.items():
			if len(group) > 1:
				titles = ", ".join(sorted(task.task.title for task in group))
				warnings.append(
					f"Collision: multiple tasks start at {start.strftime('%H:%M')}: {titles}."
				)

		for s in scheduled:
			if s.end_time <= s.start_time:
				warnings.append(
					f"Invalid duration: '{s.task.title}' ends at {s.end_time.strftime('%H:%M')} "
					f"which is not after {s.start_time.strftime('%H:%M')}."
				)

		if owner:
			av = owner.get_availability() or {}
			date_base = ordered[0].start_time.date()
			start_bound = None
			end_bound = None
			if isinstance(av.get("start"), str):
				try:
					h, m = map(int, av["start"].split(":"))
					start_bound = datetime.combine(date_base, time(hour=h, minute=m))
				except Exception:
					start_bound = None
			if isinstance(av.get("end"), str):
				try:
					h, m = map(int, av["end"].split(":"))
					end_bound = datetime.combine(date_base, time(hour=h, minute=m))
				except Exception:
					end_bound = None

			for s in scheduled:
				if start_bound and s.start_time < start_bound:
					warnings.append(
						f"Outside availability: '{s.task.title}' starts at {s.start_time.strftime('%H:%M')} "
						f"before availability starts at {start_bound.strftime('%H:%M')}."
					)
				if end_bound and s.end_time > end_bound:
					warnings.append(
						f"Outside availability: '{s.task.title}' ends at {s.end_time.strftime('%H:%M')} "
						f"after availability ends at {end_bound.strftime('%H:%M')}."
					)

		return warnings

	def complete_task(
		self,
		task: Task,
		owner: Optional[Owner] = None,
		pets: Optional[List[Pet]] = None,
	) -> Optional[Task]:
		"""Mark a task complete and create the next recurring instance if needed.

		Returns the newly created task for daily/weekly recurrences.
		"""
		task.mark_complete()
		if not task.is_recurring():
			return None

		next_time = task.next_occurrence()
		if not next_time:
			return None

		new_task = Task(
			id=None,
			title=task.title,
			duration_minutes=task.duration_minutes,
			priority=task.priority,
			owner_id=task.owner_id,
			pet_id=task.pet_id,
			notes=task.notes,
			description=task.description,
			scheduled_time=next_time,
			recurrence=task.recurrence,
			completed=False,
		)

		pet_pool = pets or (owner.pets if owner else [])
		if task.pet_id is not None:
			for pet in pet_pool:
				if pet.id == task.pet_id:
					pet.add_task(new_task)
					return new_task
			return new_task

		if owner:
			owner.add_task(new_task)

		return new_task

	def explain_schedule(self, scheduled: List[ScheduledTask]) -> List[str]:
		"""Return human-readable schedule explanations."""
		explanations = []
		for s in scheduled:
			explanations.append(
				f"{s.task.title}: {s.start_time.strftime('%Y-%m-%d %H:%M')} - {s.end_time.strftime('%H:%M')} (priority={s.task.priority.value})"
			)
		return explanations

	def persist_schedule(self, scheduled: List[ScheduledTask]) -> List[Dict[str, Any]]:
		"""Assign IDs and return serializable rows."""
		rows: List[Dict[str, Any]] = []
		next_id = 1
		for s in scheduled:
			if s.id is None:
				s.id = next_id
				next_id += 1
			rows.append(s.to_dict())
		return rows

	def reschedule_for_changes(self, owner: Owner) -> List[ScheduledTask]:
		"""Re-run scheduling after owner task changes."""
		tasks = self.retrieve_tasks(owner)
		return self.schedule_tasks(tasks=tasks, owner=owner)


__all__ = ["Owner", "Pet", "Task", "ScheduledTask", "Scheduler", "Priority"]

