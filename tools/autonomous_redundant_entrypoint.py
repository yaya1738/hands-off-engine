#!/usr/bin/env python3
"""Redundant governed Factory entrypoint.

Provides multiple execution routes without creating a second authority. The
primary route is the integrated DASS supervisor; the fallback route is the
canonical liveness supervisor. Both execute through FactoryAuthorityGateway.
The selected backend is published to both the liveness state and the durable
Factory control-state channel, so downstream transports can observe the same
bounded result without depending on one publication path.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from tools import autonomy_liveness_supervisor as liveness
from tools import autonomous_integrated_supervisor as integrated
from tools import factory_control_channel as control

ROOT = Path(__file__).resolve().parents[1]


def _record_backend(state: dict, backend: str, primary_error: str | None = None) -> dict:
    state = dict(state)
    state["execution_backend"] = backend
    state["redundancy"] = {
        "enabled": True,
        "primary": "autonomous_integrated_supervisor",
        "fallback": "autonomy_liveness_supervisor",
        "selected": backend,
        "primary_error": primary_error,
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }
    liveness.persist(ROOT, state)
    control.publish_state(
        ROOT,
        node_id=state.get("node_id"),
        status=state.get("status"),
        operating_state=state.get("operating_state"),
        objective=state.get("objective"),
        last_action=state.get("last_action"),
        last_result=state.get("last_result"),
        pending_commands=state.get("pending_commands", 0),
        problem=state.get("problem"),
        next_action=state.get("next_action"),
    )
    return state


def run() -> tuple[dict, int]:
    primary_error = None
    try:
        code = integrated.main()
        state_path = ROOT / liveness.STATE_PATH
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
        if code == 0 and state.get("live_system_active") is True:
            return _record_backend(state, "integrated"), 0
        primary_error = f"integrated supervisor returned {code}"
    except Exception as exc:
        primary_error = f"integrated supervisor exception: {exc}"

    try:
        fallback = liveness.run_once(ROOT)
        fallback["primary_route_failed"] = primary_error
        fallback = _record_backend(fallback, "liveness_fallback", primary_error)
        return fallback, 0 if fallback.get("live_system_active") is True else 1
    except Exception as exc:
        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "degraded",
            "live_system_active": False,
            "operating_state": "offline",
            "execution_backend": "none",
            "redundancy": {
                "enabled": True,
                "primary": "autonomous_integrated_supervisor",
                "fallback": "autonomy_liveness_supervisor",
                "selected": "none",
                "primary_error": primary_error,
                "fallback_error": str(exc),
            },
        }
        liveness.persist(ROOT, state)
        control.publish_state(
            ROOT,
            status="degraded",
            operating_state="offline",
            problem="all governed execution backends failed",
            next_action="retry governed recovery",
        )
        print(json.dumps(state, sort_keys=True), flush=True)
        return state, 1


def main() -> int:
    state, code = run()
    print(json.dumps(state, sort_keys=True), flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
