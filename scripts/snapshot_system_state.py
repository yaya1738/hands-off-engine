#!/usr/bin/env python3
"""
System State Snapshot Generator
Captures complete system state to permanent record
"""

# UNIFIED AI - All systems serve Yair Siegel
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = "Yair Siegel"


import json
import os
import subprocess
import os
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent

def get_polymarket_balance():
    """Return a wallet balance only from a recent complete RPC proof."""
    try:
        from finance.truth import read_verified_polymarket_balance
        result = read_verified_polymarket_balance(REPO_ROOT / "finance" / "yair_finance_hub.json")
        return result["balance_usdc"] if result["verified"] else None
    except Exception:
        return None


def get_api_status():
    """Check configured APIs without embedding or assuming credentials."""
    status = {}
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        content = env_file.read_text(encoding="utf-8")
        status["openai"] = "OPENAI_API_KEY=" in content and "your-" not in content

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        status["telegram"] = False
    else:
        try:
            import requests
            response = requests.get(
                f"https://api.telegram.org/bot{token}/getMe",
                timeout=5,
            )
            response.raise_for_status()
            status["telegram"] = response.json().get("ok", False)
        except Exception:
            status["telegram"] = False
    return status


def get_git_status():
    """Get current git state"""
    try:
        result = subprocess.run(['git', 'log', '--oneline', '-5'], capture_output=True, text=True, cwd=REPO_ROOT)
        return result.stdout.strip().split('\n')
    except:
        return []

def generate_snapshot():
    """Generate complete system snapshot"""
    snapshot = {
        "generated": datetime.utcnow().isoformat() + "Z",
        "polymarket_balance": get_polymarket_balance(),
        "polymarket_balance_verified": get_polymarket_balance() is not None,
        "api_status": get_api_status(),
        "recent_commits": get_git_status(),
        "server_ip": "138.68.103.156",
        "landing_page": "http://138.68.103.156:8080"
    }
    
    # Save snapshot
    snapshot_file = REPO_ROOT / "state" / "permanent" / "latest_snapshot.json"
    snapshot_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(snapshot_file, 'w') as f:
        json.dump(snapshot, f, indent=2)
    
    print(f"Snapshot saved to {snapshot_file}")
    print(json.dumps(snapshot, indent=2))
    
    return snapshot

if __name__ == "__main__":
    generate_snapshot()
