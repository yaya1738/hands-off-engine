#!/usr/bin/env python3
"""State File Integrity — detects tampering of critical state files.

Adds HMAC-like checksums to command_queue.jsonl and approval_queue.json
to detect unauthorized modifications. This is the defense-in-depth
layer for state file integrity identified in the security audit.
"""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
CHECKSUMS_FILE = STATE / "integrity_checksums.json"

# Files we protect
PROTECTED_FILES = [
    "command_queue.jsonl",
    "approval_queue.json",
    "governed_decisions.json",
]

# Simple shared secret (not a real HMAC key, but enough to detect casual tampering)
# In production, this would be a proper HMAC with a secret key.
SECRET = b"hands-off-engine-integrity-2026"


def file_hash(path: Path) -> str:
    """Compute SHA-256 hash of a file's contents."""
    if not path.exists():
        return "missing"
    data = path.read_bytes()
    return hashlib.sha256(SECRET + data).hexdigest()


def compute_checksums() -> dict:
    """Compute checksums for all protected files."""
    checksums = {}
    for name in PROTECTED_FILES:
        path = STATE / name
        checksums[name] = {
            "hash": file_hash(path),
            "size": path.stat().st_size if path.exists() else 0,
            "exists": path.exists(),
        }
    return checksums


def save_checksums(checksums: dict):
    """Save checksums to disk."""
    STATE.mkdir(parents=True, exist_ok=True)
    CHECKSUMS_FILE.write_text(json.dumps({
        "checksums": checksums,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2) + "\n")


def load_checksums() -> dict:
    """Load previously saved checksums."""
    if not CHECKSUMS_FILE.exists():
        return {}
    try:
        return json.loads(CHECKSUMS_FILE.read_text()).get("checksums", {})
    except Exception:
        return {}


def verify_integrity() -> dict:
    """Verify current state files match saved checksums."""
    current = compute_checksums()
    previous = load_checksums()
    
    result = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "files": {},
        "tampered": [],
        "new_files": [],
        "clean": True,
    }
    
    for name in PROTECTED_FILES:
        curr = current.get(name, {})
        prev = previous.get(name, {})
        
        if not prev:
            # No previous checksum — this is a new file, record baseline
            result["files"][name] = {"status": "baseline", **curr}
            result["new_files"].append(name)
        elif curr["hash"] != prev["hash"]:
            result["files"][name] = {
                "status": "TAMPERED",
                "expected": prev["hash"],
                "actual": curr["hash"],
                "size_change": curr["size"] - prev["size"],
            }
            result["tampered"].append(name)
            result["clean"] = False
        else:
            result["files"][name] = {"status": "ok", **curr}
    
    return result


def record_baseline():
    """Record current state as the trusted baseline."""
    checksums = compute_checksums()
    save_checksums(checksums)
    return checksums


def run():
    """Run one integrity check cycle."""
    result = verify_integrity()
    
    if result["tampered"]:
        print(f"⚠️ TAMPERING DETECTED in: {', '.join(result['tampered'])}")
        for name in result["tampered"]:
            f = result["files"][name]
            print(f"  {name}: expected {f['expected'][:16]}... got {f['actual'][:16]}...")
    elif result["new_files"]:
        print(f"📋 New files recorded as baseline: {', '.join(result['new_files'])}")
        record_baseline()
    else:
        print("✅ All state files intact")
    
    return result


if __name__ == "__main__":
    run()
