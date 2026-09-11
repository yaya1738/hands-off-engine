#!/usr/bin/env python3
"""Authoritative DASS cycle with Factory learning/improvement integrated."""
from __future__ import annotations

import json
from pathlib import Path

from tools import autonomy_liveness_supervisor as liveness
from tools.factory_forensics.dass_phase import measure, select_phase
from ai.factory.authority_gateway import FactoryAuthorityGateway

ROOT = Path(__file__).resolve().parents[1]

PRE_DASS_OBJECTIVE = (
    "Maximize verified progress toward DASS achievement: discover the highest-value "
    "remaining production-surface gaps, repair or construct missing capabilities, "
    "validate them, preserve fail-closed authority, and continue until DASS is achieved."
)
POST_DASS_OBJECTIVE = (
    "Maximize useful post-DASS operation indefinitely: discover the highest-value "
    "capability, reliability, resilience, autonomy, and economic-usefulness opportunities, "
    "rank them by expected value, execute through governed authority, verify outcomes, "
    "learn from results, recover from failures, and repeat continuously."
)


def _persist_phase(report: dict, phase: str) -> dict:
    path = ROOT / "state" / "dass_phase.json"
    previous = {}
    if path.exists():
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            previous = {}
    state = {
        "phase": phase,
        "previous_phase": previous.get("phase"),
        "transition": previous.get("phase") != phase,
        "dass_achieved": phase == "post_dass",
        "measurement": report,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return state


_ORIGINAL_EXECUTE = FactoryAuthorityGateway.execute_autonomous


def _execute_and_learn(self, objective, idempotency_key=None):
    """Execute through the gateway, then immediately feed the observed result into learning."""
    result = _ORIGINAL_EXECUTE(self, objective, idempotency_key=idempotency_key)
    runtime_result = result.get("execution") if isinstance(result, dict) else None
    learning = None
    if isinstance(runtime_result, dict):
        try:
            learning = self.runtime.run_improvement_cycle(runtime_result)
        except Exception as exc:
            learning = {"status": "improvement_cycle_failed", "error": str(exc)}
    if isinstance(result, dict):
        result["continuous_improvement"] = learning
        result["productive_capacity"] = self.productive_capacity.report()
    return result


FactoryAuthorityGateway.execute_autonomous = _execute_and_learn


def main() -> int:
    try:
        report = measure()
        phase = select_phase(report)
        phase_state = _persist_phase(report, phase)
    except Exception as exc:
        state = {
            "status": "degraded",
            "execution_succeeded": False,
            "converged": False,
            "live_system_active": False,
            "phase_selection_failed": True,
            "error": f"DASS phase measurement/selection failed: {exc}",
        }
        liveness.persist(ROOT, state)
        print(json.dumps(state, sort_keys=True))
        return 1

    liveness.MISSION_OBJECTIVE = POST_DASS_OBJECTIVE if phase == "post_dass" else PRE_DASS_OBJECTIVE
    liveness.MISSION_PHASE = phase
    state = liveness.run_once(ROOT)
    state["dass_phase"] = phase_state
    # DASS is GitHub-native: a separate physical/cloud host is not part of
    # achievement or liveness. External deployment remains a downstream target.
    state["dass_live_contract"] = {
        "runtime": "github-hosted-autonomous-production-service",
        "dass_achieved": phase == "post_dass",
        "external_host_required": False,
        "external_deployment_separate": True,
        "liveness_verified": bool(
            state.get("live_system_active") is True
            and (
                state.get("converged") is True
                or state.get("execution_succeeded") is True
            )
        ),
    }
    liveness.persist(ROOT, state)
    return 0 if state.get("execution_succeeded") is True or state.get("converged") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
