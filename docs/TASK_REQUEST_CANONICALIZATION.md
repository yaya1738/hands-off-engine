# Task Request Canonicalization

`task_request.py` is an AnyClaw → Factory ingress adapter, not a second coordination system.

The canonical transport and source of truth are `ai/coordination/messages.jsonl` via `CommHub.receive()`.

Request identity is carried by `msg_id`; correlation may use `context.task_id` / `reply_to` when assigned. Local request state may be retained only as a bounded derived/cache view and must never be required to reconstruct or route a request.

The adapter must derive all filesystem paths from its supplied checkout root and must not use module-global checkout paths.

This boundary preserves bidirectional interaction while keeping admission, lifecycle, observation, and response on the same governed spine:

`interaction → CommHub → canonical bus → admission → lifecycle → Control Room projection`.

No second transport, execution authority, credential store, or coordination source of truth is introduced.
