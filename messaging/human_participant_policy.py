"""Task-aware, fail-closed contact policy for human participants.

This module is intentionally transport-independent. A caller must evaluate the
request before calling CommHub.send; the policy never sends messages itself.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ELIGIBLE_REASON_CODES = frozenset({
    "human_context_gap",
    "material_ambiguity",
    "external_blocker",
    "stakeholder_validation",
    "requested_update",
})
REQUIRED_FIELDS = ("task_id", "correlation_id", "reason_code", "question", "why_it_matters")
DEFAULT_COOLDOWN_HOURS = 24
DEFAULT_DAILY_CAP = 3


def evaluate_contact_request(participant, payload, history, *, now=None,
                             cooldown_hours=DEFAULT_COOLDOWN_HOURS,
                             daily_cap=DEFAULT_DAILY_CAP):
    """Return {allowed, reason}; never infer missing context or consent."""
    now = now or datetime.now(timezone.utc)
    if participant.get("role") != "human_participant":
        return {"allowed": False, "reason": "not_a_human_participant"}
    if participant.get("email_consent") is not True:
        return {"allowed": False, "reason": "consent_not_recorded"}
    if "email" not in participant.get("channels", []):
        return {"allowed": False, "reason": "email_channel_not_enabled"}
    if not isinstance(payload, dict):
        return {"allowed": False, "reason": "payload_must_be_object"}
    missing = [key for key in REQUIRED_FIELDS if not str(payload.get(key, "")).strip()]
    if missing:
        return {"allowed": False, "reason": "missing_context:" + ",".join(missing)}
    if payload.get("reason_code") not in ELIGIBLE_REASON_CODES:
        return {"allowed": False, "reason": "ineligible_reason_code"}
    if not str(payload.get("context", "")).strip():
        return {"allowed": False, "reason": "missing_context:context"}

    participant_id = str(participant.get("id", "")).strip()
    correlation_id = str(payload["correlation_id"]).strip()
    task_id = str(payload["task_id"]).strip()
    entries = [e for e in history if e.get("participant_id") == participant_id]

    for entry in entries:
        if (entry.get("correlation_id") == correlation_id
                and entry.get("status") in {"sent", "awaiting_reply"}):
            return {"allowed": False, "reason": "duplicate_open_question"}

    today = now.date()
    sent_today = 0
    recent_contact = False
    cutoff = now - timedelta(hours=max(0, cooldown_hours))
    for entry in entries:
        try:
            sent_at = datetime.fromisoformat(str(entry.get("timestamp", "")).replace("Z", "+00:00"))
            if sent_at.tzinfo is None:
                sent_at = sent_at.replace(tzinfo=timezone.utc)
            if sent_at.date() == today and entry.get("status") in {"sent", "awaiting_reply", "answered"}:
                sent_today += 1
            if sent_at >= cutoff and entry.get("status") in {"sent", "awaiting_reply", "answered"}:
                recent_contact = True
        except (TypeError, ValueError):
            # Malformed history is not trusted as evidence of a recent contact.
            continue

    if sent_today >= max(1, int(daily_cap)):
        return {"allowed": False, "reason": "daily_contact_cap"}
    if recent_contact:
        return {"allowed": False, "reason": "participant_cooldown"}
    return {"allowed": True, "reason": "eligible", "task_id": task_id,
            "correlation_id": correlation_id}


class ContactHistory:
    """Small durable JSON history; corrupt state fails closed for new contacts."""
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text())
            if not isinstance(data, list):
                raise ValueError("history must be a list")
            return data
        except (OSError, ValueError, TypeError) as exc:
            raise RuntimeError("contact history unavailable; refusing contact") from exc

    def record(self, participant_id, payload, status, *, now=None):
        if status not in {"sent", "awaiting_reply", "answered", "expired", "failed"}:
            raise ValueError("invalid contact status")
        entries = self.load()
        entries.append({
            "participant_id": str(participant_id),
            "task_id": str(payload.get("task_id", "")),
            "correlation_id": str(payload.get("correlation_id", "")),
            "reason_code": str(payload.get("reason_code", "")),
            "status": status,
            "timestamp": (now or datetime.now(timezone.utc)).isoformat(),
        })
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(json.dumps(entries[-5000:], indent=2) + "\n")
        temp.replace(self.path)


    def update_status(self, correlation_id, status, *, now=None):
        if status not in {"sent", "awaiting_reply", "answered", "expired", "failed"}:
            raise ValueError("invalid contact status")
        entries = self.load()
        matches = [entry for entry in entries if entry.get("correlation_id") == str(correlation_id)]
        if not matches:
            return False
        for entry in matches:
            entry["status"] = status
            entry["updated_at"] = (now or datetime.now(timezone.utc)).isoformat()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(json.dumps(entries[-5000:], indent=2) + "\n")
        temp.replace(self.path)
        return True
