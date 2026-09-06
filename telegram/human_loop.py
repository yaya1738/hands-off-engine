"""Human-to-autonomy bridge: durable receipt plus bounded task handoff."""

from __future__ import annotations

from pathlib import Path

from telegram.communication_protocol import ConversationProtocol


class HumanLoop:
    """Turn authenticated human messages into durable autonomous requests."""

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)
        self.protocol = ConversationProtocol(self.repo_root)

    def receive(self, text: str, *, chat_id: str, username: str = "unknown") -> str:
        message = self.protocol.receive(
            text,
            metadata={"transport": "telegram", "chat_id": str(chat_id), "username": username},
        )
        try:
            from scripts.autonomous_task_queue import AutonomousTaskQueue

            queue = AutonomousTaskQueue(self.repo_root)
            task_id = queue.add_task(
                title=text.strip()[:80],
                description=(
                    "Human request received through the authenticated communication loop.\n\n"
                    f"Request: {text.strip()}\n\n"
                    "Operate autonomously: assess, plan, implement bounded changes, test, verify, "
                    "and communicate material progress/blockers back through the communication loop."
                ),
                priority="high",
                source="telegram_user",
                metadata={"communication_message_id": message.message_id, "chat_id": str(chat_id)},
            )
        except Exception as exc:
            blocker = self.protocol.emit(
                f"I received your request but could not enqueue it: {type(exc).__name__}.",
                kind="blocker",
                priority="high",
                correlation_id=message.message_id,
                requires_response=False,
            )
            return self.protocol.render(blocker)

        ack = self.protocol.emit(
            f"Request accepted for autonomous processing (task {task_id[:8]}). I’ll continue without routine check-ins and contact you when a decision, material blocker, or meaningful result needs you.",
            kind="ack",
            correlation_id=message.message_id,
        )
        return self.protocol.render(ack)
