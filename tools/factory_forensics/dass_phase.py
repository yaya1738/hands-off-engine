#!/usr/bin/env python3
"""Deterministically select the autonomous operating phase from DASS measurement."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEASURE = ROOT / "tools/factory_forensics/dass_measurement.py"
STATE = ROOT / "state" / "dass_phase.json"


def measure() -> dict:
    proc = subprocess.run(["python", str(MEASURE)], cwd=ROOT, text=True, capture_output=True)
    if not proc.stdout.strip():
        raise SystemExit(proc.stderr.strip() or "DASS measurement produced no report")
    report = json.loads(proc.stdout)
    report["measurement_exit_code"] = proc.returncode
    return report


def select_phase(report: dict) -> str:
    achieved = (
        report.get("dass_coverage_percent") == report.get("target_percent")
        and report.get("dass_pure") is True
        and not report.get("operational_unclassified_files")
        and not report.get("quarantined_import_hits")
    )
    return "post_dass" if achieved else "pre_dass"


def main() -> int:
    report = measure()
    phase = select_phase(report)
    previous = {}
    if STATE.exists():
        previous = json.loads(STATE.read_text(encoding="utf-8"))
    transition = previous.get("phase") != phase
    STATE.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "phase": phase,
        "transition": transition,
        "previous_phase": previous.get("phase"),
        "dass_achieved": phase == "post_dass",
        "measurement": report,
    }
    STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(state, indent=2, sort_keys=True))
    return 0 if phase in {"pre_dass", "post_dass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
