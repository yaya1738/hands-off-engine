#!/usr/bin/env python3
"""
Factory-side Request Intake — admission gate for inbound task_request messages.

Consumes task_request entries from the canonical coordination bus
(ai/coordination/messages.jsonl), including governed CommHub envelopes,
validates sender and request contract, deduplicates by msg_id, and persists
admission decisions durably.

Design constraints:
- No auto-dispatch: admitted requests are queued, not forwarded as assignments
- Sender validation against CommHub party registry
- Request type validation against bounded allowed set
- Correlation/dedup by msg_id with durable state across restarts
- Exactly-once admission: same msg_id never admitted twice
- Fail-closed: unknown senders, bad types, and malformed messages rejected

Admitted requests sit in state/request_intake_state.json for Factory
(external party) to read and decide on next action.
"""

import json
import sys
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [RequestIntake] %(message)s')
log = logging.getLogger("RequestIntake")

REPO_ROOT = Path(__file__).resolve().parent.parent
MESSAGES_FILE = REPO_ROOT / "ai" / "coordination" / "messages.jsonl"
INTAKE_STATE = REPO_ROOT / "state" / "request_intake_state.json"
PARTY_REGISTRY = REPO_ROOT / "state" / "party_registry.json"

ALLOWED_REQUEST_TYPES = frozenset({"work_request", "question", "status_probe"})
ALLOWED_SENDERS = frozenset({"anyclaw", "openclaw"})
MAX_MESSAGE_LENGTH = 2048


def _load_party_registry(path: Optional[Path] = None) -> dict:
    registry_path = Path(path) if path else PARTY_REGISTRY
    if registry_path.exists():
        try:
            return json.loads(registry_path.read_text())
        except Exception:
            pass
    return {}


def _load_state(path: Optional[Path] = None) -> dict:
    state_path = Path(path) if path else INTAKE_STATE
    if state_path.exists():
        try:
            return json.loads(state_path.read_text())
        except Exception:
            pass
    return {"admitted_ids": [], "rejected_ids": [], "admissions": [], "rejections": []}


def _save_state(state: dict, path: Optional[Path] = None):
    state_path = Path(path) if path else INTAKE_STATE
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2) + "\n")


def _fingerprint(msg: dict) -> str:
    msg_id = msg.get("msg_id", "")
    return hashlib.sha256(msg_id.encode("utf-8")).hexdigest()


