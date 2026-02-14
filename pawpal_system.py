from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any


class Priority(str, Enum):
	HIGH = "high"
	MEDIUM = "medium"
	LOW = "low"


@dataclass
class Owner:
	id: Optional[int]
	name: str
	preferences: Dict[str, Any] = field(default_factory=dict)

	def add_pet(self, pet: "Pet") -> None:
		"""Associate a Pet with this Owner (skeleton)."""
		pass

	def get_availability(self) -> Optional[Dict[str, Any]]:
		"""Return owner's availability windows (skeleton)."""
		pass


@dataclass
class Pet:
	id: Optional[int]
	name: str
	species: Optional[str] = None
	owner_id: Optional[int] = None

	def describe(self) -> str:
		"""Return a short description of the pet (skeleton)."""
		return f"{self.name} ({self.species})" if self.species else f"{self.name}"


@dataclass
class Task:
	id: Optional[int]
	title: str
	duration_minutes: int
	priority: Priority = Priority.MEDIUM
	owner_id: Optional[int] = None
	pet_id: Optional[int] = None
	notes: Optional[str] = None

	def estimate_end(self, start: datetime) -> datetime:
		"""Estimate end time from a start datetime."""
		return start + timedelta(minutes=self.duration_minutes)


@dataclass
class ScheduledTask:
	id: Optional[int]
	task: Task
	start_time: datetime
	end_time: datetime
	reason: Optional[str] = None

	def to_dict(self) -> Dict[str, Any]:
		"""Serialize scheduled task to a dict (skeleton)."""
		return {
			"id": self.id,
			"task": self.task.title if self.task else None,
			"start_time": self.start_time.isoformat() if self.start_time else None,
			"end_time": self.end_time.isoformat() if self.end_time else None,
			"reason": self.reason,
		}


class Scheduler:
	"""Scheduling engine skeleton.

	Implement `schedule_tasks` and related helper rules here.
	"""

	def __init__(self, rules: Optional[Dict[str, Any]] = None) -> None:
		self.rules = rules or {}

	def add_rule(self, name: str, rule_fn) -> None:
		"""Register a scheduling rule (skeleton)."""
		pass

	def schedule_tasks(
		self,
		tasks: List[Task],
		owner: Optional[Owner] = None,
		pets: Optional[List[Pet]] = None,
		start_time: Optional[datetime] = None,
	) -> List[ScheduledTask]:
		"""Produce an ordered list of ScheduledTask objects (skeleton)."""
		return []

	def explain_schedule(self, scheduled: List[ScheduledTask]) -> List[str]:
		"""Return human-readable explanations for scheduled items (skeleton)."""
		return []


__all__ = ["Owner", "Pet", "Task", "ScheduledTask", "Scheduler", "Priority"]

