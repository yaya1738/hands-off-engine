# Control Room request observability

The Control Room should expose admitted request state as a read-only projection alongside the canonical coordination bus and durable task lifecycle projection.

Source files remain authoritative: `ai/coordination/messages.jsonl` is the transport/source of truth, while request intake and task lifecycle files are durable projections. The Control Room must not create a second transport, mutate admission/execution state, or dispatch work.

The intended bounded snapshot contains:
- canonical bus events;
- admitted/rejected request counts and recent decisions;
- durable task lifecycle state.

All views must remain checkout-local when an explicit repository root is supplied.
