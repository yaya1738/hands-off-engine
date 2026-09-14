#!/usr/bin/env python3
"""Hands-Off Engine Dashboard — one terminal view of everything."""
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
BUS = ROOT / "ai" / "coordination" / "messages.jsonl"
STATE = ROOT / "state"


def count_bus():
    if not BUS.exists():
        return 0, {}, {}
    msgs = []
    for line in BUS.read_text().splitlines():
        try:
            msgs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    from collections import Counter
    types = Counter(m.get("type") for m in msgs)
    routes = Counter(f'{m["from"]}→{m["to"]}' for m in msgs)
    return len(msgs), types, routes


def process_status():
    procs = []
    for pid_dir in Path("/proc").iterdir():
        if not pid_dir.name.isdigit():
            continue
        try:
            cmd = (pid_dir / "cmdline").read_text().replace("\x00", " ")
            if any(x in cmd for x in ["node1_runtime", "telegram_bridge", "yair_control_room"]):
                name = "node1_runtime" if "node1_runtime" in cmd else (
                    "telegram_bridge" if "telegram_bridge" in cmd else "control_room"
                )
                procs.append({"pid": int(pid_dir.name), "name": name})
        except (FileNotFoundError, PermissionError):
            continue
    return procs


def governed_state():
    try:
        f = STATE / "governed_root_status.json"
        if f.exists():
            return json.loads(f.read_text())
    except Exception:
        pass
    return {"status": "unknown"}


def factory_intake_state():
    try:
        f = STATE / "factory_intake_state.json"
        if f.exists():
            d = json.loads(f.read_text())
            return {
                "consumed": len(d.get("consumed_ids", [])),
                "decisions": d.get("decision_count", 0),
            }
    except Exception:
        pass
    return {"consumed": 0, "decisions": 0}


def test_status():
    try:
        import subprocess
        r = subprocess.run(
            ["python3", "-m", "pytest", "tests/test_worker_hardening.py",
             "tests/test_continuation.py", "tests/test_factory_intake.py",
             "tests/test_event_router.py", "tests/test_termux_supervisor.py",
             "tests/test_node1_runtime.py", "tests/test_e2e_pipeline.py",
             "tests/test_governed_authority.py", "tests/test_governed_root.py",
             "tests/test_yair_control_room.py", "-q", "--tb=no"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=30
        )
        for line in test_status.output_lines:
            if "passed" in line:
                return line.strip()
        return test_status.output_lines[-1].strip() if test_status.output_lines else "unknown"
    except Exception:
        return "error"

test_status.output_lines = []


def main():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    procs = process_status()
    bus_count, bus_types, bus_routes = count_bus()
    gov = governed_state()
    fi = factory_intake_state()
    
    print(f"\n{'='*50}")
    print(f"  HANDS-OFF ENGINE DASHBOARD")
    print(f"  {now}")
    print(f"{'='*50}\n")
    
    # Services
    print("SERVICES:")
    svc_map = {p["name"]: p["pid"] for p in procs}
    for name in ["node1_runtime", "telegram_bridge", "control_room"]:
        if name in svc_map:
            print(f"  ✅ {name:20s} pid {svc_map[name]}")
        else:
            print(f"  ❌ {name:20s} NOT RUNNING")
    
    # Bus
    print(f"\nCOORDINATION BUS:")
    print(f"  Messages:     {bus_count}")
    print(f"  Types:        {dict(bus_types)}")
    
    # Authority
    print(f"\nGOVERNANCE:")
    print(f"  Status:       {gov.get('status', 'unknown')}")
    print(f"  Exec enabled: {gov.get('execution_enabled', 'unknown')}")
    
    # Factory intake
    print(f"\nFACTORY INTAKE:")
    print(f"  Consumed:     {fi['consumed']} events")
    print(f"  Decisions:    {fi['decisions']}")
    
    # Git
    try:
        import subprocess
        r = subprocess.run(["git", "log", "-1", "--format=%h %s"], capture_output=True, text=True, cwd=str(ROOT))
        print(f"\nGIT: {r.stdout.strip()}")
    except Exception:
        pass
    
    print(f"\n{'='*50}\n")


if __name__ == "__main__":
    main()
