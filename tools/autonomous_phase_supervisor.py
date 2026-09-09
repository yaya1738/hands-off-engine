#!/usr/bin/env python3
"""Run the governed autonomous loop with a fail-closed DASS-derived objective."""
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


def _load_previous_phase(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return {}


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


def _phase_error_state(exc: Exception) -> dict:
    return {
        "timestamp": supervisor.utc_now(),
        "status": "degraded",
        "execution_succeeded": False,
        "converged": False,
        "live_system_active": False,
        "phase_selection_failed": True,
        "error": f"DASS phase measurement/selection failed: {exc}",
    }


def main() -> int:
    phase_path = ROOT / "state" / "dass_phase.json"
    try:
        report = measure()
        phase = select_phase(report)
        phase_state = persist_phase(phase, report, _load_previous_phase(phase_path))
    except Exception as exc:
        state = _phase_error_state(exc)
        supervisor.persist(ROOT, state)
        print(json.dumps(state, sort_keys=True))
        return 1

    supervisor.MISSION_OBJECTIVE = (
        POST_DASS_OBJECTIVE if phase == "post_dass" else PRE_DASS_OBJECTIVE
    )
    # Pass the authoritative phase into selection. This keeps the phase
    # decision derived from measurement rather than inferred from the mission
    # text, while preserving the existing governed execution path.
    supervisor.MISSION_PHASE = phase
    state = supervisor.run_once(ROOT)
    state["dass_phase"] = phase_state
    supervisor.persist(ROOT, state)
    return 0 if state.get("execution_succeeded") is True or state.get("converged") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
