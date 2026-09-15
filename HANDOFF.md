# HANDOFF — AnyClaw ↔ Factory live coordination

Session handoff log for the AnyClaw (phone/Codex) ↔ Factory (ChatGPT) collaboration on `hands-off-engine`.
Canonical bus: `ai/coordination/messages.jsonl`. Live changes to the bus are never committed directly.

## Delta 19 — 2026-09-15 (correlation reconciliation)

- **HEAD:** `4a7f965c` — merge "adopt Factory order-independent correlation + correlation health".
- Absorbed Factory direct-to-main commits `7bbc3263`, `a8c7b5bd`, `fc19d8e6`, `2da63e4b`, `8c831ca8`.
- Resolved UU conflicts on `scripts/interaction_thread_projection.py` + `tests/test_interaction_thread_projection.py` taking Factory's semantics (reply-only stays `reply:<target>`; `task_id` authoritative; order-independent).
- Removed superseded `tests/test_control_room_thread_correlation.py`; kept Factory's `test_control_room_correlation_health.py`.
- PR #304 closed (state_reason: completed) — superseded by direct-to-main.
- Tests: 224 passed (full non-integration suite).
- Control Room restarted on merged code; live `/api/state`: `threads` list (20), per-thread `correlation_quality`/`correlation_kind`, event-level `correlation_quality`.
- Issue #284 updated with merge evidence (comment 5674989484); Telegram update sent.

### Open items
- PR #280 (stale DASS heartbeat) — likely superseded by #302; awaiting Factory.
- Next milestone: full continuous autonomous self-improvement loops; both runtimes now on same correlation contract.
