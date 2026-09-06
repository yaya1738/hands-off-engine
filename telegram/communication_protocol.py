#!/usr/bin/env python3
"""Durable, low-interruption communication protocol for autonomous operation.

The system should run without routine human intervention while retaining a
reliable channel for decisions, blockers, progress, and responses. This module
is deliberately transport-neutral: Telegram (or another transport) is only a
messenger; authority and execution remain elsewhere.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ConversationMessage:
    message_id: str
    direction: str  # inbound | outbound
    kind: str  # progress | decision | blocker | request | response | ack
    priority: str  # low | normal | high | critical
    text: str
    correlation_id: str | None = None
    requires_response: bool = False
    created_at: float = 0.0
    metadata: dict[str, Any] | None = None

    @classmethod
    def create(
        cls,
        *,
        direction: str,
        kind: str,
        text: str,
        priority: str = "normal",
        correlation_id: str | None = None,
        requires_response: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> "ConversationMessage":
        if direction not in {"inbound", "outbound"}:
            raise ValueError("invalid direction")
        if kind not in {"progress", "decision", "blocker", "request", "response", "ack"}:
            raise ValueError("invalid message kind")
        if priority not in {"low", "normal", "high", "critical"}:
            raise ValueError("invalid priority")
        if not text.strip():
            raise ValueError("message text is required")
        return cls(
            message_id=uuid.uuid4().hex,
            direction=direction,
            kind=kind,
            priority=priority,
            text=text.strip(),
            correlation_id=correlation_id,
            requires_response=requires_response,
            created_at=time.time(),
            metadata=metadata or {},
        )


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
        messages: list[ConversationMessage] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            messages.append(ConversationMessage(**json.loads(line)))
        return messages

    def pending_responses(self) -> list[ConversationMessage]:
        """Return unanswered inbound messages requiring a human response."""
        messages = self.read()
        answered = {
            message.correlation_id
            for message in messages
            if message.direction == "outbound" and message.correlation_id
        }
        return [
            message
            for message in messages
            if message.direction == "inbound"
            and message.requires_response
            and message.message_id not in answered
        ]


class ConversationProtocol:
    """Policy-aware interface used by autonomous components and transports."""

    def __init__(self, root: Path):
        self.store = ConversationStore(root)

    def receive(self, text: str, *, correlation_id: str | None = None, metadata: dict[str, Any] | None = None) -> ConversationMessage:
        return self.store.append(
            ConversationMessage.create(
                direction="inbound",
                kind="request",
                text=text,
                correlation_id=correlation_id,
                metadata=metadata,
            )
        )

    def emit(
        self,
        text: str,
        *,
        kind: str = "progress",
        priority: str = "normal",
        correlation_id: str | None = None,
        requires_response: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationMessage:
        return self.store.append(
            ConversationMessage.create(
                direction="outbound",
                kind=kind,
                priority=priority,
                text=text,
                correlation_id=correlation_id,
                requires_response=requires_response,
                metadata=metadata,
            )
        )

    def render(self, message: ConversationMessage) -> str:
        """Produce concise transport text; never expose credentials or internals."""
        prefix = {
            "progress": "ℹ️",
            "decision": "🧭",
            "blocker": "🛑",
            "request": "📥",
            "response": "↩️",
            "ack": "✅",
        }[message.kind]
        suffix = "\nReply is requested." if message.requires_response else ""
        return f"{prefix} {message.text}{suffix}"
