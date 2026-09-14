# CommHub canonical exactly-once boundary

`ai/coordination/messages.jsonl` is the canonical AI-to-AI coordination bus.

For one logical `CommHub.send()` call, a `messages_jsonl` channel must produce exactly one canonical bus entry identified by the generated `msg_id`.

`CommHub(repo_root=...)` must keep all filesystem state under the supplied checkout root, including party registry and communication logs.

This contract is observational/transport-only: it does not grant protected execution authority and does not introduce a second coordination transport.