class RequestIntake:
    """Factory-side admission gate for inbound task_request messages."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = Path(repo_root) if repo_root else REPO_ROOT
        self.messages_file = self.repo_root / "ai" / "coordination" / "messages.jsonl"
        self.state_file = self.repo_root / "state" / "request_intake_state.json"
        self.party_registry = self.repo_root / "state" / "party_registry.json"
        self.state = _load_state(self.state_file)
        self.admitted_ids = set(self.state.get("admitted_ids", []))
        self.rejected_ids = set(self.state.get("rejected_ids", []))
        self.parties = _load_party_registry(self.party_registry)

    def _persist(self):
        self.state["admitted_ids"] = sorted(self.admitted_ids)[-2000:]
        self.state["rejected_ids"] = sorted(self.rejected_ids)[-2000:]
        self.state["admissions"] = self.state.get("admissions", [])[-200:]
        self.state["rejections"] = self.state.get("rejections", [])[-200:]
        _save_state(self.state, self.state_file)

    def _validate_sender(self, msg: dict) -> Tuple[bool, str]:
        sender = msg.get("from", "")
        if not sender:
            return False, "missing_sender"
        if sender not in self.parties:
            return False, f"unknown_sender:{sender}"
        if sender not in ALLOWED_SENDERS:
            return False, f"sender_not_authorized:{sender}"
        party = self.parties[sender]
        if party.get("trust_level", 0) < 7:
            return False, f"insufficient_trust:{sender}"
        return True, "ok"

    def _validate_request_type(self, msg: dict) -> Tuple[bool, str]:
        context = msg.get("context") or {}
        request_type = context.get("request_type", "")
        if not request_type:
            return False, "missing_request_type"
        if request_type not in ALLOWED_REQUEST_TYPES:
            return False, f"invalid_request_type:{request_type}"
        return True, "ok"

    def _validate_message(self, msg: dict) -> Tuple[bool, str]:
        if not msg.get("msg_id"):
            return False, "missing_msg_id"
        if msg.get("type") != "task_request":
            return False, f"wrong_type:{msg.get('type', 'none')}"
        message_text = msg.get("message", "")
        if not message_text:
            return False, "empty_message"
        if len(message_text) > MAX_MESSAGE_LENGTH:
            return False, f"message_too_long:{len(message_text)}"
        return True, "ok"

    def _validate_contract(self, msg: dict) -> Tuple[bool, str]:
        ok, reason = self._validate_message(msg)
        if not ok:
            return False, reason
        ok, reason = self._validate_sender(msg)
        if not ok:
            return False, reason
        return self._validate_request_type(msg)

    def _read_task_requests(self) -> List[dict]:
        """Read canonical task_request records, including CommHub envelopes."""
        if not self.messages_file.exists():
            return []
        requests = []
        try:
            with open(self.messages_file, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        msg = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if msg.get("type") == "task_request":
                        requests.append(msg)
                        continue
                    if msg.get("type") != "inbound_from_agent":
                        continue
                    payload = msg.get("payload")
                    if not isinstance(payload, dict) or payload.get("type") != "task_request":
                        continue
                    request = dict(payload)
                    request["from"] = msg.get("from", request.get("from", ""))
                    request["to"] = msg.get("to", request.get("to", "factory"))
                    request["timestamp"] = msg.get("timestamp", request.get("timestamp"))
                    request["channel"] = msg.get("channel", request.get("channel"))
                    requests.append(request)
        except Exception:
            pass
        return requests

    def admit_once(self) -> List[dict]:
        requests = self._read_task_requests()
        decisions = []
        for msg in requests:
            msg_id = msg.get("msg_id", "")
            fp = _fingerprint(msg)
            if msg_id in self.admitted_ids or msg_id in self.rejected_ids:
                continue
            ok, reason = self._validate_contract(msg)
            decision = {
                "msg_id": msg_id,
                "fingerprint": fp,
                "from": msg.get("from", ""),
                "request_type": (msg.get("context") or {}).get("request_type", ""),
                "message_preview": msg.get("message", "")[:120],
                "admitted": ok,
                "reason": reason,
                "decided_at": datetime.now(timezone.utc).isoformat(),
            }
            if ok:
                self.admitted_ids.add(msg_id)
                self.state.setdefault("admissions", []).append(decision)
                log.info(f"Admitted: {msg_id} from={msg['from']} type={decision['request_type']}")
            else:
                self.rejected_ids.add(msg_id)
                self.state.setdefault("rejections", []).append(decision)
                log.info(f"Rejected: {msg_id} from={msg.get('from','?')} reason={reason}")
            decisions.append(decision)
        if decisions:
            self._persist()
        return decisions

    def status(self) -> dict:
        return {
            "admitted_count": len(self.admitted_ids),
            "rejected_count": len(self.rejected_ids),
            "pending_requests": len([
                r for r in self._read_task_requests()
                if r.get("msg_id") not in self.admitted_ids
                and r.get("msg_id") not in self.rejected_ids
            ]),
            "last_admission": self.state.get("admissions", [])[-1] if self.state.get("admissions") else None,
        }

    def get_admitted(self) -> List[dict]:
        return self.state.get("admissions", [])

    def get_rejections(self) -> List[dict]:
        return self.state.get("rejections", [])


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Factory-side request intake (admission gate)")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("process", help="Process pending task_request messages")
    sub.add_parser("status", help="Show admission status")
    sub.add_parser("admitted", help="List admitted requests")
    sub.add_parser("rejected", help="List rejected requests")
    args = parser.parse_args()
    intake = RequestIntake()
    if args.cmd == "process":
        decisions = intake.admit_once()
        print(f"Processed {len(decisions)} task_requests")
        for d in decisions:
            status = "ADMITTED" if d["admitted"] else f"REJECTED({d['reason']})"
            print(f"  {d['msg_id'][:20]}... from={d['from']} type={d['request_type']} -> {status}")
    elif args.cmd == "status":
        print(json.dumps(intake.status(), indent=2))
    elif args.cmd == "admitted":
        admitted = intake.get_admitted()
        print(f"{len(admitted)} admitted requests")
        for a in admitted:
            print(f"  {a['msg_id'][:20]}... from={a['from']} type={a['request_type']}")
    elif args.cmd == "rejected":
        rejected = intake.get_rejections()
        print(f"{len(rejected)} rejected requests")
        for r in rejected:
            print(f"  {r['msg_id'][:20]}... from={r['from']} reason={r['reason']}")
    else:
        parser.print_help()
