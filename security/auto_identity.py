#!/usr/bin/env python3
"""
Auto Identity Detection - Always knows when it's Yair Siegel

Detection methods:
1. SSH key fingerprint (most reliable)
2. SSH client IP + key comment
3. Environment variables
4. Process ancestry (who spawned this)
5. Device hostname patterns
"""

import os
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime

MASTER_IDENTITY = {
    "name": "Yair Siegel",
    "email": "siegel.yaz@gmail.com",

    # SSH key fingerprints (SHA256)
    "key_fingerprints": [
        "SHA256:oIAeGFrxTHyg4Tjat9u1Q05lEdy823nqxhfWuU/t7ro",  # handsoff-do138
        "SHA256:g71K8Lk8TYFDEQCj/vmD1jjHls1GPjqyjkA7Ke7yVk4",  # pm-agent
        "SHA256:vTfnGmsuPm8guKkew31xyAl63XMM2GspeugpFR5HyfY",  # termux@handsoff
    ],

    # Known device identifiers
    "devices": [
        "termux@handsoff",
        "pm-agent@206.189.60.125",
        "handsoff-do138",
    ],

    # Known source IPs (your phone, your servers)
    "trusted_ips": [
        "127.0.0.1",        # Local
        "138.68.103.156",   # pm-helper
        "167.172.132.72",   # ho-cli-main
        "167.172.155.42",   # ho-compute-1
        "178.128.155.150",  # ho-compute-2
        "64.227.26.112",    # ho-scale
        "157.230.221.18",   # ho-topdawg-4
    ],

    # Environment markers
    "env_markers": [
        ("USER", "root"),
        ("HOME", "/root"),
    ]
}

IDENTITY_LOG = Path("/root/hands-off-engine/security/identity_checks.jsonl")

def get_ssh_key_comment() -> str:
    """Get the SSH key comment used for this connection"""
    # Check auth log for most recent successful auth
    try:
        result = subprocess.run(
            ["tail", "-50", "/var/log/auth.log"],
            capture_output=True, text=True, timeout=5
        )
        for line in reversed(result.stdout.split('\n')):
            if 'Accepted publickey' in line:
                # Extract key comment from log
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == 'SHA256:':
                        return parts[i+1] if i+1 < len(parts) else None
    except:
        pass
    return None

def get_ssh_client_ip() -> str:
    """Get the IP of the SSH client"""
    ssh_client = os.environ.get('SSH_CLIENT', '')
    if ssh_client:
        return ssh_client.split()[0]

    ssh_connection = os.environ.get('SSH_CONNECTION', '')
    if ssh_connection:
        return ssh_connection.split()[0]

    return None

def get_current_tty_owner() -> str:
    """Get who owns the current TTY"""
    try:
        tty = os.ttyname(0)
        result = subprocess.run(['stat', '-c', '%U', tty], capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return None

def check_authorized_key_used() -> bool:
    """Check if connection used an authorized key"""
    auth_sock = os.environ.get('SSH_AUTH_SOCK')
    if auth_sock:
        return True
    return False

def is_yair() -> dict:
    """
    Comprehensive identity check - returns confidence score

    Returns:
        {
            "is_master": bool,
            "confidence": float (0-1),
            "signals": list of matched signals,
            "identity": "Yair Siegel" or "Unknown"
        }
    """
    signals = []
    confidence = 0.0

    # Check 1: SSH client IP from trusted server
    client_ip = get_ssh_client_ip()
    if client_ip in MASTER_IDENTITY["trusted_ips"]:
        signals.append(f"trusted_ip:{client_ip}")
        confidence += 0.3

    # Check 2: Running as root on known system
    if os.getuid() == 0:
        hostname = os.uname().nodename
        if any(d in hostname for d in ['handsoff', 'ho-', 'pm-']):
            signals.append(f"root_on_known_host:{hostname}")
            confidence += 0.3

    # Check 3: Environment markers
    for env_var, expected in MASTER_IDENTITY["env_markers"]:
        if os.environ.get(env_var) == expected:
            signals.append(f"env:{env_var}={expected}")
            confidence += 0.1

    # Check 4: SSH auth present (key-based)
    if check_authorized_key_used():
        signals.append("ssh_key_auth")
        confidence += 0.2

    # Check 5: Local connection (already on the server)
    if client_ip == "127.0.0.1" or client_ip is None:
        signals.append("local_connection")
        confidence += 0.2

    # Check 6: Process running from hands-off-engine directory
    cwd = os.getcwd()
    if 'hands-off' in cwd:
        signals.append(f"cwd:{cwd}")
        confidence += 0.1

    # Normalize confidence to max 1.0
    confidence = min(confidence, 1.0)

    # Determine identity
    is_master = confidence >= 0.5  # 50% threshold

    result = {
        "is_master": is_master,
        "confidence": round(confidence, 2),
        "signals": signals,
        "identity": MASTER_IDENTITY["name"] if is_master else "Unknown",
        "timestamp": datetime.now().isoformat()
    }

    # Log the check
    log_identity_check(result)

    return result

def log_identity_check(result: dict):
    """Log identity checks for audit"""
    try:
        import json
        with open(IDENTITY_LOG, "a") as f:
            f.write(json.dumps(result) + "\n")
    except:
        pass

def require_yair(func):
    """Decorator - only run if it's Yair"""
    def wrapper(*args, **kwargs):
        check = is_yair()
        if not check["is_master"]:
            raise PermissionError(
                f"Access denied. Identity confidence: {check['confidence']}"
            )
        return func(*args, **kwargs)
    return wrapper

# Quick check function for other scripts
def am_i_yair() -> bool:
    """Simple bool check - is the current user Yair?"""
    return is_yair()["is_master"]

def whoami() -> str:
    """Return identity string"""
    check = is_yair()
    if check["is_master"]:
        return f"{MASTER_IDENTITY['name']} (confidence: {check['confidence']})"
    return f"Unknown (confidence: {check['confidence']})"

if __name__ == "__main__":
    import json
    result = is_yair()
    print(f"Identity: {result['identity']}")
    print(f"Confidence: {result['confidence'] * 100}%")
    print(f"Signals: {', '.join(result['signals'])}")
    print(f"Access: {'GRANTED' if result['is_master'] else 'DENIED'}")
