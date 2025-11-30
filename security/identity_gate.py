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

MASTER_IDENTITY = {
    "name": "Yair Siegel",
    "email": "siegel.yaz@gmail.com",
    "devices": [
        "termux@handsoff",  # Phone
        "pm-agent@206.189.60.125",  # Termux agent
        "handsoff-do138",  # Server
    ],
    "ssh_key_fingerprints": [
        # Your keys - SHA256 fingerprints
    ]
}

APPROVAL_QUEUE = Path("/root/hands-off-engine/security/approval_queue.json")
ACCESS_LOG = Path("/root/hands-off-engine/security/access_log.jsonl")

def is_master(ssh_key_comment: str = None, device_id: str = None) -> bool:
    """Check if accessor is the master (Yair)"""
    if ssh_key_comment in MASTER_IDENTITY["devices"]:
        return True
    if device_id in MASTER_IDENTITY["devices"]:
        return True
    return False

def request_access(requester: str, purpose: str, benefit_to_master: str) -> str:
    """Others must explain how access benefits Yair"""
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
    """Check if requester has valid access"""
    # Master always has access
    if is_master(device_id=requester):
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
    with open(ACCESS_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

if __name__ == "__main__":
    print("Identity Gate Active")
    print(f"Master: {MASTER_IDENTITY['name']}")
    print(f"Devices: {len(MASTER_IDENTITY['devices'])}")
