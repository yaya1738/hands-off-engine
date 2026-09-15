# Interaction thread correlation invariants

The Control Room thread projection is observational only.

- `task_id` is authoritative when explicitly present on an event.
- `reply_to` may link only to an observed `msg_id`.
- A reply inherits the referenced message's explicit task thread when that task is known.
- Explicit correlation is order-independent within the bounded bus window.
- A missing `reply_to` target remains visible as `orphan_reply`.
- Adjacent events without explicit identifiers remain separate.
- Message text and event proximity are never used to infer relationships.
- The projection never writes, routes, authorizes, executes, or mutates lifecycle state.
