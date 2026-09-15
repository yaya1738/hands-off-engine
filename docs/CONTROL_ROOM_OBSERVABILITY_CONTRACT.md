# Control Room Observability Contract

The Control Room exposes one bounded, read-only observability projection over the Factory's existing state.

## Sources

- `ai/coordination/messages.jsonl` remains the canonical transport and source of truth.
- `state/request_intake_state.json` provides durable request admission decisions.
- `state/task_lifecycle.json` provides the durable lifecycle projection.
- `state/factory_intake_state.json` provides Factory intake decisions when present.

## Boundary

The projection is checkout-local and accepts an explicit `repo_root`. It does not create a second transport, dispatch work, authorize execution, mutate lifecycle state, or handle credentials.

## Required bounded view

A snapshot contains bounded tails/counts for:

1. canonical bus events;
2. request-intake admissions and rejections;
3. Factory intake decisions;
4. durable task lifecycle state.

This makes the same operational window inspectable by the human Control Room and by automation without introducing another state authority.
