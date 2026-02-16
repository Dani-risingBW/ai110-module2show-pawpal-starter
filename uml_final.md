## PawPal+ Final Class Diagram

```mermaid
classDiagram
    %% Enum
    class Priority {
      <<enumeration>>
      HIGH
      MEDIUM
      LOW
      +from_str(value: Optional~string~) Priority
    }

    %% Classes
    class Owner {
      +id: Optional~int~
      +name: string
      +preferences: dict
      +pets: List~Pet~
      +tasks: List~Task~
      +add_pet(pet: Pet) void
      +add_task(task: Task) void
      +get_availability() Optional~dict~
    }

    class Pet {
      +id: Optional~int~
      +name: string
      +species: Optional~string~
      +owner_id: Optional~int~
      +tasks: List~Task~
      +describe() string
      +add_task(task: Task) void
    }

    class Task {
      +id: Optional~int~
      +title: string
      +duration_minutes: int
      +priority: Priority
      +owner_id: Optional~int~
      +pet_id: Optional~int~
      +notes: Optional~string~
      +description: Optional~string~
      +scheduled_time: Optional~datetime~
      +recurrence: Optional~string~
      +completed: bool
      +estimate_end(start: datetime) datetime
      +mark_complete() void
      +is_recurring() bool
      +next_occurrence() Optional~datetime~
    }

    class ScheduledTask {
      +id: Optional~int~
      +task: Task
      +start_time: datetime
      +end_time: datetime
      +reason: Optional~string~
      +frequency: Optional~string~
      +to_dict() dict
      +validate() bool
    }

    class Scheduler {
      +rules: dict
      +last_warnings: List~string~
      +add_rule(name: string, rule_fn: Callable) void
      +retrieve_tasks(owner: Owner) List~Task~
      +filter_tasks(tasks: List~Task~, completed: Optional~bool~, pet_name: Optional~string~, owner: Optional~Owner~, pets: Optional~List~Pet~) List~Task~
      +schedule_tasks(tasks: Optional~List~Task~, owner: Optional~Owner~, pets: Optional~List~Pet~, start_time: Optional~datetime~) List~ScheduledTask~
      +sort_by_time(tasks: List~Task~) List~Task~
      +detect_conflicts(scheduled: List~ScheduledTask~, owner: Optional~Owner~) List~string~
      +complete_task(task: Task, owner: Optional~Owner~, pets: Optional~List~Pet~) Optional~Task~
      +explain_schedule(scheduled: List~ScheduledTask~) List~string~
      +persist_schedule(scheduled: List~ScheduledTask~) List~dict~
      +reschedule_for_changes(owner: Owner) List~ScheduledTask~
    }

    %% Relationships
    Owner "1" o-- "0..*" Pet : owns
    Owner "1" o-- "0..*" Task : owns
    Pet "1" o-- "0..*" Task : tasks
    Task --> Priority : uses
    ScheduledTask "1" --> "1" Task : wraps
    Scheduler ..> Owner : reads
    Scheduler ..> Pet : reads
    Scheduler ..> Task : processes
    Scheduler ..> ScheduledTask : produces