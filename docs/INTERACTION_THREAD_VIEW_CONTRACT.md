# Interaction Thread View Contract

The Control Room may present a bounded conversation/thread view derived from the canonical coordination bus and existing lifecycle projection.

## Correlation

For each displayed thread, preserve only observed relationships:

- `msg_id` — canonical event identity
- `task_id` — task correlation when explicitly present
- `reply_to` — explicit reply relationship when present
- lifecycle state — from the existing lifecycle projection when available
- event type and timestamp

## Rules

- `ai/coordination/messages.jsonl` remains the sole coordination transport/source of truth.
- `state/task_lifecycle.json` remains a derived lifecycle projection.
- The thread view is read-only and bounded.
- Missing identifiers are displayed as unknown; relationships are never inferred from proximity or message text.
- The view must not create, mutate, route, authorize, or execute work.
- Human, Factory, and AnyClaw interactions use the same correlation model.

## Goal

A human or agent should be able to inspect one interaction and follow its observed path from request through task execution, result publication, and subsequent observation without needing a second transport or state store.
