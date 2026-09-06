"""Human-to-autonomy bridge: durable receipt plus bounded task handoff."""

from __future__ import annotations

import re
from pathlib import Path

from telegram.communication_protocol import ConversationProtocol

_RESPONSE_RE = re.compile(r"^response:(?P<id>[a-f0-9]{32})\s+(?P<text>.+)$", re.IGNORECASE | re.DOTALL)


class HumanLoop:
    """Turn authenticated human messages into durable autonomous requests/responses."""

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)
        self.protocol = ConversationProtocol(self.repo_root)

    def receive(self, text: str, *, chat_id: str, username: str = "unknown") -> str:
        text = text.strip()
        match = _RESPONSE_RE.match(text)
        if match:
            return self._receive_response(
                match.group("id"), match.group("text"), chat_id=chat_id, username=username
            )
        return self._receive_request(text, chat_id=chat_id, username=username)

    def _receive_response(self, correlation_id: str, text: str, *, chat_id: str, username: str) -> str:
        pending = {
            message.message_id: message
            for message in self.protocol.store.pending_human_requests()
        }
        if correlation_id not in pending:
            blocker = self.protocol.emit(
                "I could not match that response to a pending decision or blocker. Please use the exact response reference from the request.",
                kind="blocker", priority="high", requires_response=False,
            )
            return self.protocol.render(blocker)

        response = self.protocol.receive(
            text, kind="response", correlation_id=correlation_id,
            metadata={"transport": "telegram", "chat_id": str(chat_id), "username": username},
        )
        try:
            from scripts.autonomous_task_queue import AutonomousTaskQueue
            task_id = AutonomousTaskQueue(self.repo_root).add_task(
                title=f"Continue response {correlation_id[:8]}",
                description=(
                    "Continue the autonomous task associated with the human response. "
                    "Re-evaluate the originating decision/blocker, apply the response as input "
                    "only within existing authority and safety boundaries, then test, verify, and continue.\n\n"
                    f"Correlation: {correlation_id}\nHuman response: {text}"
                ),
                priority="high", source="telegram_response",
                metadata={"communication_message_id": response.message_id, "correlation_id": correlation_id, "chat_id": str(chat_id)},
            )
        except Exception as exc:
            blocker = self.protocol.emit(
                f"I recorded your response but could not enqueue continuation: {type(exc).__name__}.",
                kind="blocker", priority="high", correlation_id=correlation_id,
            )
            return self.protocol.render(blocker)

        ack = self.protocol.emit(
            f"Response received and linked to the waiting task ({task_id[:8]}). I’ll continue autonomously within existing authority and safety controls.",
            kind="ack", correlation_id=correlation_id,
        )
        return self.protocol.render(ack)

    def _receive_request(self, text: str, *, chat_id: str, username: str) -> str:
        message = self.protocol.receive(
            text, metadata={"transport": "telegram", "chat_id": str(chat_id), "username": username}
        )
        try:
            from scripts.autonomous_task_queue import AutonomousTaskQueue
            task_id = AutonomousTaskQueue(self.repo_root).add_task(
                title=text[:80],
                description=(
                    "Human request received through the authenticated communication loop.\n\n"
                    f"Request: {text}\n\n"
                    "Operate autonomously: assess, plan, implement bounded changes, test, verify, "
                    "and communicate material progress/blockers back through the communication loop."
                ),
                priority="high", source="telegram_user",
                metadata={"communication_message_id": message.message_id, "chat_id": str(chat_id)},
            )
        except Exception as exc:
            blocker = self.protocol.emit(
                f"I received your request but could not enqueue it: {type(exc).__name__}.",
                kind="blocker", priority="high", correlation_id=message.message_id,
            )
            return self.protocol.render(blocker)

        ack = self.protocol.emit(
            f"Request accepted for autonomous processing (task {task_id[:8]}). I’ll continue without routine check-ins and contact you when a decision, material blocker, or meaningful result needs you.",
            kind="ack", correlation_id=message.message_id,
        )
        return self.protocol.render(ack)
