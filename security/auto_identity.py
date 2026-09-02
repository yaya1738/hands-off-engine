"""Read-only identity detection without shell/process execution.

Identity evidence is intentionally advisory. Authorization and operational
execution remain owned by FactoryAuthorityGateway.
"""

import os
from datetime import datetime

MASTER_IDENTITY = {
    "name": "Yair Siegel",
    "key_fingerprints": [],
    "devices": [],
    "trusted_ips": ["127.0.0.1"],
    "env_markers": [("USER", "root"), ("HOME", "/root")],
}


def get_ssh_key_comment():
    return None


def get_ssh_client_ip():
    value = os.environ.get("SSH_CLIENT", "") or os.environ.get("SSH_CONNECTION", "")
    return value.split()[0] if value else None


def get_current_tty_owner():
    return None


def check_authorized_key_used() -> bool:
    return bool(os.environ.get("SSH_AUTH_SOCK"))


def is_yair() -> dict:
    signals = []
    confidence = 0.0
    client_ip = get_ssh_client_ip()
    if client_ip in MASTER_IDENTITY["trusted_ips"]:
        signals.append(f"trusted_ip:{client_ip}")
        confidence += 0.3
    if os.getuid() == 0 and any(x in os.uname().nodename for x in ("handsoff", "ho-", "pm-")):
        signals.append(f"root_on_known_host:{os.uname().nodename}")
        confidence += 0.3
    for env_var, expected in MASTER_IDENTITY["env_markers"]:
        if os.environ.get(env_var) == expected:
            signals.append(f"env:{env_var}={expected}")
            confidence += 0.1
    if check_authorized_key_used():
        signals.append("ssh_key_auth")
        confidence += 0.2
    if client_ip in ("127.0.0.1", None):
        signals.append("local_connection")
        confidence += 0.2
    confidence = min(confidence, 1.0)
    is_master = confidence >= 0.5
    return {
        "is_master": is_master,
        "confidence": round(confidence, 2),
        "signals": signals,
        "identity": MASTER_IDENTITY["name"] if is_master else "Unknown",
        "timestamp": datetime.now().isoformat(),
    }


def log_identity_check(result: dict):
    return False


def require_yair(func):
    def wrapper(*args, **kwargs):
        check = is_yair()
        if not check["is_master"]:
            raise PermissionError(f"Access denied. Identity confidence: {check['confidence']}")
        return func(*args, **kwargs)
    return wrapper


def am_i_yair() -> bool:
    return is_yair()["is_master"]


def whoami() -> str:
    check = is_yair()
    return f"{check['identity']} (confidence: {check['confidence']})"


if __name__ == "__main__":
    result = is_yair()
    print(f"Identity: {result['identity']}")
    print(f"Confidence: {result['confidence'] * 100}%")
    print(f"Signals: {', '.join(result['signals'])}")
    print(f"Access: {'GRANTED' if result['is_master'] else 'DENIED'}")
