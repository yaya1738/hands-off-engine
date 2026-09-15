#!/usr/bin/env python3
"""
Unified Communication Hub

Maximally able bidirectional communication layer for the autonomous system.
Routes messages to/from any party — operators, agents, external APIs — using
the most helpful and prudent information for each party's role and trust level.

Parties:
  - operator: Yair Siegel (full trust, full context)
  - agents: Claude CLI, Copilot, ChatGPT (task-scoped, structured)
  - exchanges: Polymarket, CEX APIs (minimal, safe payloads only)
  - telegram: Telegram bot channel (operator-facing)
  - webhook: HTTP coordination bus (agent-facing)

Usage:
  from scripts.comm_hub import CommHub
  hub = CommHub()
  hub.send("operator", "trade_alert", {"market": "ETH", "action": "buy", "pnl": "+$42"})
  hub.broadcast("system_status", {"health": "ok", "uptime": "3d"})
"""

import json
import os
import sys
import uuid
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [CommHub] %(message)s')
log = logging.getLogger("CommHub")

REPO_ROOT = Path.home() / "hands-off-engine"
STATE_DIR = REPO_ROOT / "state"
MESSAGES_FILE = REPO_ROOT / "ai" / "coordination" / "messages.jsonl"
COMM_LOG = STATE_DIR / "comm_log.jsonl"
INBOUND_DIR = STATE_DIR / "inbound"
OUTBOUND_DIR = STATE_DIR / "outbound"
PARTY_REGISTRY = STATE_DIR / "party_registry.json"


# ──────────────────────────────────────────────────────────────────────
# Party definitions — who can communicate, what channel, what trust level
# ──────────────────────────────────────────────────────────────────────

DEFAULT_PARTIES = {
    "operator": {"id": "operator", "name": "Yair Siegel", "role": "owner", "trust_level": 10, "channels": ["telegram", "webhook", "notification"], "info_scope": "full", "notify_on": ["trade_alert", "approval_needed", "system_status", "error", "daily_digest", "income_update"], "format": "human_readable"},
    "claude-code": {"id": "claude-code", "name": "Claude Code CLI", "role": "agent", "trust_level": 8, "channels": ["webhook", "messages_jsonl", "file"], "info_scope": "structured", "notify_on": ["task_assignment", "coordination", "system_status", "approval_needed"], "format": "json"},
    "copilot": {"id": "copilot", "name": "GitHub Copilot", "role": "agent", "trust_level": 8, "channels": ["webhook", "messages_jsonl"], "info_scope": "structured", "notify_on": ["task_assignment", "coordination", "system_status"], "format": "json"},
    "chatgpt": {"id": "chatgpt", "name": "ChatGPT", "role": "agent", "trust_level": 7, "channels": ["webhook", "messages_jsonl"], "info_scope": "structured", "notify_on": ["task_assignment", "coordination"], "format": "json"},
    "anyclaw": {"id": "anyclaw", "name": "AnyClaw (Codex CLI)", "role": "agent", "trust_level": 9, "channels": ["file", "messages_jsonl"], "info_scope": "structured", "notify_on": ["task_assignment", "coordination", "system_status"], "format": "json"},
    "factory": {"id": "factory", "name": "Factory (ChatGPT)", "role": "agent", "trust_level": 9, "channels": ["file", "messages_jsonl", "github_issue"], "info_scope": "structured", "notify_on": ["task_result", "continuation_event", "coordination"], "format": "json"},
    "openclaw": {"id": "openclaw", "name": "OpenClaw (parallel executor)", "role": "agent", "trust_level": 8, "channels": ["file", "messages_jsonl"], "info_scope": "structured", "notify_on": ["task_assignment", "coordination", "system_status"], "format": "json"},
    "grok": {"id": "grok", "name": "Grok (X.AI)", "role": "agent", "trust_level": 7, "channels": ["file", "messages_jsonl"], "info_scope": "structured", "notify_on": ["query", "task_assignment"], "format": "json"},
    "telegram": {"id": "telegram", "name": "Telegram Bot", "role": "channel", "trust_level": 10, "channels": ["telegram"], "info_scope": "human_friendly", "notify_on": ["trade_alert", "approval_needed", "system_status", "error"], "format": "telegram_markdown"},
    "system_internal": {"id": "system_internal", "name": "Internal System", "role": "internal", "trust_level": 10, "channels": ["file", "messages_jsonl"], "info_scope": "full", "notify_on": ["*"], "format": "json"},
}

