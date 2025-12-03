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
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent

def get_polymarket_balance():
    """Get current Polymarket balance"""
    try:
        os.chdir(REPO_ROOT)
        result = subprocess.run(
            ['python3', '-c', '''
import os
os.chdir("/root/hands-off-engine")
exec(open(".env.polymarket").read().replace("export ", ""))
from executor.trading_safeguards import TradingSafeguards
s = TradingSafeguards()
ok, msg = s.check_wallet_balance(0)
import re
match = re.search(r"\\$([\\d.]+)", msg)
print(match.group(1) if match else "0")
'''],
            capture_output=True, text=True, timeout=30
        )
        return float(result.stdout.strip()) if result.stdout.strip() else 0
    except:
        return 0

def get_api_status():
    """Check which APIs are working"""
    status = {}
    
    # Check env vars
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        content = env_file.read_text()
        status['openai'] = 'OPENAI_API_KEY=' in content and 'your-' not in content
    
    # Telegram - test it
    try:
        import requests
        r = requests.get('https://api.telegram.org/bot8214203655:AAGkAamvjQq0b7T7lmaTPDd-yYY_hvo_xvA/getMe', timeout=5)
        status['telegram'] = r.json().get('ok', False)
    except:
        status['telegram'] = False
    
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
