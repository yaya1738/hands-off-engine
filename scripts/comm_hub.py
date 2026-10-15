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
    "operator": {
        "id": "operator",
        "name": "Yair Siegel",
        "role": "owner",
        "trust_level": 10,
        "approval_authority": True,
        "channels": ["telegram", "webhook", "notification"],
        "info_scope": "full",
        "notify_on": ["trade_alert", "approval_needed", "system_status", "error", "daily_digest", "income_update"],
        "format": "human_readable",
    },
    "claude-code": {
        "id": "claude-code",
        "name": "Claude Code CLI",
        "role": "agent",
        "trust_level": 8,
        "channels": ["webhook", "messages_jsonl", "file"],
        "info_scope": "structured",
        "notify_on": ["task_assignment", "coordination", "system_status", "approval_needed"],
        "format": "json",
    },
    "copilot": {
        "id": "copilot",
        "name": "GitHub Copilot",
        "role": "agent",
        "trust_level": 8,
        "channels": ["webhook", "messages_jsonl"],
        "info_scope": "structured",
        "notify_on": ["task_assignment", "coordination", "system_status"],
        "format": "json",
    },
    "chatgpt": {
        "id": "chatgpt",
        "name": "ChatGPT",
        "role": "agent",
        "trust_level": 7,
        "channels": ["webhook", "messages_jsonl"],
        "info_scope": "structured",
        "notify_on": ["task_assignment", "coordination"],
        "format": "json",
    },
    "anyclaw": {
        "id": "anyclaw",
        "name": "AnyClaw (Codex CLI)",
        "role": "agent",
        "trust_level": 9,
        "channels": ["file", "messages_jsonl"],
        "info_scope": "structured",
        "notify_on": ["task_assignment", "coordination", "system_status"],
        "format": "json",
    },
    "factory": {
        "id": "factory",
        "name": "Factory (ChatGPT)",
        "role": "agent",
        "trust_level": 9,
        "channels": ["file", "messages_jsonl", "github_issue"],
        "info_scope": "structured",
        "notify_on": ["task_result", "continuation_event", "coordination"],
        "format": "json",
    },
    "openclaw": {
        "id": "openclaw",
        "name": "OpenClaw (parallel executor)",
        "role": "agent",
        "trust_level": 8,
        "channels": ["file", "messages_jsonl"],
        "info_scope": "structured",
        "notify_on": ["task_assignment", "coordination", "system_status"],
        "format": "json",
    },
    "grok": {
        "id": "grok",
        "name": "Grok (X.AI)",
        "role": "agent",
        "trust_level": 7,
        "channels": ["file", "messages_jsonl"],
        "info_scope": "structured",
        "notify_on": ["query", "task_assignment"],
        "format": "json",
    },
    "telegram": {
        "id": "telegram",
        "name": "Telegram Bot",
        "role": "channel",
        "trust_level": 10,
        "channels": ["telegram"],
        "info_scope": "human_friendly",
        "notify_on": ["trade_alert", "approval_needed", "system_status", "error"],
        "format": "telegram_markdown",
    },
    "system_internal": {
        "id": "system_internal",
        "name": "Internal System",
        "role": "internal",
        "trust_level": 10,
        "channels": ["file", "messages_jsonl"],
        "info_scope": "full",
        "notify_on": ["*"],
        "format": "json",
    },
}


# ──────────────────────────────────────────────────────────────────────
# Message types and their priority / routing metadata
# ──────────────────────────────────────────────────────────────────────

