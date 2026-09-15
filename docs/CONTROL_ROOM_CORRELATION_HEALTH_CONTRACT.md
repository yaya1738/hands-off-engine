# Control Room correlation health contract

The Control Room exposes bounded, read-only correlation health derived from the canonical coordination bus and interaction-thread projection.

The health view is observational only. It does not create, route, authorize, execute, or mutate lifecycle state.

## Fields

- `event_count`: events observed in the bounded bus window.
- `thread_count`: projected interaction threads in that window.
- `correlated_event_count`: events explicitly joined to a task or observed reply target.
- `orphan_reply_count`: replies whose explicit target is absent from the bounded window.
- `single_event_count`: events without an explicit task or observed reply relationship.
- `explicit_task_event_count`: events carrying an explicit `task_id`.
- `explicit_task_thread_coverage`: explicit-task events divided by observed events; `null` when the window is empty.
- `bounded_window_truncated`: true when the bus reader returned its configured maximum, meaning older relationships may lie outside the observation window.

No relationship may be inferred from message text, adjacency, or ordering.

`ai/coordination/messages.jsonl` remains the sole coordination transport/source of truth; `state/task_lifecycle.json` remains derived.

The same health contract may later be consumed by Factory improvement decisions and governed bidirectional human/AI interaction, without creating another transport or state store.
