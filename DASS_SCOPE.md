# DASS scope and live-state benchmark

DASS is the production autonomous system, not the historical repository as a whole.

## What counts

The DASS runtime surface is the governed loop that can observe state, make autonomous decisions, obtain authority, act, verify outcomes, recover, and remain live. Its active code is explicitly bounded by `tools/factory_forensics/dass_scope.json`.

**DASS is a desired live autonomous-system state, not merely a collection of code.** It is intentionally deployable and operable using the repository/GitHub execution assets alone. A separate physical/cloud host is not a prerequisite for DASS. The GitHub-hosted autonomous production-service workflow is the primary live-system benchmark for this mission. External infrastructure such as DigitalOcean is a downstream deployment target, not a DASS prerequisite.

## What was found outside DASS

The repository contains historical income-generation material, including `AUTONOMOUS_INCOME.md`, `ai/INCOME_RESEARCH_2025-11-30.md`, `deliverables/INCOME_ACTION_PLAN.md`, `autonomous/income_worker.py`, `autonomous/income_accelerator.py`, `autonomous/zero_capital_income.py`, and `integrafix/income_engine.py`. Search results also show older income-pipeline and backup state material. These are not DASS runtime capabilities.

They are therefore quarantined from the DASS denominator. Retaining them does not make them part of DASS; importing them into the active runtime would fail the DASS purity measurement.

## 100% rule

`tools/factory_forensics/dass_measurement.py` is fail-closed. The target is exactly 100% mapped active DASS surface, zero operational-looking unclassified paths, zero active-unmapped files, and zero imports from quarantined non-DASS material. Newly introduced operational surface must be explicitly classified rather than silently excluded from the measurement.

## DASS live state

DASS is achieved only when **both** conditions are true:

1. **Runtime integrity:** the authoritative measurement reaches 100% with a pure, fully classified active surface.
2. **Runtime liveness:** the governed autonomous production-service runtime has actually executed a live cycle recently and has an unexpired liveness attestation proving that the system is operating in its desired live state.

A saved source tree, a static measurement, a historical success, or a `converged` flag by itself is **not** DASS live state. `converged` means the currently operating autonomous system has no actionable improvement objective at that moment; it means healthy steady-state operation, not dormancy.

The live state is represented explicitly as `live_system_active=true`, `operating_state=live_steady_state` or `live_executing`, and an unexpired `live_attestation`. If the runtime stops executing and the attestation expires, the system must no longer represent itself as DASS live until execution resumes.

## External deployment

External physical/cloud deployment is independent of DASS achievement. A missing DigitalOcean host can block external deployment, but it cannot turn a live GitHub DASS system back into PRE-DASS. Conversely, merely having a physical host does not establish DASS; the governed autonomous runtime must actually be operating there or through the GitHub-hosted runtime benchmark.
