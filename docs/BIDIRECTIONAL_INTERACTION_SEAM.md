# Governed Bidirectional Interaction Seam

The interaction layer builds on the existing Control Room projection rather than creating another channel.

## Flow

`human / agent observer → governed message → CommHub → canonical bus → RequestIntake → lifecycle → Control Room projection`

Responses travel back through the same canonical bus and lifecycle projection.

## Boundary

- `ai/coordination/messages.jsonl` remains the sole coordination transport and source of truth.
- The Control Room remains read-mostly; `/api/send` is the existing governed operator-message entry point.
- `scripts/interaction_bridge.py` is a thin adapter for programmatic interaction and correlation; it delegates to `CommHub.receive()` and adds no authority.
- Admission and execution authority remain downstream of the message boundary.
- No arbitrary shell, credentials, or direct protected execution is exposed.
- Correlation uses the existing message/task/reply identifiers so an observer can follow a request through its lifecycle.

The purpose is not to give an interface more power. It is to make interaction observable, correlated, and governed end-to-end so humans and autonomous agents can participate in the same operational loop.
