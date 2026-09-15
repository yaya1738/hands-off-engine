# FactoryIntake continuation fan-out boundary

Generic `task_completed` continuation events are observational by default. FactoryIntake only emits a follow-up `task_assignment` for a completion when the event explicitly carries a non-empty `next_action` in `context.next_action` or top-level `next_action`.

Other wake-worthy boundary events retain their existing governed follow-up behavior.
