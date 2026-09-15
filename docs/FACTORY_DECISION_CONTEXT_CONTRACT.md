# Factory Decision Context Contract

The Factory decision context is the bounded integration contract between mainline observation and autonomous reasoning.

## Source

The context is derived from the existing Control Room/shared observation snapshot. The canonical coordination transport remains `ai/coordination/messages.jsonl`.

## Evidence domains

- `interaction`: correlation and observation-window health.
- `admission`: explicit request admission identity and result.
- `authority`: explicit authority decision and correlation.
- `assessment`: already-derived Factory assessment.
- `system_health`: bounded environmental/system health evidence.

## Rules

1. Missing or malformed evidence fails closed.
2. Correlation uses explicit `msg_id`, `task_id`, and `reply_to`; no text or proximity inference.
3. The context is evidence, not authorization.
4. `execution_enabled` may be observed as evidence but never becomes execution authority through this contract.
5. Consumers must not create a second coordination transport or state store.
6. Health observation must not directly trigger orchestration.
7. Human, Factory, and AnyClaw consumers should be able to consume the same bounded context.

The contract therefore supports the convergence loop:

`observe → correlate → assess → decide → govern → execute (separate gate) → observe`