MESSAGE_TYPES = {
    "trade_alert": {"priority": 9, "requires_ack": True, "retention_hours": 168},
    "approval_needed": {"priority": 10, "requires_ack": True, "retention_hours": 72},
    "system_status": {"priority": 5, "requires_ack": False, "retention_hours": 24},
    "error": {"priority": 8, "requires_ack": True, "retention_hours": 168},
    "daily_digest": {"priority": 6, "requires_ack": False, "retention_hours": 48},
    "income_update": {"priority": 7, "requires_ack": False, "retention_hours": 72},
    "task_assignment": {"priority": 7, "requires_ack": True, "retention_hours": 24},
    "coordination": {"priority": 5, "requires_ack": False, "retention_hours": 12},
    "inbound_from_operator": {"priority": 10, "requires_ack": False, "retention_hours": 168},
    "inbound_from_agent": {"priority": 7, "requires_ack": False, "retention_hours": 48},
    "inbound_from_external": {"priority": 6, "requires_ack": False, "retention_hours": 48},
    "info_response": {"priority": 4, "requires_ack": False, "retention_hours": 24},
    "health_check": {"priority": 3, "requires_ack": False, "retention_hours": 6},
    "heartbeat": {"priority": 1, "requires_ack": False, "retention_hours": 1},
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

    # ── party registry ──

    def _registry_path(self):
        return getattr(self, "registry_file", None) or (self.state_dir / "party_registry.json")

    def _load_parties(self):
        registry = self._registry_path()
        if registry.exists():
            try:
                return json.loads(registry.read_text())
            except Exception:
                pass
        registry.write_text(json.dumps(DEFAULT_PARTIES, indent=2) + "\n")
        return dict(DEFAULT_PARTIES)

    def _save_parties(self):
        self._registry_path().write_text(json.dumps(self.parties, indent=2) + "\n")

    def register_party(self, party_id, name, role, channels, trust_level=5, info_scope="structured",
                       notify_on=None, fmt="json"):
        self.parties[party_id] = {
            "id": party_id, "name": name, "role": role, "trust_level": trust_level,
            "channels": channels, "info_scope": info_scope,
            "notify_on": notify_on or ["system_status"],
            "format": fmt,
        }
        self._save_parties()
        log.info(f"Registered party: {party_id} ({name}, role={role})")

    def get_party(self, party_id):
        return self.parties.get(party_id)

    def list_parties(self):
        return list(self.parties.values())

    # ── outbound: system → party ──

    def send(self, party_id, msg_type, payload, source="system", channel_override=None, urgency="normal"):
        """Send a message to a specific party via their configured channel."""
        party = self.parties.get(party_id)
        if not party:
            log.warning(f"Unknown party: {party_id}")
            return {"status": "error", "error": f"Unknown party: {party_id}"}

        # Check if this party subscribes to this message type
        if "*" not in party.get("notify_on", []) and msg_type not in party.get("notify_on", []):
            log.info(f"Skipping {party_id} — not subscribed to {msg_type}")
            return {"status": "skipped", "reason": f"{party_id} not subscribed to {msg_type}"}

        meta = MESSAGE_TYPES.get(msg_type, {"priority": 5, "requires_ack": False})
        channel = channel_override or party["channels"][0] if party["channels"] else "file"

        msg = {
            "id": str(uuid.uuid4()),
            "from": source,
            "to": party_id,
            "type": msg_type,
            "priority": meta["priority"],
            "requires_ack": meta.get("requires_ack", False),
            "channel": channel,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
            "format": party.get("format", "json"),
            "urgency": urgency,
        }

        # Format for the target channel
        formatted = self._format_for_channel(msg, party)

        # Deliver
        result = self._deliver(channel, formatted, party_id)
        # Log
        self._log_outbound(msg, result)

        # Write to coordination bus exactly once:
        # - messages_jsonl/webhook channels already append during delivery
        # - other channels append the canonical entry here
        if channel not in ("messages_jsonl", "webhook"):
            self._write_to_messages_jsonl(msg)

        # SMTP acceptance and local persistence are separate outcomes. Never
        # report a clean send when the transport accepted the message but the
        # correlation record could not be durably written.
        if channel == "email" and result.get("status") in {"sent", "sent_audit_incomplete"}:
            try:
                self._record_message_correlation(msg, party_id)
            except Exception as exc:
                log.critical(
                    "Email accepted but correlation persistence failed (%s); reply reconciliation required",
                    type(exc).__name__,
                )
                result = {
                    **result,
                    "status": "sent_audit_incomplete",
                    "transport_accepted": True,
                    "correlation_recorded": False,
                    "audit_error": type(exc).__name__,
                }
            else:
                result = {**result, "transport_accepted": True, "correlation_recorded": True}

        # Handle ack tracking
        if meta.get("requires_ack"):
            self.pending_acks[msg["id"]] = {
                "msg": msg,
                "sent_at": msg["timestamp"],
                "status": "pending",
            }
            self._save_pending_acks()

        log.info(f"Sent {msg_type} to {party_id} via {channel}: {result.get('status', 'ok')}")
        # Do not report a guarded email send as successful when policy blocked it.
        overall_status = result.get("status", "sent") if channel == "email" else "sent"
        return {"status": overall_status, "id": msg["id"], "channel": channel, "result": result}

    def broadcast(self, msg_type, payload, source="system"):
        """Broadcast to all parties subscribed to this message type."""
        results = {}
        for party_id, party in self.parties.items():
            if party_id == "system_internal":
                continue
            result = self.send(party_id, msg_type, payload, source=source)
            results[party_id] = result
        return results

    # ── inbound: party → system ──

    def receive(self, sender_id, msg_type, payload, channel="webhook"):
        """Process an inbound message from a party.

        Rejects unregistered sender_ids to prevent bus poisoning.
        """
        if sender_id not in self.parties:
            return {"routed_to": "rejected", "error": f"Unknown sender: {sender_id}"}
        sender = self.parties[sender_id]

        msg = {
            "id": str(uuid.uuid4()),
            "from": sender_id,
            "to": "system_internal",
            "type": msg_type,
            "channel": channel,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
            "sender_trust": sender.get("trust_level", 0),
            "sender_role": sender.get("role", "unknown"),
        }

        # Log inbound
        self._log_inbound(msg)

        # Write to coordination bus
        inbound_type = f"inbound_from_{sender.get('role', 'external')}"
        bus_msg = dict(msg)
        bus_msg["type"] = inbound_type
        self._write_to_messages_jsonl(bus_msg)

        # Route based on message type
        response = self._route_inbound(msg)

        log.info(f"Received {msg_type} from {sender_id} via {channel}: routed={response.get('routed_to', 'none')}")
        return response

    def _route_inbound(self, msg):
        """Route an inbound message to the appropriate handler."""
        msg_type = msg.get("type", "")
        sender_trust = msg.get("sender_trust", 0)

        # Approval responses require explicit authority, not merely a registered identity.
        if msg_type in ("approve", "reject"):
            sender = self.parties.get(msg.get("from"), {})
            if sender.get("role") != "owner" or sender.get("approval_authority") is not True:
                return {"routed_to": "rejected", "error": "Sender lacks explicit approval authority"}
            return self._handle_approval_response(msg)

        # Status queries
        if msg_type in ("status_query", "health_query"):
            return self._handle_status_query(msg)

        # Trade commands from operator
        if msg_type in ("trade_command", "execute_command") and sender_trust >= 8:
            return self._handle_trade_command(msg)

        # Agent task results
        if msg_type == "task_result":
            return self._handle_task_result(msg)

        # Generic inbound — log and acknowledge
        return {"routed_to": "logged", "acknowledged": True}

    # ── human participant reply correlation ──

    def _correlation_path(self):
        return self.state_dir / "message_correlations.json"

    def _record_message_correlation(self, msg, party_id):
        """Record an outbound email reference for later verified reply matching."""
        path = self._correlation_path()
        try:
            records = json.loads(path.read_text()) if path.exists() else {}
        except (OSError, ValueError):
            records = {}
        payload = msg.get("payload", {})
        reference = str(payload.get("correlation_id") or msg.get("id") or "").strip()
        if not reference:
            return
        records[reference] = {
            "message_id": msg.get("id"),
            "party_id": party_id,
            "message_type": msg.get("type"),
            "created_at": msg.get("timestamp"),
            "status": "awaiting_reply",
        }
        path.write_text(json.dumps(records, indent=2) + "\n")

    def receive_human_reply(self, sender_id, verified_sender, correlation_id, body,
                            provider_message_id, channel="email"):
        """Persist a verified, correlated human reply as advisory input only.

        This method deliberately does not route replies through command/approval
        handlers. The adapter must establish sender identity before calling it.
        """
        party = self.parties.get(sender_id)
        if not party or party.get("role") != "human_participant":
            return {"routed_to": "rejected", "error": "Unknown human participant"}
        if not party.get("email_consent", False) or "email" not in party.get("channels", []):
            return {"routed_to": "rejected", "error": "Email participation is not enabled"}
        expected = str(party.get("email", "")).strip().casefold()
        actual = str(verified_sender or "").strip().casefold()
        if not expected or not actual or actual != expected:
            return {"routed_to": "rejected", "error": "Sender identity mismatch"}
        provider_message_id = str(provider_message_id or "").strip()
        reference = str(correlation_id or "").strip()
        if not provider_message_id or not reference:
            return {"routed_to": "rejected", "error": "Missing provider message ID or correlation reference"}

        path = self._correlation_path()
        try:
            records = json.loads(path.read_text()) if path.exists() else {}
        except (OSError, ValueError):
            records = {}
        correlation = records.get(reference)
        if not correlation or correlation.get("party_id") != sender_id:
            return {"routed_to": "rejected", "error": "Unknown or mismatched correlation reference"}

        seen_path = self.state_dir / "processed_email_replies.json"
        try:
            seen = json.loads(seen_path.read_text()) if seen_path.exists() else []
            if not isinstance(seen, list) or any(not isinstance(item, str) for item in seen):
                raise ValueError("processed reply state must be a list of message IDs")
        except (OSError, ValueError, TypeError):
            log.error("Processed email reply state unavailable; refusing inbound reply")
            return {"routed_to": "rejected", "error": "Reply deduplication state unavailable"}
        if provider_message_id in seen:
            return {"routed_to": "duplicate", "provider_message_id": provider_message_id}

        reply = {
            "id": str(uuid.uuid4()),
            "from": sender_id,
            "to": "system_internal",
            "type": "human_reply_advisory",
            "channel": channel,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": reference,
            "in_reply_to_message_id": correlation.get("message_id"),
            "provider_message_id": provider_message_id,
            "payload": {"text": str(body or "")[:12000], "disposition": "advisory_pending_review"},
        }
        self._log_inbound(reply)
        self._write_to_messages_jsonl(reply)
        seen.append(provider_message_id)
        seen_path.write_text(json.dumps(seen[-5000:], indent=2) + "\n")
        try:
            from messaging.human_participant_policy import ContactHistory
            ContactHistory(self.state_dir / "human_contact_history.json").update_status(
                reference, "answered", now=datetime.now(timezone.utc),
            )
        except Exception as exc:
            log.critical("Advisory reply recorded but contact history could not be closed (%s)", type(exc).__name__)
        return {"routed_to": "advisory_input", "correlation_id": reference,
                "requires_review": True, "authority": "none"}

    # ── channel delivery ──

    def _deliver(self, channel, msg, party_id):
        """Deliver a formatted message via the specified channel."""
        try:
            if channel == "telegram":
                return self._deliver_telegram(msg, party_id)
            elif channel == "webhook":
                return self._deliver_webhook(msg, party_id)
            elif channel == "messages_jsonl":
                return self._deliver_jsonl(msg, party_id)
            elif channel == "email":
                return self._deliver_email(msg, party_id)
            elif channel == "notification":
                return self._deliver_notification(msg, party_id)
            elif channel == "file":
                return self._deliver_file(msg, party_id)
            else:
                return {"status": "error", "error": f"Unknown channel: {channel}"}
        except Exception as e:
            log.error(f"Delivery failed on {channel} to {party_id}: {e}")
            return {"status": "error", "error": str(e)}

    def _deliver_telegram(self, msg, party_id):
        """Send via Telegram using termux-notification or the bot."""
        text = msg.get("formatted_text", json.dumps(msg.get("payload", {})))
        # Use termux-notification for immediate alerts
        title = msg.get("payload", {}).get("title", msg.get("type", "system"))
        try:
            subprocess.run(
                ["termux-notification", "-t", str(title)[:50], "-c", str(text)[:200], "--id", str(msg.get("id", ""))[:10]],
                capture_output=True, timeout=5,
            )
            return {"status": "sent", "channel": "telegram_notification"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _deliver_webhook(self, msg, party_id):
        """Write to the coordination messages.jsonl bus."""
        return self._deliver_jsonl(msg, party_id)

    def _deliver_jsonl(self, msg, party_id):
        """Append to messages.jsonl for agent consumption."""
        msgs_file = self.repo_root / "ai" / "coordination" / "messages.jsonl"
        msgs_file.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "from": msg.get("from", "system"),
            "to": party_id,
            "type": msg.get("type", "info"),
            "message": json.dumps(msg.get("payload", {})),
            "timestamp": msg.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "msg_id": msg.get("id"),
            "priority": msg.get("priority", 5),
        }
        try:
            with open(msgs_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
            return {"status": "sent", "channel": "messages_jsonl"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _deliver_email(self, msg, party_id):
        """Send email only when consent, allowlisting, and task-aware policy pass."""
        party = self.parties.get(party_id, {})
        if party.get("role") == "human_participant":
            try:
                from messaging.human_participant_policy import ContactHistory, evaluate_contact_request
                history_store = ContactHistory(self.state_dir / "human_contact_history.json")
                decision = evaluate_contact_request(party, msg.get("payload", {}), history_store.load())
            except Exception as exc:
                log.error("Human email policy unavailable; refusing contact (%s)", type(exc).__name__)
                return {"status": "blocked", "reason": "policy_unavailable"}
            if not decision.get("allowed"):
                return {"status": "blocked", "reason": decision.get("reason", "policy_denied")}
        if not party.get("email_consent", False):
            return {"status": "blocked", "reason": "email consent not recorded"}
        recipient = str(party.get("email", "")).strip().lower()
        allowed = {
            item.strip().lower()
            for item in os.getenv("EMAIL_ALLOWED_RECIPIENTS", "").split(",")
            if item.strip()
        }
        if not recipient or recipient not in allowed:
            return {"status": "blocked", "reason": "recipient missing or not allowlisted"}
        try:
            from messaging.email_smtp import send_email
            payload = msg.get("payload", {})
            subject = str(payload.get("subject") or f"Hands-Off Engine: {msg.get('type', 'update')}")[:180]
            body = msg.get("formatted_text") or json.dumps(payload, indent=2, default=str)
            correlation_id = payload.get("correlation_id") or msg.get("id")
            body = f"{body}\n\nReference: {correlation_id}\nReply with this reference preserved so your response can be linked to the right task."
            result = send_email(recipient=recipient, subject=subject, body=body)
            audit_incomplete = False
            if party.get("role") == "human_participant":
                try:
                    history_store.record(
                        party_id, payload, "awaiting_reply",
                        now=datetime.fromisoformat(msg["timestamp"]),
                    )
                except Exception as exc:
                    audit_incomplete = True
                    log.critical(
                        "Email accepted but contact history could not be persisted (%s); reconciliation required",
                        type(exc).__name__,
                    )
            return {
                "status": "sent_audit_incomplete" if audit_incomplete else "sent",
                "channel": "email",
                "provider": result,
                "transport_accepted": True,
                "contact_history_recorded": not audit_incomplete,
            }
        except (ValueError, OSError, TimeoutError) as e:
            return {"status": "error", "error": str(e)}
        except Exception as e:
            log.error("Email delivery failed for %s: %s", party_id, type(e).__name__)
            return {"status": "error", "error": "email delivery failed"}

    def _deliver_notification(self, msg, party_id):
        """Send a local notification (Android)."""
        title = msg.get("payload", {}).get("title", "System")
        body = msg.get("formatted_text", json.dumps(msg.get("payload", {})))[:200]
        try:
            subprocess.run(
                ["termux-notification", "-t", str(title)[:50], "-c", body, "--id", str(msg.get("id", ""))[:10]],
                capture_output=True, timeout=5,
            )
            return {"status": "sent", "channel": "notification"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _deliver_file(self, msg, party_id):
        """Write to an outbound file for the party to read (checkout-local)."""
        out_dir = getattr(self, "outbound_dir", None) or OUTBOUND_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{party_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        try:
            out_file.write_text(json.dumps(msg, indent=2) + "\n")
            return {"status": "delivered", "channel": "file", "path": str(out_file)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ── formatting ──

    def _format_for_channel(self, msg, party):
        """Format message payload based on target channel and party needs."""
        fmt = party.get("format", "json")
        payload = msg.get("payload", {})

        if fmt == "telegram_markdown":
            msg["formatted_text"] = self._to_telegram_markdown(payload)
        elif fmt == "human_readable":
            msg["formatted_text"] = self._to_human_readable(payload)
        elif fmt == "json":
            msg["formatted_text"] = json.dumps(payload)
        else:
            msg["formatted_text"] = json.dumps(payload)

        return msg

    def _to_telegram_markdown(self, payload):
        """Convert payload to Telegram-friendly markdown."""
        if isinstance(payload, dict):
            lines = []
            for k, v in payload.items():
                if isinstance(v, dict):
                    v = json.dumps(v)
                lines.append(f"*{k}*: {v}")
            return "\n".join(lines)
        return str(payload)

    def _to_human_readable(self, payload):
        """Convert payload to human-readable text."""
        if isinstance(payload, dict):
            parts = []
            for k, v in payload.items():
                if isinstance(v, bool):
                    v = "Yes" if v else "No"
                elif isinstance(v, dict):
                    v = json.dumps(v, indent=2)
                parts.append(f"{k.replace('_', ' ').title()}: {v}")
            return "\n".join(parts)
        return str(payload)

    # ── handlers ──

    def _handle_approval_response(self, msg):
        """Handle approve/reject from a party."""
        cmd_id = msg.get("payload", {}).get("command_id")
        action = msg.get("type")
        if not cmd_id:
            return {"routed_to": "error", "error": "Missing command_id"}
        # Delegate to control API
        try:
            from scripts.control_api import SystemControl
            sc = SystemControl(repo_root=self.repo_root)
            if action == "approve":
                result = sc.approve(cmd_id)
            else:
                result = sc.reject(cmd_id)
            return {"routed_to": "approval_workflow", "result": result}
        except Exception as e:
            return {"routed_to": "error", "error": str(e)}

    def _handle_status_query(self, msg):
        """Return system status to the requesting party."""
        status_file = self.state_dir / "autonomy_status.json"
        brain_file = self.state_dir / "hands_off_brain.json"
        status = {}
        if status_file.exists():
            try:
                status = json.loads(status_file.read_text())
            except Exception:
                pass
        if brain_file.exists():
            try:
                status["brain"] = json.loads(brain_file.read_text())
            except Exception:
                pass
        return {"routed_to": "status_response", "data": status}

    def _handle_trade_command(self, msg):
        """Route a trade command from a trusted party to the approval queue."""
        payload = msg.get("payload", {})
        try:
            from scripts.control_api import SystemControl
            sc = SystemControl(repo_root=self.repo_root)
            cmd_id = sc.execute(
                action=payload.get("action", "trade"),
                params=payload.get("params", {}),
                mode=payload.get("mode", "LIVE"),
                sync=False,
            )
            return {"routed_to": "command_queue", "command_id": cmd_id}
        except Exception as e:
            return {"routed_to": "error", "error": str(e)}

    def _handle_task_result(self, msg):
        """Process a task result from an agent."""
        result_log = self.state_dir / "task_results.jsonl"
        try:
            with open(result_log, "a") as f:
                f.write(json.dumps(msg, default=str) + "\n")
            return {"routed_to": "task_result_log"}
        except Exception as e:
            return {"routed_to": "error", "error": str(e)}

    # ── proactive notifications ──

    def check_and_notify(self):
        """Watch system state and push proactive alerts to relevant parties."""
        notifications = []

        # Check approval queue
        approval_file = self.state_dir / "approval_queue.json"
        if approval_file.exists():
            try:
                q = json.loads(approval_file.read_text())
                pending = q.get("pending", [])
                if pending:
                    for cmd in pending:
                        notifications.append({
                            "type": "approval_needed",
                            "payload": {
                                "title": "Approval Required",
                                "command_id": cmd.get("id"),
                                "action": cmd.get("payload", {}).get("action", "unknown"),
                                "mode": cmd.get("mode", "DRYRUN"),
                                "queued_at": cmd.get("queued_at", "unknown"),
                            },
                        })
            except Exception:
                pass

        # Check governed root status
        status_file = self.state_dir / "governed_root_status.json"
        if status_file.exists():
            try:
                status = json.loads(status_file.read_text())
                if status.get("status") != "running":
                    notifications.append({
                        "type": "error",
                        "payload": {
                            "title": "Governed Root Not Running",
                            "status": status.get("status", "unknown"),
                        },
                    })
            except Exception:
                pass

        # Check for any error results in the last 5 minutes
        results_file = self.state_dir / "results.jsonl"
        if results_file.exists():
            try:
                cutoff = datetime.now(timezone.utc).isoformat()[:19]
                with open(results_file, "r") as f:
                    for line in f:
                        if line.strip():
                            r = json.loads(line)
                            if r.get("status") == "failed":
                                notifications.append({
                                    "type": "error",
                                    "payload": {
                                        "title": "Command Failed",
                                        "command_id": r.get("id"),
                                        "error": r.get("result", {}).get("error", "unknown"),
                                    },
                                })
            except Exception:
                pass

        # Send all notifications
        sent = []
        for n in notifications:
            result = self.send("operator", n["type"], n["payload"], source="comm_hub_proactive")
            sent.append(result)

        return {"notifications_checked": len(notifications), "sent": len(sent)}

    # ── pending acks ──

    def acknowledge(self, msg_id):
        """Mark a message as acknowledged."""
        if msg_id in self.pending_acks:
            self.pending_acks[msg_id]["status"] = "acknowledged"
            self.pending_acks[msg_id]["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
            self._save_pending_acks()
            return {"status": "acknowledged", "id": msg_id}
        return {"status": "not_found", "id": msg_id}

    def get_unacknowledged(self):
        return {k: v for k, v in self.pending_acks.items() if v.get("status") == "pending"}

    def _load_pending_acks(self):
        ack_file = self.state_dir / "pending_acks.json"
        if ack_file.exists():
            try:
                self.pending_acks = json.loads(ack_file.read_text())
            except Exception:
                self.pending_acks = {}

    def _save_pending_acks(self):
        ack_file = self.state_dir / "pending_acks.json"
        ack_file.write_text(json.dumps(self.pending_acks, indent=2, default=str) + "\n")

    # ── logging ──

    def _log_outbound(self, msg, result):
        entry = {"direction": "outbound", "msg": msg, "result": result}
        self._append_log(entry)

    def _log_inbound(self, msg):
        entry = {"direction": "inbound", "msg": msg}
        self._append_log(entry)

    def _append_log(self, entry):
        entry["logged_at"] = datetime.now(timezone.utc).isoformat()
        try:
            log_path = getattr(self, "comm_log", None) or (self.state_dir / "comm_log.jsonl")
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except Exception:
            pass

    def _write_to_messages_jsonl(self, msg):
        """Write to the coordination bus for other agents."""
        msgs_file = self.repo_root / "ai" / "coordination" / "messages.jsonl"
        msgs_file.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "from": msg.get("from", "system"),
            "to": msg.get("to", "all"),
            "type": msg.get("type", "info"),
            "message": json.dumps(msg.get("payload", {})),
            "timestamp": msg.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "msg_id": msg.get("id"),
        }
        try:
            with open(msgs_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass


# ── convenience CLI ──

def cli():
    import argparse
    parser = argparse.ArgumentParser(description="Unified Communication Hub CLI")
    sub = parser.add_subparsers(dest="cmd")

    send_p = sub.add_parser("send", help="Send message to a party")
    send_p.add_argument("party", help="Party ID")
    send_p.add_argument("type", help="Message type")
    send_p.add_argument("message", help="Message text")

    sub.add_parser("parties", help="List registered parties")
    sub.add_parser("pending", help="List unacknowledged messages")
    sub.add_parser("check", help="Run proactive notification check")

    approve_p = sub.add_parser("approve", help="Approve a pending command")
    approve_p.add_argument("command_id", help="Command ID to approve")

    reject_p = sub.add_parser("reject", help="Reject a pending command")
    reject_p.add_argument("command_id", help="Command ID to reject")

    args = parser.parse_args()
    hub = CommHub()

    if args.cmd == "send":
        result = hub.send(args.party, args.type, {"text": args.message})
        print(json.dumps(result, indent=2))
    elif args.cmd == "parties":
        for p in hub.list_parties():
            print(f"  {p['id']:20s} trust={p['trust_level']}  role={p['role']}  channels={p['channels']}")
    elif args.cmd == "pending":
        unacked = hub.get_unacknowledged()
        if unacked:
            for mid, info in unacked.items():
                print(f"  {mid[:8]}... type={info['msg']['type']} to={info['msg']['to']}")
        else:
            print("  No unacknowledged messages")
    elif args.cmd == "check":
        result = hub.check_and_notify()
        print(json.dumps(result, indent=2))
    elif args.cmd == "approve":
        result = hub.receive("operator", "approve", {"command_id": args.command_id}, channel="telegram")
        print(json.dumps(result, indent=2))
    elif args.cmd == "reject":
        result = hub.receive("operator", "reject", {"command_id": args.command_id}, channel="telegram")
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    cli()
