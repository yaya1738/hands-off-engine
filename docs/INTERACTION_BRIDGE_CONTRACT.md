# Interaction Bridge Contract

`scripts/interaction_bridge.py` is the narrow adapter for bidirectional interaction.

It deliberately delegates inbound operator messages to `CommHub.receive()` and
identifies the canonical bus as `ai/coordination/messages.jsonl`. It does not
perform dispatch, protected execution, credential access, or create a parallel
message/state store.

`correlate_event()` exposes the existing `msg_id`, `task_id`, and `reply_to`
fields so a human or agent can follow a conversation across assignment,
execution, result publication, and observation.

The adapter is checkout-local: callers provide the repository root explicitly.
