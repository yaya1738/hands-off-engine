"""Canonical binding for the separate LIVE command approval workflow."""
import hashlib
import json

# Fields that define what the operator approved. Queue lifecycle metadata is
# intentionally excluded; the approval timestamp is checked separately.
APPROVED_COMMAND_FIELDS = (
    "id", "source", "action", "target", "payload", "mode", "timestamp",
    "priority", "sync", "timeout_seconds", "queued_at",
)


def command_fingerprint(command):
    """Return a deterministic digest of the security-relevant command fields."""
    snapshot = {key: command.get(key) for key in APPROVED_COMMAND_FIELDS}
    encoded = json.dumps(
        snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
