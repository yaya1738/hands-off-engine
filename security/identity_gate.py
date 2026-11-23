"""
Identity Gate - Access based on WHO you are, not just WHAT you have

YOUR ACCESS: Always (identity verified by multiple factors)
OTHERS ACCESS: Only when it benefits you (approval queue)
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

def _env_list(name: str) -> list:
    return [value.strip() for value in os.getenv(name, "").split(",") if value.strip()]


PRIVATE_DIR = Path(os.getenv("HANDS_OFF_PRIVATE_DIR", str(Path.home() / ".config" / "hands-off-engine"))).expanduser()
MASTER_IDENTITY = {
    "name": os.getenv("HANDS_OFF_OWNER_NAME", "Configured owner"),
    "email": os.getenv("HANDS_OFF_OWNER_EMAIL", ""),
    "devices": _env_list("HANDS_OFF_OWNER_DEVICE_IDS"),
    "ssh_key_fingerprints": _env_list("HANDS_OFF_OWNER_SSH_KEY_FINGERPRINTS"),
}

APPROVAL_QUEUE = PRIVATE_DIR / "approval_queue.json"
ACCESS_LOG = PRIVATE_DIR / "access_log.jsonl"


def _ensure_private_dir() -> None:
    PRIVATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        PRIVATE_DIR.chmod(0o700)
    except OSError:
        pass


def is_master(ssh_key_comment: str = None, device_id: str = None) -> bool:
    """Require a configured SSH fingerprint; device/hostname hints alone are insufficient."""
    fingerprints = set(MASTER_IDENTITY["ssh_key_fingerprints"])
    devices = set(MASTER_IDENTITY["devices"])
    if not ssh_key_comment or ssh_key_comment not in fingerprints:
        return False
    if device_id is not None and devices and device_id not in devices:
        return False
    return True

def request_access(requester: str, purpose: str, benefit_to_master: str) -> str:
    """Others must explain how access benefits Yair"""
    _ensure_private_dir()
    request = {
        "id": hashlib.sha256(f"{requester}{datetime.now()}".encode()).hexdigest()[:12],
        "requester": requester,
        "purpose": purpose,
        "benefit_to_master": benefit_to_master,
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
        "expires": None
    }
    
    queue = []
    if APPROVAL_QUEUE.exists():
        queue = json.loads(APPROVAL_QUEUE.read_text())
    queue.append(request)
    APPROVAL_QUEUE.write_text(json.dumps(queue, indent=2))
    
    return request["id"]

def approve_access(request_id: str, duration_hours: int = 1) -> dict:
    """Master approves access with time limit"""
    if not APPROVAL_QUEUE.exists():
        return {"error": "No pending requests"}
    
    queue = json.loads(APPROVAL_QUEUE.read_text())
    for req in queue:
        if req["id"] == request_id:
            req["status"] = "approved"
            req["approved_at"] = datetime.now().isoformat()
            req["expires"] = (datetime.now().timestamp() + duration_hours * 3600)
            APPROVAL_QUEUE.write_text(json.dumps(queue, indent=2))
            return req
    
    return {"error": "Request not found"}

def check_access(requester: str) -> dict:
    """Check if requester is a configured SSH fingerprint or has approved access."""
    # Master access requires a cryptographic fingerprint, not a device-name hint.
    if is_master(ssh_key_comment=requester):
        return {"access": True, "reason": "Master identity verified", "unlimited": True}
    
    # Others need approved, non-expired access
    if not APPROVAL_QUEUE.exists():
        return {"access": False, "reason": "No access granted"}
    
    queue = json.loads(APPROVAL_QUEUE.read_text())
    for req in queue:
        if req["requester"] == requester and req["status"] == "approved":
            if req["expires"] and datetime.now().timestamp() < req["expires"]:
                return {
                    "access": True, 
                    "reason": f"Approved: {req['benefit_to_master']}",
                    "expires": req["expires"]
                }
    
    return {"access": False, "reason": "Access not granted or expired"}

def log_access(identity: str, action: str, granted: bool):
    """Log all access attempts"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "identity": identity,
        "action": action,
        "granted": granted
    }
    _ensure_private_dir()
    with open(ACCESS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    try:
        ACCESS_LOG.chmod(0o600)
    except OSError:
        pass

if __name__ == "__main__":
    print("Identity Gate Active")
    print(f"Master: {MASTER_IDENTITY['name']}")
    print(f"Devices: {len(MASTER_IDENTITY['devices'])}")