MESSAGE_TYPES = {
    "trade_alert": {"priority": 9, "requires_ack": True, "retention_hours": 168}, "approval_needed": {"priority": 10, "requires_ack": True, "retention_hours": 72}, "system_status": {"priority": 5, "requires_ack": False, "retention_hours": 24}, "error": {"priority": 8, "requires_ack": True, "retention_hours": 168}, "daily_digest": {"priority": 6, "requires_ack": False, "retention_hours": 48}, "income_update": {"priority": 7, "requires_ack": False, "retention_hours": 72}, "task_assignment": {"priority": 7, "requires_ack": True, "retention_hours": 24}, "coordination": {"priority": 5, "requires_ack": False, "retention_hours": 12}, "inbound_from_operator": {"priority": 10, "requires_ack": False, "retention_hours": 168}, "inbound_from_agent": {"priority": 7, "requires_ack": False, "retention_hours": 48}, "inbound_from_external": {"priority": 6, "requires_ack": False, "retention_hours": 48}, "info_response": {"priority": 4, "requires_ack": False, "retention_hours": 24}, "health_check": {"priority": 3, "requires_ack": False, "retention_hours": 6}, "heartbeat": {"priority": 1, "requires_ack": False, "retention_hours": 1},
}

class CommHub:
    """Unified bidirectional communication hub for the autonomous system."""
    def __init__(self, repo_root=None):
        self.repo_root = Path(repo_root) if repo_root else REPO_ROOT
        self.state_dir = self.repo_root / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.state_dir / "party_registry.json"
        self.comm_log = self.state_dir / "comm_log.jsonl"
        self.messages_file = self.repo_root / "ai" / "coordination" / "messages.jsonl"
        self.inbound_dir = self.state_dir / "inbound"
        self.outbound_dir = self.state_dir / "outbound"
        self.messages_file.parent.mkdir(parents=True, exist_ok=True)
        self.inbound_dir.mkdir(parents=True, exist_ok=True)
        self.outbound_dir.mkdir(parents=True, exist_ok=True)
        self.parties = self._load_parties()
        self.pending_acks = {}
        self._load_pending_acks()
    def _registry_path(self): return getattr(self, "registry_file", None) or (self.state_dir / "party_registry.json")
    def _load_parties(self):
        registry = self._registry_path()
        if registry.exists():
            try: return json.loads(registry.read_text())
            except Exception: pass
        registry.write_text(json.dumps(DEFAULT_PARTIES, indent=2) + "\n"); return dict(DEFAULT_PARTIES)
    def _save_parties(self): self._registry_path().write_text(json.dumps(self.parties, indent=2) + "\n")
    def register_party(self, party_id, name, role, channels, trust_level=5, info_scope="structured", notify_on=None, fmt="json"):
        self.parties[party_id] = {"id": party_id, "name": name, "role": role, "trust_level": trust_level, "channels": channels, "info_scope": info_scope, "notify_on": notify_on or ["system_status"], "format": fmt}; self._save_parties()
    def get_party(self, party_id): return self.parties.get(party_id)
    def list_parties(self): return list(self.parties.values())
    def send(self, party_id, msg_type, payload, source="system", channel_override=None, urgency="normal"):
        party = self.parties.get(party_id)
        if not party: return {"status": "error", "error": f"Unknown party: {party_id}"}
        if "*" not in party.get("notify_on", []) and msg_type not in party.get("notify_on", []): return {"status": "skipped", "reason": f"{party_id} not subscribed to {msg_type}"}
        meta = MESSAGE_TYPES.get(msg_type, {"priority": 5, "requires_ack": False}); channel = channel_override or party["channels"][0] if party["channels"] else "file"
        msg = {"id": str(uuid.uuid4()), "from": source, "to": party_id, "type": msg_type, "priority": meta["priority"], "requires_ack": meta.get("requires_ack", False), "channel": channel, "timestamp": datetime.now(timezone.utc).isoformat(), "payload": payload, "format": party.get("format", "json"), "urgency": urgency}
        formatted = self._format_for_channel(msg, party); result = self._deliver(channel, formatted, party_id); self._log_outbound(msg, result)
        if channel not in ("messages_jsonl", "webhook"): self._write_to_messages_jsonl(msg)
        if meta.get("requires_ack"):
            self.pending_acks[msg["id"]] = {"msg": msg, "sent_at": msg["timestamp"], "status": "pending"}; self._save_pending_acks()
        return {"status": "sent", "id": msg["id"], "channel": channel, "result": result}
    def broadcast(self, msg_type, payload, source="system"):
        return {pid: self.send(pid, msg_type, payload, source=source) for pid in self.parties if pid != "system_internal"}
    def receive(self, sender_id, msg_type, payload, channel="webhook"):
        if sender_id not in self.parties: return {"routed_to": "rejected", "error": f"Unknown sender: {sender_id}"}
        sender = self.parties[sender_id]; msg = {"id": str(uuid.uuid4()), "from": sender_id, "to": "system_internal", "type": msg_type, "channel": channel, "timestamp": datetime.now(timezone.utc).isoformat(), "payload": payload, "sender_trust": sender.get("trust_level", 0), "sender_role": sender.get("role", "unknown")}
        self._log_inbound(msg); bus_msg = dict(msg); bus_msg["type"] = f"inbound_from_{sender.get('role', 'external')}"; self._write_to_messages_jsonl(bus_msg); return self._route_inbound(msg)
    def _route_inbound(self, msg):
        msg_type = msg.get("type", ""); sender_trust = msg.get("sender_trust", 0)
        if msg_type in ("approve", "reject"): return self._handle_approval_response(msg)
        if msg_type in ("status_query", "health_query"): return self._handle_status_query(msg)
        if msg_type in ("trade_command", "execute_command") and sender_trust >= 8: return self._handle_trade_command(msg)
        if msg_type == "task_result": return self._handle_task_result(msg)
        return {"routed_to": "logged", "acknowledged": True}
    def _deliver(self, channel, msg, party_id):
        try:
            if channel == "telegram": return self._deliver_telegram(msg, party_id)
            if channel == "webhook": return self._deliver_webhook(msg, party_id)
            if channel == "messages_jsonl": return self._deliver_jsonl(msg, party_id)
            if channel == "notification": return self._deliver_notification(msg, party_id)
            if channel == "file": return self._deliver_file(msg, party_id)
            return {"status": "error", "error": f"Unknown channel: {channel}"}
        except Exception as e: return {"status": "error", "error": str(e)}
    def _deliver_telegram(self, msg, party_id):
        text = msg.get("formatted_text", json.dumps(msg.get("payload", {}))); title = msg.get("payload", {}).get("title", msg.get("type", "system"))
        try: subprocess.run(["termux-notification", "-t", str(title)[:50], "-c", str(text)[:200], "--id", str(msg.get("id", ""))[:10]], capture_output=True, timeout=5); return {"status": "sent", "channel": "telegram_notification"}
        except Exception as e: return {"status": "error", "error": str(e)}
    def _deliver_webhook(self, msg, party_id): return self._deliver_jsonl(msg, party_id)
    def _deliver_jsonl(self, msg, party_id):
        msgs_file = self.repo_root / "ai" / "coordination" / "messages.jsonl"; msgs_file.parent.mkdir(parents=True, exist_ok=True)
        entry = {"from": msg.get("from", "system"), "to": party_id, "type": msg.get("type", "info"), "message": json.dumps(msg.get("payload", {})), "timestamp": msg.get("timestamp", datetime.now(timezone.utc).isoformat()), "msg_id": msg.get("id"), "priority": msg.get("priority", 5)}
        try:
            with open(msgs_file, "a") as f: f.write(json.dumps(entry) + "\n")
            return {"status": "sent", "channel": "messages_jsonl"}
        except Exception as e: return {"status": "error", "error": str(e)}
    def _deliver_notification(self, msg, party_id):
        title = msg.get("payload", {}).get("title", "System"); body = msg.get("formatted_text", json.dumps(msg.get("payload", {})))[:200]
        try: subprocess.run(["termux-notification", "-t", str(title)[:50], "-c", body, "--id", str(msg.get("id", ""))[:10]], capture_output=True, timeout=5); return {"status": "sent", "channel": "notification"}
        except Exception as e: return {"status": "error", "error": str(e)}
    def _deliver_file(self, msg, party_id):
        out_file = self.outbound_dir / f"{party_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        try: out_file.write_text(json.dumps(msg, indent=2) + "\n"); return {"status": "sent", "channel": "file", "path": str(out_file)}
        except Exception as e: return {"status": "error", "error": str(e)}
    def _format_for_channel(self, msg, party):
        fmt = party.get("format", "json"); payload = msg.get("payload", {})
        if fmt == "telegram_markdown": msg["formatted_text"] = self._to_telegram_markdown(payload)
        elif fmt == "human_readable": msg["formatted_text"] = self._to_human_readable(payload)
        else: msg["formatted_text"] = json.dumps(payload)
        return msg
    def _to_telegram_markdown(self, payload):
        if isinstance(payload, dict): return "\n".join(f"*{k}*: {json.dumps(v) if isinstance(v, dict) else v}" for k, v in payload.items())
        return str(payload)
    def _to_human_readable(self, payload):
        if isinstance(payload, dict):
            parts = []
            for k, v in payload.items():
                if isinstance(v, bool): v = "Yes" if v else "No"
                elif isinstance(v, dict): v = json.dumps(v, indent=2)
                parts.append(f"{k.replace('_', ' ').title()}: {v}")
            return "\n".join(parts)
        return str(payload)
    def _handle_approval_response(self, msg):
        cmd_id = msg.get("payload", {}).get("command_id"); action = msg.get("type")
        if not cmd_id: return {"routed_to": "error", "error": "Missing command_id"}
        try:
            from scripts.control_api import SystemControl
            sc = SystemControl(repo_root=self.repo_root); result = sc.approve(cmd_id) if action == "approve" else sc.reject(cmd_id); return {"routed_to": "approval_workflow", "result": result}
        except Exception as e: return {"routed_to": "error", "error": str(e)}
    def _handle_status_query(self, msg):
        status = {}
        for name in ("autonomy_status.json", "hands_off_brain.json"):
            p = self.state_dir / name
            if p.exists():
                try: status["brain" if name.startswith("hands") else "status"] = json.loads(p.read_text())
                except Exception: pass
        return {"routed_to": "status_response", "data": status}
    def _handle_trade_command(self, msg):
        payload = msg.get("payload", {})
        try:
            from scripts.control_api import SystemControl
            sc = SystemControl(repo_root=self.repo_root); cmd_id = sc.execute(action=payload.get("action", "trade"), params=payload.get("params", {}), mode=payload.get("mode", "LIVE"), sync=False); return {"routed_to": "command_queue", "command_id": cmd_id}
        except Exception as e: return {"routed_to": "error", "error": str(e)}
    def _handle_task_result(self, msg):
        try:
            with open(self.state_dir / "task_results.jsonl", "a") as f: f.write(json.dumps(msg, default=str) + "\n")
            return {"routed_to": "task_result_log"}
        except Exception as e: return {"routed_to": "error", "error": str(e)}
    def check_and_notify(self):
        notifications = []
        approval_file = self.state_dir / "approval_queue.json"
        if approval_file.exists():
            try:
                for cmd in json.loads(approval_file.read_text()).get("pending", []): notifications.append({"type": "approval_needed", "payload": {"title": "Approval Required", "command_id": cmd.get("id"), "action": cmd.get("payload", {}).get("action", "unknown"), "mode": cmd.get("mode", "DRYRUN"), "queued_at": cmd.get("queued_at", "unknown")}})
            except Exception: pass
        status_file = self.state_dir / "governed_root_status.json"
        if status_file.exists():
            try:
                status = json.loads(status_file.read_text())
                if status.get("status") != "running": notifications.append({"type": "error", "payload": {"title": "Governed Root Not Running", "status": status.get("status", "unknown")}})
            except Exception: pass
        sent = [self.send("operator", n["type"], n["payload"], source="comm_hub_proactive") for n in notifications]
        return {"notifications_checked": len(notifications), "sent": len(sent)}
    def acknowledge(self, msg_id):
        if msg_id in self.pending_acks:
            self.pending_acks[msg_id]["status"] = "acknowledged"; self.pending_acks[msg_id]["acknowledged_at"] = datetime.now(timezone.utc).isoformat(); self._save_pending_acks(); return {"status": "acknowledged", "id": msg_id}
        return {"status": "not_found", "id": msg_id}
    def get_unacknowledged(self): return {k: v for k, v in self.pending_acks.items() if v.get("status") == "pending"}
    def _load_pending_acks(self):
        p = self.state_dir / "pending_acks.json"
        if p.exists():
            try: self.pending_acks = json.loads(p.read_text())
            except Exception: self.pending_acks = {}
    def _save_pending_acks(self): (self.state_dir / "pending_acks.json").write_text(json.dumps(self.pending_acks, indent=2, default=str) + "\n")
    def _log_outbound(self, msg, result): self._append_log({"direction": "outbound", "msg": msg, "result": result})
    def _log_inbound(self, msg): self._append_log({"direction": "inbound", "msg": msg})
    def _append_log(self, entry):
        entry["logged_at"] = datetime.now(timezone.utc).isoformat()
        try:
            p = self.comm_log; p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "a") as f: f.write(json.dumps(entry, default=str) + "\n")
        except Exception: pass
    def _write_to_messages_jsonl(self, msg):
        msgs_file = self.repo_root / "ai" / "coordination" / "messages.jsonl"; msgs_file.parent.mkdir(parents=True, exist_ok=True)
        entry = {"from": msg.get("from", "system"), "to": msg.get("to", "all"), "type": msg.get("type", "info"), "message": json.dumps(msg.get("payload", {})), "timestamp": msg.get("timestamp", datetime.now(timezone.utc).isoformat()), "msg_id": msg.get("id")}
        try:
            with open(msgs_file, "a") as f: f.write(json.dumps(entry) + "\n")
        except Exception: pass


