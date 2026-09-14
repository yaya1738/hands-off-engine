#!/usr/bin/env python3
"""Self-Improvement Engine — reads learning state and generates actionable improvements.

This is the "constantly improving" part of the system. It:
1. Reads the learning loop state (patterns, suggestions)
2. Reads the health monitor log
3. Reads bus activity patterns
4. Generates concrete improvement tasks
5. Posts them to the bus for Factory/AnyClaw to execute
"""
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
BUS = ROOT / "ai" / "coordination" / "messages.jsonl"
IMPROVEMENT_STATE = STATE / "improvement_state.json"


def load_json(path):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}


def get_health_trend():
    log = STATE / "health_log.jsonl"
    if not log.exists():
        return {"checks": 0, "issues": 0}
    lines = log.read_text().splitlines()[-20:]
    checks = 0
    issues = 0
    for line in lines:
        try:
            entry = json.loads(line)
            checks += 1
            if not entry.get("healthy", True):
                issues += 1
        except Exception:
            continue
    return {"checks": checks, "issues": issues}


def get_learning_state():
    return load_json(STATE / "learning_state.json")


def generate_improvements():
    """Generate improvement tasks based on current state."""
    improvements = []
    learning = get_learning_state()
    health = get_health_trend()
    patterns = learning.get("patterns", {})
    
    # 1. If health has issues, add monitoring improvement
    if health["issues"] > 0:
        improvements.append({
            "id": str(uuid.uuid4()),
            "category": "reliability",
            "title": "Investigate health failures",
            "description": f"{health['issues']} health issues in last {health['checks']} checks. Review health_log.jsonl for patterns.",
            "priority": "high",
            "actionable": True,
        })
    
    # 2. If success rate is low, add validation improvement
    rate = patterns.get("success_rate", 1.0)
    if rate < 0.8 and patterns.get("total_tasks", 0) > 0:
        improvements.append({
            "id": str(uuid.uuid4()),
            "category": "quality",
            "title": "Improve task validation",
            "description": f"Success rate {rate:.0%}. Add input validation, retry logic, and error categorization.",
            "priority": "high",
            "actionable": True,
        })
    
    # 3. Bus is growing — suggest cleanup
    if BUS.exists():
        lines = len(BUS.read_text().splitlines())
        if lines > 200:
            improvements.append({
                "id": str(uuid.uuid4()),
                "category": "maintenance",
                "title": "Clean up bus messages",
                "description": f"Bus has {lines} lines. Archive old continuation events, keep task_assignments and results.",
                "priority": "medium",
                "actionable": True,
            })
    
    # 4. Add operator convenience improvements
    improvements.append({
        "id": str(uuid.uuid4()),
        "category": "usability",
        "title": "Add Termux boot launcher",
        "description": "Create Termux:Boot script to auto-start Node 1 + Telegram bridge + Control Room on device boot.",
        "priority": "medium",
        "actionable": True,
    })
    
    # 5. Security hardening (from audit)
    improvements.append({
        "id": str(uuid.uuid4()),
        "category": "security",
        "title": "Validate sender_id against registered parties",
        "description": "CommHub.receive() should reject unknown sender_ids to prevent bus poisoning.",
        "priority": "medium",
        "actionable": True,
    })
    
    # 6. Learning improvement
    if patterns.get("total_tasks", 0) > 10 and rate > 0.9:
        improvements.append({
            "id": str(uuid.uuid4()),
            "category": "expansion",
            "title": "Expand autonomous task scope",
            "description": f"System is stable ({rate:.0%} over {patterns['total_tasks']} tasks). Consider enabling autonomous web research, file analysis, or monitoring tasks.",
            "priority": "low",
            "actionable": True,
        })
    
    return improvements


def save_improvements(improvements):
    state = {
        "improvements": improvements,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(improvements),
    }
    IMPROVEMENT_STATE.parent.mkdir(parents=True, exist_ok=True)
    IMPROVEMENT_STATE.write_text(json.dumps(state, indent=2) + "\n")
    return state


def run():
    improvements = generate_improvements()
    state = save_improvements(improvements)
    
    print(f"Self-improvement: {len(improvements)} improvements generated")
    for imp in improvements:
        print(f"  [{imp['priority']}] {imp['category']}: {imp['title']}")
    
    return state


if __name__ == "__main__":
    run()
