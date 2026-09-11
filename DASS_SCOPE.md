# DASS scope and 100% measurement

DASS is the production autonomous system, not the historical repository as a whole.

## What counts

The DASS runtime surface is the governed loop that can observe state, make autonomous decisions, obtain authority, act, verify outcomes, recover, and remain live. Its active code is explicitly bounded by `tools/factory_forensics/dass_scope.json`.

**DASS is intentionally deployable and operable using the repository/GitHub execution assets alone.** A separate physical/cloud host is not a prerequisite for DASS achievement. The GitHub-hosted autonomous production-service workflow is a valid DASS runtime and is the primary live-system benchmark for this mission. External infrastructure (for example DigitalOcean) is an optional deployment target, not part of the DASS achievement gate.

## What was found outside DASS

The repository contains historical income-generation material, including `AUTONOMOUS_INCOME.md`, `ai/INCOME_RESEARCH_2025-11-30.md`, `deliverables/INCOME_ACTION_PLAN.md`, `autonomous/income_worker.py`, `autonomous/income_accelerator.py`, `autonomous/zero_capital_income.py`, and `integrafix/income_engine.py`. Search results also show older income-pipeline and backup state material. These are not DASS runtime capabilities.

They are therefore quarantined from the DASS denominator. Retaining them does not make them part of DASS; importing them into the active runtime would fail the DASS purity measurement.

## 100% rule

`tools/factory_forensics/dass_measurement.py` is fail-closed. The target is exactly 100% mapped active DASS surface, zero operational-looking unclassified paths, and zero imports from quarantined non-DASS material. Newly introduced operational surface must be explicitly classified rather than silently excluded from the measurement.

## Live-system benchmark

DASS achievement and DASS liveness are related but distinct checks:

1. **DASS achievement:** the authoritative measurement reaches 100% with a pure, fully classified active surface.
2. **DASS liveness:** the governed GitHub-hosted autonomous production-service cycle actually executes the integrated supervisor, verifies its liveness/authority contract, and remains eligible for its scheduled continuation.
3. **External deployment:** optional activation on a separate physical/cloud host is a downstream deployment target and must not be retroactively made a prerequisite for DASS.

Therefore, a missing DigitalOcean host cannot turn an otherwise achieved and live GitHub DASS system back into PRE-DASS. It is an external deployment blocker only.