def cli():
    import argparse
    parser = argparse.ArgumentParser(description="Unified Communication Hub CLI"); sub = parser.add_subparsers(dest="cmd")
    send_p = sub.add_parser("send", help="Send message to a party"); send_p.add_argument("party"); send_p.add_argument("type"); send_p.add_argument("message")
    sub.add_parser("parties"); sub.add_parser("pending"); sub.add_parser("check")
    approve_p = sub.add_parser("approve"); approve_p.add_argument("command_id")
    reject_p = sub.add_parser("reject"); reject_p.add_argument("command_id")
    args = parser.parse_args(); hub = CommHub()
    if args.cmd == "send": print(json.dumps(hub.send(args.party, args.type, {"text": args.message}), indent=2))
    elif args.cmd == "parties":
        for p in hub.list_parties(): print(f"  {p['id']:20s} trust={p['trust_level']}  role={p['role']}  channels={p['channels']}")
    elif args.cmd == "pending":
        for mid, info in hub.get_unacknowledged().items(): print(f"  {mid[:8]}... type={info['msg']['type']} to={info['msg']['to']}")
    elif args.cmd == "check": print(json.dumps(hub.check_and_notify(), indent=2))
    elif args.cmd in ("approve", "reject"): print(json.dumps(hub.receive("operator", args.cmd, {"command_id": args.command_id}, channel="telegram"), indent=2))
    else: parser.print_help()

if __name__ == "__main__": cli()
