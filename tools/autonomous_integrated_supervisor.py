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
        "dass_is_live_state": phase == "post_dass",
        "external_host_required": False,
        "live_runtime_observed": phase == "post_dass",
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
        initial_report = measure()
        initial_phase = select_phase(initial_report)
    except Exception as exc:
        state = {
            "status": "degraded",
            "execution_succeeded": False,
            "converged": False,
            "live_system_active": False,
            "operating_state": "offline",
            "phase_selection_failed": True,
            "error": f"DASS phase measurement/selection failed: {exc}",
        }
        liveness.persist(ROOT, state)
        print(json.dumps(state, sort_keys=True))
        return 1

    liveness.MISSION_OBJECTIVE = POST_DASS_OBJECTIVE if initial_phase == "post_dass" else PRE_DASS_OBJECTIVE
    liveness.MISSION_PHASE = initial_phase
    cycle_state = liveness.run_once(ROOT)

    # Re-measure after the actual governed cycle. This is essential: DASS is a
    # live state, so the cycle itself must establish the attestation before the
    # same run can claim DASS. A stale pre-cycle state can never do that.
    try:
        final_report = measure()
        final_phase = select_phase(final_report)
        phase_state = _persist_phase(final_report, final_phase)
    except Exception as exc:
        cycle_state["dass_phase"] = {
            "phase": "pre_dass",
            "dass_achieved": False,
            "dass_is_live_state": False,
            "external_host_required": False,
            "live_runtime_observed": False,
            "error": f"post-cycle DASS verification failed: {exc}",
        }
        cycle_state["dass_live_contract"] = {
            "runtime": "github-hosted-autonomous-production-service",
            "dass_achieved": False,
            "external_host_required": False,
            "external_deployment_separate": True,
            "liveness_verified": False,
        }
        liveness.persist(ROOT, cycle_state)
        print(json.dumps(cycle_state, sort_keys=True))
        return 1

    cycle_state["dass_phase"] = phase_state
    liveness_verified = bool(
        cycle_state.get("live_system_active") is True
        and isinstance(cycle_state.get("live_attestation"), dict)
        and cycle_state["live_attestation"].get("active") is True
        and cycle_state.get("operating_state") in {"live_executing", "live_steady_state"}
    )
    dass_live = final_phase == "post_dass" and liveness_verified
    cycle_state["dass_live_contract"] = {
        "runtime": "github-hosted-autonomous-production-service",
        "dass_achieved": dass_live,
        "external_host_required": False,
        "external_deployment_separate": True,
        "liveness_verified": liveness_verified,
        "verification_basis": "post-cycle structural measurement plus fresh runtime liveness attestation",
    }
    cycle_state["dass_phase"]["dass_achieved"] = dass_live
    cycle_state["dass_phase"]["dass_is_live_state"] = dass_live
    cycle_state["dass_phase"]["live_runtime_observed"] = liveness_verified
    liveness.persist(ROOT, cycle_state)
    print(json.dumps(cycle_state, sort_keys=True))
    return 0 if dass_live else 1


if __name__ == "__main__":
    raise SystemExit(main())
