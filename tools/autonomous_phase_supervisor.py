#!/usr/bin/env python3
"""Run the governed autonomous loop with a DASS-derived operating objective."""
from __future__ import annotations

import json
from pathlib import Path

from tools import autonomy_liveness_supervisor as supervisor
from tools.factory_forensics.dass_phase import measure, select_phase

ROOT = Path(__file__).resolve().parents[1]

PRE_DASS_OBJECTIVE = (
    "Maximize verified progress toward DASS achievement: discover the highest-value "
    "remaining production-surface gaps, repair or construct the missing capabilities, "
    "validate them, preserve fail-closed measurement and authority boundaries, and "
    "continue until DASS is achieved. Prepare post-DASS capabilities without activating "
    "them prematurely. Preserve all safety, audit, cost, risk, and verification boundaries."
)

POST_DASS_OBJECTIVE = (
    "Maximize useful post-DASS operation indefinitely: discover the highest-value "
    "capability, reliability, resilience, autonomy, and economic-usefulness opportunities, "
    "rank them by expected value, confidence, reversibility, cost, and risk, execute only "
    "through the governed authority path, verify outcomes, learn from results, recover "
    "from failures, and repeat continuously. Periodically re-check DASS integrity and "
    "never weaken safety, audit, cost, risk, authority, or verification boundaries."
)


def persist_phase(phase: str, report: dict, previous: dict | None = None) -> dict:
    previous = previous or {}
    state = {
        "phase": phase,
        "previous_phase": previous.get("phase"),
        "transition": previous.get("phase") != phase,
        "dass_achieved": phase == "post_dass",
        "measurement": report,
    }
    path = ROOT / "state" / "dass_phase.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return state


def main() -> int:
    report = measure()
    phase = select_phase(report)
    phase_path = ROOT / "state" / "dass_phase.json"
    previous = json.loads(phase_path.read_text(encoding="utf-8")) if phase_path.exists() else {}
    phase_state = persist_phase(phase, report, previous)

    supervisor.MISSION_OBJECTIVE = (
        POST_DASS_OBJECTIVE if phase == "post_dass" else PRE_DASS_OBJECTIVE
    )
    state = supervisor.run_once(ROOT)
    state["dass_phase"] = phase_state
    supervisor.persist(ROOT, state)
    return 0 if state.get("execution_succeeded") is True or state.get("converged") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
