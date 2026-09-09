# DASS scope and 100% measurement

DASS is the production autonomous system, not the historical repository as a whole.

## What counts

The DASS runtime surface is the governed loop that can observe state, make autonomous decisions, obtain authority, act, verify outcomes, recover, and remain live. Its active code is explicitly bounded by `tools/factory_forensics/dass_scope.json`.

## What was found outside DASS

The repository contains historical income-generation material, including `AUTONOMOUS_INCOME.md`, `ai/INCOME_RESEARCH_2025-11-30.md`, `deliverables/INCOME_ACTION_PLAN.md`, `autonomous/income_worker.py`, `autonomous/income_accelerator.py`, `autonomous/zero_capital_income.py`, and `integrafix/income_engine.py`. Search results also show older income-pipeline and backup state material. These are not DASS runtime capabilities.

They are therefore quarantined from the DASS denominator. Retaining them does not make them part of DASS; importing them into the active runtime would fail the DASS purity measurement.

## 100% rule

`tools/factory_forensics/dass_measurement.py` is fail-closed. The target is exactly 100% mapped active DASS surface and zero imports from quarantined non-DASS material. The measurement is intended to run continuously in CI so newly introduced operational surface cannot silently become an unmeasured part of DASS.
