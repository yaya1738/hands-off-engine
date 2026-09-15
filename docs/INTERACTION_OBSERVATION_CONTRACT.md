# Interaction Observation Contract

The interaction bridge is complete only when a request and its response can be followed through the same observable system.

## Required projection

For each bounded interaction record, expose read-only correlation fields:

- `msg_id`
- `task_id`, when assigned
- `reply_to`, when present
- event `type`
- event timestamp
- lifecycle `current_state`, when a task projection exists

## Invariants

- The canonical bus remains `ai/coordination/messages.jsonl`.
- Control Room observation is a projection, never a second source of truth.
- Missing correlation fields fail closed rather than being guessed.
- Observation must not mutate admission, execution, or authorization state.
- Human and agent messages use the same governed transport and correlation model.
