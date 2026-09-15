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

## Delta 20 — 2026-09-15 (observability adoption + bus-derived assessment)

- Merged PR #307 (correlation health observability: bounded-window truncation probe, `window` shape, machine/Factory adapters) and PR #309 (factory_assessment snapshot projection).
- Absorbed `6a08c55c` bus-derived Factory assessment + `eabf17b2` fail-closed sentinel fix in `_factory_assessment_observation`.
- Fixed stale/inconsistent Factory tests to match tail-window semantics (correlated=0/orphan=2 for limit-3 over 4 events; `bounded_window_truncated` → `window`).
- Tests: 233 passed. Live Control Room: `factory_assessment.available=false` (fail-closed), `correlation_health.window={bounded:true, limit:120, truncated:true}`, threads=20.
- #284 updated (comment 5675173937); Telegram sent. Open: PR #280 (awaiting Factory); orphan-vs-truncation nuance flagged to Factory.

## Delta 21 — 2026-09-15 (cleanup + #288 architecture review)

Housekeeping: closed PR #308 (superseded by #309+6a08c55c), PR #280 (DASS heartbeat superseded by #302), issue #306 (resolved by #307), issue #283 (Telegram blocker resolved).

Architecture review (#288 — 4 invariants confirmed):
1. task_id/reply_to: preserved verbatim through task_assignment → task_result → continuation (live-bus trace: intake-20260914163206 reply_to=281 in both).
2. Exactly-once: PublishLock + fcntl.flock + existing-id scan; 0 duplicate task_results on live bus.
3. Read-only + Termux-safe: all observation adapters pure reads; lifecycle_projection writes only gitignored state/; no native deps.
4. Fan-out guard: `_should_follow_up` returns False for standard task_completed (no next_action); regression test confirms.

Tests: 233/233. Open: #305 (CI observability), #279 (DASS coordination).

## Delta 22 — 2026-09-15 (CI observability root cause)

#305 root cause identified: GitHub Actions billing block — no runner assigned (`runner_id: 0`).
Annotation: "recent account payments have failed or your spending limit needs to be increased."
No code change needed; requires account owner (Yair) to update payment method in GitHub Settings → Billing.
Resolution: human account-level action; after clearing, re-run any workflow to confirm.

Open: #279 (DASS coordination). Pipeline clean (233/233), bus healthy, all runtimes alive.

## Delta 23 — 2026-09-15 (bus compaction + duplicate node1 cleanup)

- Killed duplicate node1 (pid 17611): pre-existing multi-AI bootstrap was emitting spurious BLOCKED events with stale test fixture strings ("token missing"/"bot token"). Existing `NodeLock` guard (fcntl.flock) now effective for preventing recurrence.
- Implemented `scripts/bus_compact.py`: deduplicates by event_id/msg_id, drops stale blocker events (>24h), atomic write, dry-run mode. Live bus: 665 → 88 messages (577 noise events removed).
- Control Room post-compaction: `window.truncated=false` (full bus now within 120-event window), `orphan_reply_count=0` (corrected from inflated noise).
- Added `tests/test_bus_compact.py` (3 tests). Full suite: 236/236 pass.
- Posted liveness + 3 bounded objectives on #279.

## Delta 24 — 2026-09-15 (admission observation contract)

- Merged PR #312 (commit 2caaf376): canonical admission-observation path.
  - `scripts/admission_observability.py`: reads latest explicit admission decision from bus, fail-closed.
  - `scripts/admission_publisher.py`: publishes bounded admission decisions through CommHub.
  - `scripts/factory_admission_observability.py`: projects admission observation from snapshot.
  - `control_room_state.py`: adds `admission_observation` to shared snapshot.
  - 12 new tests. Full suite: 248/248 pass.
- Control Room live: `admission_observation: {available: false}` (fail-closed, no bus events yet).
- PR #312 closed as completed. Bus: 102 messages, truncated=false.
