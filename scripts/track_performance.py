#!/usr/bin/env python3
"""
Performance Tracker - Logs trading system performance metrics
"""

# UNIFIED AI - All systems serve Yair Siegel
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = "Yair Siegel"

import json
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
EXEC_PLAN = REPO_ROOT / "executor" / "execution_plan.json"
PERF_LOG = REPO_ROOT / "logs" / "performance_tracking.jsonl"

def main():
    if not EXEC_PLAN.exists():
        print("[skip] No execution plan found")
        return
    
    with open(EXEC_PLAN) as f:
        plan = json.load(f)
    
    # Log performance metrics
    PERF_LOG.parent.mkdir(parents=True, exist_ok=True)
    
    metric = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_orders": plan.get("total_orders", 0),
        "total_size_usd": plan.get("total_size_usd", 0.0),
        "mode": "dryrun" if plan.get("dryrun", True) else "live",
        "orders": len(plan.get("orders", [])),
        "avg_confidence": sum(o.get("confidence", 0) for o in plan.get("orders", [])) / max(len(plan.get("orders", [])), 1)
    }
    
    with open(PERF_LOG, 'a') as f:
        f.write(json.dumps(metric) + '\n')
    
    print("✓ Metrics logged")
    print(f"  Orders: {metric['total_orders']}")
    print(f"  Size: ${metric['total_size_usd']:.2f}")
    print(f"  Signals: {metric['orders']} selected")

if __name__ == "__main__":
    main()
