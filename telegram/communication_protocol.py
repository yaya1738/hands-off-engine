#!/usr/bin/env python3
"""Durable, low-interruption communication protocol for autonomous operation."""

from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


_SECRET_PATTERNS = (
    re.compile(r"(?i)(?:token|api[_-]?key|secret|private[_-]?key|password)\s*[:=]\s*\S+"),
    re.compile(r"\b(?:sk|pk)_[A-Za-z0-9_-]{12,}\b"),
)


@dataclass(frozen=True)
class ConversationMessage:
    message_id: str
    direction: str
    kind: str
    priority: str
    text: str
    correlation_id: str | None = None
    requires_response: bool = False
    created_at: float = 0.0
    metadata: dict[str, Any] | None = None

    @classmethod
    def create(cls, *, direction: str, kind: str, text: str, priority: str = "normal",
               correlation_id: str | None = None, requires_response: bool = False,
               metadata: dict[str, Any] | None = None) -> "ConversationMessage":
        if direction not in {"inbound", "outbound"}:
            raise ValueError("invalid direction")
        if kind not in {"progress", "decision", "blocker", "request", "response", "ack"}:
            raise ValueError("invalid message kind")
        if priority not in {"low", "normal", "high", "critical"}:
            raise ValueError("invalid priority")
        if not text.strip():
            raise ValueError("message text is required")
        return cls(uuid.uuid4().hex, direction, kind, priority, text.strip(), correlation_id,
                   requires_response, time.time(), metadata or {})


class ConversationStore:
    """Append-only local journal for durable human/system conversation state."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.path = self.root / "state" / "communication" / "messages.jsonl"

    def append(self, message: ConversationMessage) -> ConversationMessage:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(message), sort_keys=True) + "\n")
        return message

    def read(self) -> list[ConversationMessage]:
        if not self.path.exists():
            return []
        return [ConversationMessage(**json.loads(line)) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def pending_human_requests(self) -> list[ConversationMessage]:
        """Return outbound requests/decisions/blockers awaiting a human response."""
        messages = self.read()
        answered = {
            message.correlation_id for message in messages
            if message.direction == "inbound" and message.kind == "response" and message.correlation_id
        }
        return [message for message in messages if message.direction == "outbound"
                and message.requires_response and message.message_id not in answered]

    def pending_responses(self) -> list[ConversationMessage]:
        """Backward-compatible alias for pending outbound human requests."""
        return self.pending_human_requests()


class ConversationProtocol:
    """Policy-aware interface used by autonomous components and transports."""

    def __init__(self, root: Path):
        self.store = ConversationStore(root)

    def receive(self, text: str, *, correlation_id: str | None = None,
                metadata: dict[str, Any] | None = None,
                kind: str = "request") -> ConversationMessage:
        if kind not in {"request", "response"}:
            raise ValueError("inbound communication must be request or response")
        return self.store.append(ConversationMessage.create(
            direction="inbound", kind=kind, text=text,
            correlation_id=correlation_id, metadata=metadata))

    def emit(self, text: str, *, kind: str = "progress", priority: str = "normal",
             correlation_id: str | None = None, requires_response: bool = False,
             metadata: dict[str, Any] | None = None, deliver: bool = False) -> ConversationMessage:
        safe_text = self._redact(text)
        message = self.store.append(ConversationMessage.create(
            direction="outbound", kind=kind, priority=priority, text=safe_text,
            correlation_id=correlation_id, requires_response=requires_response, metadata=metadata))
        if deliver:
            self.deliver(message)
        return message

    def deliver(self, message: ConversationMessage) -> bool:
        """Deliver through the existing actuator boundary; journaling remains authoritative."""
        try:
            from autonomous.actuators import ActuatorHub
            return ActuatorHub().notify(self.render(message))
        except Exception:
            return False

    @staticmethod
    def _redact(text: str) -> str:
        safe = text
        for pattern in _SECRET_PATTERNS:
            safe = pattern.sub(lambda match: match.group(0).split("=", 1)[0].split(":", 1)[0] + "=[REDACTED]", safe)
        return safe

    def render(self, message: ConversationMessage) -> str:
        prefix = {"progress": "ℹ️", "decision": "🧭", "blocker": "🛑", "request": "📥", "response": "↩️", "ack": "✅"}[message.kind]
        suffix = "\nReply is requested." if message.requires_response else ""
        return f"{prefix} {self._redact(message.text)}{suffix}"
