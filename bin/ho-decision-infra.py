#!/usr/bin/env python3
"""
ho-decision-infra.py

Post-processor for decision_report.json living in /root/hands-off-out/state.

Responsibilities:
- Read base decision_report.json (output of core decision engine).
- Read health.json and attach:
    - health_status
    - infra_allow_trades
    - infra_reason
- Optionally read and attach:
    - polymarket-model.json   -> decision["polymarket"]["model"]
    - polymarket-compact.json -> decision["polymarket"]["compact"]
    - finance_report.json     -> decision["finance"]

Script is conservative: if any file is missing or malformed, it logs a warning
and skips that attachment rather than failing.
"""

import json
from pathlib import Path
from typing import Any, Dict

STATE = Path("/root/hands-off-out/state")
DECISION = STATE / "decision_report.json"
HEALTH = STATE / "health.json"
PM_MODEL = STATE / "polymarket-model.json"
PM_COMPACT = STATE / "polymarket-compact.json"
FINANCE = STATE / "finance_report.json"


def load_json(path: Path, label: str) -> Dict[str, Any]:
    if not path.exists():
        print(f"[warn] {label} missing at {path}, skipping")
        return {}
    try:
        return json.loads(path.read_text())
    except Exception as e:
        print(f"[warn] failed to parse {label}: {e}")
        return {}


def main():
    # --- base decision ---
    if not DECISION.exists():
        print("[warn] no base decision_report.json to decorate")
        return

    try:
        base = json.loads(DECISION.read_text())
    except Exception as e:
        print(f"[warn] failed to parse base decision_report.json: {e}")
        return

    # --- health / infra gate ---
    health = load_json(HEALTH, "health.json")
    status = (
        health.get("status")
        or health.get("overall_status")
        or base.get("health_status")
        or "unknown"
    )

    # issues might be a list, dict, or absent
    issues = health.get("issues") or health.get("problems") or []
    has_issues = False
    if isinstance(issues, list):
        has_issues = len(issues) > 0
    elif isinstance(issues, dict):
        has_issues = any(issues.values())

    # base infra_allow from decider, default True
    base_allow = base.get("infra_allow_trades")
    if base_allow is None:
        base_allow = True

    final_allow = bool(base_allow) and not has_issues

    reason_bits = []
    reason_bits.append(f"health_status={status}")
    if has_issues:
        reason_bits.append("issues_present")
    else:
        reason_bits.append("no_health_issues")
    infra_reason = "; ".join(reason_bits)

    base["health_status"] = status
    base["infra_allow_trades"] = final_allow
    base["infra_reason"] = infra_reason

    # --- Polymarket attachments ---
    pm_block = base.get("polymarket") or {}
    if not isinstance(pm_block, dict):
        pm_block = {}

    pm_model = load_json(PM_MODEL, "polymarket-model.json")
    if pm_model:
        pm_block["model"] = pm_model
        print("[info] attached polymarket-model.json into decision_report.polymarket.model")

    pm_compact = load_json(PM_COMPACT, "polymarket-compact.json")
    if pm_compact:
        pm_block["compact"] = pm_compact
        print("[info] attached polymarket-compact.json into decision_report.polymarket.compact")

    base["polymarket"] = pm_block

    # --- Finance attachment ---
    finance = load_json(FINANCE, "finance_report.json")
    if finance:
        base["finance"] = finance
        print("[info] attached finance_report.json into decision_report.finance")

    # --- write back (atomic: write to .tmp, then rename) ---
    tmp = DECISION.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(base, indent=2, sort_keys=True))
    tmp.replace(DECISION)
    print("[ok] ho-decision-infra.py updated decision_report.json")


if __name__ == "__main__":
    main()
