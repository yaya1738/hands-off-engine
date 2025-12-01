#!/usr/bin/env python3
"""
Automation Health Monitor

Checks the health of all automation components and reports status.
Can be run manually or scheduled via cron.

Usage:
    python scripts/automation_health_monitor.py [--json] [--verbose]
    
Options:
    --json      Output in JSON format
    --verbose   Show detailed information
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

STATE_DIR = REPO_ROOT / "state"
AI_DIR = REPO_ROOT / "ai"
AUTONOMOUS_DIR = REPO_ROOT / "autonomous"


def check_component_exists(name: str, path: Path) -> Dict[str, Any]:
    """Check if a component file or directory exists."""
    exists = path.exists()
    return {
        "component": name,
        "exists": exists,
        "path": str(path),
        "status": "ok" if exists else "missing"
    }


def check_json_valid(name: str, path: Path) -> Dict[str, Any]:
    """Check if a JSON file exists and is valid."""
    if not path.exists():
        return {
            "component": name,
            "status": "missing",
            "path": str(path)
        }
    
    try:
        with open(path) as f:
            data = json.load(f)
        
        return {
            "component": name,
            "status": "ok",
            "path": str(path),
            "size": len(json.dumps(data))
        }
    except json.JSONDecodeError as e:
        return {
            "component": name,
            "status": "invalid_json",
            "path": str(path),
            "error": str(e)
        }
    except Exception as e:
        return {
            "component": name,
            "status": "error",
            "path": str(path),
            "error": str(e)
        }


def check_cascade_system() -> Dict[str, Any]:
    """Check if the cascade directive system is functional."""
    try:
        from autonomous.absolute_directive import (
            cascade_directive,
            get_master,
            get_directive
        )
        
        master = get_master()
        directive = get_directive()
        
        # Test cascade
        result = cascade_directive("Health check test")
        
        return {
            "component": "cascade_system",
            "status": "ok",
            "master": master,
            "directive": directive,
            "levels_touched": len(result.get("levels_touched", []))
        }
    except Exception as e:
        return {
            "component": "cascade_system",
            "status": "error",
            "error": str(e)
        }


def check_ai_coordination() -> Dict[str, Any]:
    """Check AI coordination system health."""
    status_file = AI_DIR / "coordination" / "status.json"
    
    result = check_json_valid("ai_coordination", status_file)
    
    if result["status"] == "ok":
        try:
            with open(status_file) as f:
                status = json.load(f)
            
            autonomous_mode = status.get("autonomous_mode", {})
            active_agents = status.get("active_agents", [])
            
            result["autonomous_enabled"] = autonomous_mode.get("enabled") is not None
            result["active_agents"] = len(active_agents)
            result["current_phase"] = status.get("current_phase", "unknown")
        except Exception as e:
            result["warning"] = f"Could not parse details: {e}"
    
    return result


def check_safety_controls() -> Dict[str, Any]:
    """Check that safety controls are in place."""
    checks = []
    
    # Check for emergency stop locks
    emergency_locks = [
        STATE_DIR / "EMERGENCY_STOP.lock",
        STATE_DIR / "SYSTEM_FAILURE.lock"
    ]
    
    has_emergency_lock = any(lock.exists() for lock in emergency_locks)
    
    checks.append({
        "check": "no_emergency_locks",
        "status": "warning" if has_emergency_lock else "ok",
        "message": "Emergency lock detected" if has_emergency_lock else "No emergency locks"
    })
    
    # Check for circuit breaker
    circuit_breaker = STATE_DIR / "circuit_breaker.lock"
    checks.append({
        "check": "no_circuit_breaker",
        "status": "warning" if circuit_breaker.exists() else "ok",
        "message": "Circuit breaker active" if circuit_breaker.exists() else "No circuit breaker"
    })
    
    # Check DRYRUN in autoloop
    autoloop_file = REPO_ROOT / "ho_autoloop.py"
    if autoloop_file.exists():
        with open(autoloop_file) as f:
            content = f.read()
        
        has_dryrun = "DRYRUN" in content
        checks.append({
            "check": "dryrun_present",
            "status": "ok" if has_dryrun else "error",
            "message": "DRYRUN mode found" if has_dryrun else "DRYRUN mode not found"
        })
    
    overall_status = "ok"
    if any(c["status"] == "error" for c in checks):
        overall_status = "error"
    elif any(c["status"] == "warning" for c in checks):
        overall_status = "warning"
    
    return {
        "component": "safety_controls",
        "status": overall_status,
        "checks": checks
    }


def check_documentation() -> Dict[str, Any]:
    """Check that key documentation files exist."""
    docs = [
        ("automation_metrics", REPO_ROOT / "docs" / "AUTOMATION_SUCCESS_METRICS.md"),
        ("troubleshooting", REPO_ROOT / "docs" / "AUTOMATION_TROUBLESHOOTING_GUIDE.md"),
        ("risk_model", REPO_ROOT / "docs" / "RISK_MODEL_V1.md"),
        ("deployment_status", AI_DIR / "DEPLOYMENT_STATUS.md")
    ]
    
    doc_checks = []
    for name, path in docs:
        exists = path.exists()
        doc_checks.append({
            "doc": name,
            "exists": exists,
            "path": str(path)
        })
    
    all_exist = all(c["exists"] for c in doc_checks)
    
    return {
        "component": "documentation",
        "status": "ok" if all_exist else "warning",
        "docs": doc_checks
    }


def run_health_check(verbose: bool = False) -> Dict[str, Any]:
    """Run all health checks and return results."""
    timestamp = datetime.now(timezone.utc).isoformat()
    
    checks = {
        "timestamp": timestamp,
        "overall_status": "ok",
        "checks": []
    }
    
    # Component existence checks
    components = [
        ("autonomous_directory", AUTONOMOUS_DIR),
        ("ai_directory", AI_DIR),
        ("state_directory", STATE_DIR),
        ("autoloop_script", REPO_ROOT / "ho_autoloop.py"),
        ("ai_runner_script", REPO_ROOT / "ai_runner.py")
    ]
    
    for name, path in components:
        checks["checks"].append(check_component_exists(name, path))
    
    # State file checks
    state_files = [
        ("knowledge_json", STATE_DIR / "knowledge.json"),
        ("ai_nexus_state", STATE_DIR / "ai_nexus_state.json")
    ]
    
    for name, path in state_files:
        checks["checks"].append(check_json_valid(name, path))
    
    # System checks
    checks["checks"].append(check_cascade_system())
    checks["checks"].append(check_ai_coordination())
    checks["checks"].append(check_safety_controls())
    checks["checks"].append(check_documentation())
    
    # Determine overall status
    statuses = [c.get("status") for c in checks["checks"]]
    if "error" in statuses:
        checks["overall_status"] = "error"
    elif "warning" in statuses:
        checks["overall_status"] = "warning"
    elif "missing" in statuses:
        checks["overall_status"] = "degraded"
    else:
        checks["overall_status"] = "ok"
    
    return checks


def print_human_readable(results: Dict[str, Any], verbose: bool = False):
    """Print results in human-readable format."""
    timestamp = results["timestamp"]
    overall = results["overall_status"]
    
    # Status emoji
    status_emoji = {
        "ok": "✅",
        "warning": "⚠️ ",
        "error": "❌",
        "degraded": "🟡",
        "missing": "❓"
    }
    
    print("=" * 60)
    print("Automation Health Monitor")
    print("=" * 60)
    print(f"Timestamp: {timestamp}")
    print(f"Overall Status: {status_emoji.get(overall, '?')} {overall.upper()}")
    print("=" * 60)
    print()
    
    # Group by status
    ok_checks = []
    warning_checks = []
    error_checks = []
    
    for check in results["checks"]:
        status = check.get("status", "unknown")
        if status == "ok":
            ok_checks.append(check)
        elif status in ["warning", "degraded", "missing"]:
            warning_checks.append(check)
        else:
            error_checks.append(check)
    
    # Show errors first
    if error_checks:
        print("ERRORS:")
        for check in error_checks:
            component = check.get("component", "unknown")
            error = check.get("error", "Unknown error")
            print(f"  ❌ {component}: {error}")
        print()
    
    # Show warnings
    if warning_checks:
        print("WARNINGS:")
        for check in warning_checks:
            component = check.get("component", "unknown")
            print(f"  ⚠️  {component}")
            if verbose:
                for key, value in check.items():
                    if key not in ["component", "status"]:
                        print(f"      {key}: {value}")
        print()
    
    # Show ok checks (only in verbose mode)
    if verbose and ok_checks:
        print("OK:")
        for check in ok_checks:
            component = check.get("component", "unknown")
            print(f"  ✅ {component}")
        print()
    
    # Summary
    print("=" * 60)
    print(f"Total Checks: {len(results['checks'])}")
    print(f"  OK: {len(ok_checks)}")
    print(f"  Warnings: {len(warning_checks)}")
    print(f"  Errors: {len(error_checks)}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Check health of automation components"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed information"
    )
    
    args = parser.parse_args()
    
    results = run_health_check(verbose=args.verbose)
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_human_readable(results, verbose=args.verbose)
    
    # Exit with appropriate code
    if results["overall_status"] == "error":
        sys.exit(1)
    elif results["overall_status"] in ["warning", "degraded"]:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
