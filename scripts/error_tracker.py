#!/usr/bin/env python3
"""Error Tracker — categorizes and tracks errors across all services.

Provides structured error data for the learning loop and self-improvement engine.
"""
import json
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
ERROR_LOG = STATE / "error_tracker.json"


def load_errors():
    if ERROR_LOG.exists():
        try:
            return json.loads(ERROR_LOG.read_text())
        except Exception:
            pass
    return {"errors": [], "patterns": {}, "last_analysis": None}


def save_errors(data):
    STATE.mkdir(parents=True, exist_ok=True)
    ERROR_LOG.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def scan_logs():
    """Scan all service logs for errors."""
    log_dir = STATE / "logs"
    errors = []
    if not log_dir.exists():
        return errors
    
    for log_file in log_dir.glob("*.log"):
        try:
            content = log_file.read_text(errors="replace")
            for line in content.splitlines():
                if "ERROR" in line or "Traceback" in line or "Exception" in line:
                    errors.append({
                        "source": log_file.stem,
                        "message": line.strip()[:200],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
        except Exception:
            continue
    return errors


def categorize_error(message):
    """Categorize an error message."""
    msg_lower = message.lower()
    if "dns" in msg_lower or "resolve" in msg_lower:
        return "network/dns"
    if "connection" in msg_lower or "timeout" in msg_lower:
        return "network/connection"
    if "permission" in msg_lower or "access" in msg_lower:
        return "permission"
    if "import" in msg_lower or "module" in msg_lower:
        return "import"
    if "json" in msg_lower or "parse" in msg_lower:
        return "parse"
    if "409" in message:
        return "conflict/409"
    if "400" in message:
        return "bad_request/400"
    if "no such file" in msg_lower:
        return "file_missing"
    return "other"


def analyze():
    """Analyze error patterns."""
    data = load_errors()
    new_errors = scan_logs()
    
    for err in new_errors:
        err["category"] = categorize_error(err["message"])
        # Dedup
        if not any(e["message"] == err["message"] and e["source"] == err["source"] for e in data["errors"]):
            data["errors"].append(err)
    
    # Keep last 200
    if len(data["errors"]) > 200:
        data["errors"] = data["errors"][-200:]
    
    # Patterns
    categories = Counter(e["category"] for e in data["errors"])
    sources = Counter(e["source"] for e in data["errors"])
    data["patterns"] = {
        "categories": dict(categories),
        "sources": dict(sources),
        "total": len(data["errors"]),
        "top_category": categories.most_common(1)[0] if categories else None,
    }
    data["last_analysis"] = datetime.now(timezone.utc).isoformat()
    
    save_errors(data)
    
    print(f"Errors tracked: {data['patterns']['total']}")
    if data["patterns"]["top_category"]:
        print(f"Top category: {data['patterns']['top_category']}")
    
    return data


if __name__ == "__main__":
    analyze()
