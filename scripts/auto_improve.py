#!/usr/bin/env python3
"""Auto-Improvement Executor — executes low-risk self-improvements automatically.

Reads improvement suggestions and executes the safe ones (cleanup, metrics,
documentation updates) while flagging high-risk ones for approval.
"""
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
IMPROVE_LOG = STATE / "auto_improve_log.json"

# Only these categories auto-execute
SAFE_CATEGORIES = {"maintenance", "usability", "documentation"}
# These require approval
REQUIRES_APPROVAL = {"reliability", "quality", "security", "expansion"}


def load_improvements():
    try:
        return json.loads((STATE / "improvement_state.json").read_text()).get("improvements", [])
    except Exception:
        return []


def execute_improvement(imp):
    """Execute a single safe improvement."""
    cat = imp.get("category", "")
    title = imp.get("title", "")
    
    if cat == "maintenance" and "bus" in title.lower():
        # Auto-run bus cleanup
        r = subprocess.run([sys.executable, str(ROOT / "scripts/bus_cleanup.py")],
                          capture_output=True, text=True, timeout=30)
        return {"executed": True, "action": "bus_cleanup", "output": r.stdout.strip()}
    
    if cat == "maintenance" and "integrity" in title.lower():
        r = subprocess.run([sys.executable, str(ROOT / "scripts/state_integrity.py")],
                          capture_output=True, text=True, timeout=30)
        return {"executed": True, "action": "integrity_check", "output": r.stdout.strip()}
    
    if cat == "usability" and "dashboard" in title.lower():
        return {"executed": False, "action": "deferred", "reason": "Dashboard already exists"}
    
    return {"executed": False, "action": "skipped", "reason": f"Category '{cat}' not auto-executable"}


def run():
    improvements = load_improvements()
    results = []
    executed = 0
    deferred = 0
    
    for imp in improvements:
        cat = imp.get("category", "")
        
        if cat in SAFE_CATEGORIES:
            result = execute_improvement(imp)
            result["improvement"] = imp.get("title", "")
            results.append(result)
            if result.get("executed"):
                executed += 1
        elif cat in REQUIRES_APPROVAL:
            results.append({
                "executed": False,
                "action": "needs_approval",
                "improvement": imp.get("title", ""),
                "category": cat,
            })
            deferred += 1
        else:
            results.append({"executed": False, "action": "unknown_category", "improvement": imp.get("title", "")})
    
    log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_improvements": len(improvements),
        "executed": executed,
        "deferred": deferred,
        "results": results,
    }
    
    STATE.mkdir(parents=True, exist_ok=True)
    IMPROVE_LOG.write_text(json.dumps(log, indent=2) + "\n")
    
    print(f"Auto-improve: {executed} executed, {deferred} deferred (needs approval)")
    for r in results:
        status = "✅" if r.get("executed") else "⏳"
        print(f"  {status} {r.get('improvement', '?')}")
    
    return log


if __name__ == "__main__":
    run()
