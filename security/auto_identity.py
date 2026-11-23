#!/usr/bin/env python3
"""
Private Identity Detection - configured owner verification

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
import re
from pathlib import Path
from datetime import datetime

def _env_list(name: str) -> list:
    return [value.strip() for value in os.getenv(name, "").split(",") if value.strip()]


MASTER_IDENTITY = {
    "name": os.getenv("HANDS_OFF_OWNER_NAME", "Configured owner"),
    "email": os.getenv("HANDS_OFF_OWNER_EMAIL", ""),
    "key_fingerprints": _env_list("HANDS_OFF_OWNER_SSH_KEY_FINGERPRINTS"),
    "devices": _env_list("HANDS_OFF_OWNER_DEVICE_IDS"),
    "trusted_ips": _env_list("HANDS_OFF_OWNER_TRUSTED_IPS"),
    # Environment defaults such as USER=root or HOME=/root are not identity proof.
    "env_markers": [],
}

PRIVATE_DIR = Path(os.getenv("HANDS_OFF_PRIVATE_DIR", str(Path.home() / ".config" / "hands-off-engine"))).expanduser()
IDENTITY_LOG = PRIVATE_DIR / "identity_checks.jsonl"

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
                match = re.search(r"SHA256:[A-Za-z0-9+/=]+", line)
                if match:
                    return match.group(0)
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
    """Verify the configured owner using an explicitly configured SSH fingerprint.

    Hostname, root, IP, working-directory, and SSH-agent presence are not identity
    proof. If no private fingerprint configuration is present, deny by default.
    """
    signals = []
    known = set(MASTER_IDENTITY["key_fingerprints"])
    fingerprint = get_ssh_key_comment()

    if fingerprint and fingerprint in known:
        signals.append("configured_ssh_fingerprint_match")
        confidence = 1.0
        is_master = True
    else:
        signals.append("identity_not_verified")
        confidence = 0.0
        is_master = False

    result = {
        "is_master": is_master,
        "confidence": confidence,
        "signals": signals,
        "identity": MASTER_IDENTITY["name"] if is_master else "Unknown",
        "timestamp": datetime.now().isoformat(),
    }
    log_identity_check(result)
    return result

def log_identity_check(result: dict):
    """Log identity checks for audit"""
    try:
        import json
        PRIVATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            PRIVATE_DIR.chmod(0o700)
        except OSError:
            pass
        with open(IDENTITY_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")
        try:
            IDENTITY_LOG.chmod(0o600)
        except OSError:
            pass
    except OSError:
        pass

def require_yair(func):
    """Decorator - only run when configured owner identity is verified"""
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
    """Simple bool check for configured owner identity."""
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
