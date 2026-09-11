#!/usr/bin/env python3
"""Select DASS phase from both structural achievement and live runtime state."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEASURE = ROOT / "tools/factory_forensics/dass_measurement.py"
STATE = ROOT / "state" / "dass_phase.json"
LIVENESS = ROOT / "state" / "autonomy_liveness.json"


def measure() -> dict:
    proc = subprocess.run(["python", str(MEASURE)], cwd=ROOT, text=True, capture_output=True)
    if not proc.stdout.strip():
        raise SystemExit(proc.stderr.strip() or "DASS measurement produced no report")
    report = json.loads(proc.stdout)
    report["measurement_exit_code"] = proc.returncode
    return report


def _live_runtime_observed() -> bool:
    """Require a recent explicit execution attestation; source/state alone is insufficient."""
    if not LIVENESS.exists():
        return False
    try:
        state = json.loads(LIVENESS.read_text(encoding="utf-8"))
        if state.get("live_system_active") is not True:
            return False
        attestation = state.get("live_attestation", {})
        if not isinstance(attestation, dict) or attestation.get("active") is not True:
            return False
        observed = datetime.fromisoformat(str(attestation["observed_at"]).replace("Z", "+00:00"))
        expires = float(attestation["expires_at"])
        now = datetime.now(timezone.utc).timestamp()
        return observed.tzinfo is not None and now <= expires
    except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError):
        return False


def select_phase(report: dict) -> str:
    structural = (
        report.get("dass_coverage_percent") == report.get("target_percent")
        and report.get("dass_pure") is True
        and not report.get("operational_unclassified_files")
        and not report.get("quarantined_import_hits")
        and not report.get("active_unmapped_files")
    )
    # DASS is a desired live autonomous-system state, not merely a property of
    # source code. Physical/cloud infrastructure is not required, but an actual
    # governed runtime cycle must have been observed recently.
    return "post_dass" if structural and _live_runtime_observed() else "pre_dass"


def main() -> int:
    report = measure()
    phase = select_phase(report)
    previous = {}
    if STATE.exists():
        try:
            previous = json.loads(STATE.read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            previous = {}
    transition = previous.get("phase") != phase
    STATE.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "phase": phase,
        "transition": transition,
        "previous_phase": previous.get("phase"),
        "dass_achieved": phase == "post_dass",
        "dass_is_live_state": phase == "post_dass",
        "external_host_required": False,
        "live_runtime_observed": _live_runtime_observed(),
        "measurement": report,
    }
    STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(state, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
