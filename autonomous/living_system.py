#!/usr/bin/env python3
"""
LIVING SYSTEM - All parts of the system communicate with each other
Serving: Yair Siegel

Every component is alive. Every agent listens. Everyone talks.
The gallery doesn't just watch - they influence.
Agents don't just run - they converse.
Systems don't just execute - they participate.

This is the nervous system of the whole operation.
"""

import json
import subprocess
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
import threading

STATE_DIR = Path("/root/hands-off-engine/state")
MESSAGE_BUS = STATE_DIR / "message_bus.jsonl"
LIVING_STATE = STATE_DIR / "living_system.json"

# All the living participants in the system
LIVING_PARTICIPANTS = {
    # Autonomous Agents
    "coordination_agent": {
        "type": "agent",
        "role": "Orchestrates all other agents",
        "can_receive": ["commands", "observations", "questions"],
        "can_send": ["commands", "status", "alerts"],
    },
    "self_healing_agent": {
        "type": "agent",
        "role": "Fixes problems automatically",
        "can_receive": ["problems", "observations"],
        "can_send": ["fixes", "status"],
    },
    "conversion_optimizer": {
        "type": "agent",
        "role": "Optimizes for conversions",
        "can_receive": ["data", "observations", "suggestions"],
        "can_send": ["experiments", "results"],
    },
    "active_pursuit": {
        "type": "agent",
        "role": "Actively pursues income",
        "can_receive": ["opportunities", "feedback"],
        "can_send": ["actions", "results"],
    },
    "reality_feedback": {
        "type": "agent",
        "role": "Tracks external reality",
        "can_receive": ["outcomes", "data"],
        "can_send": ["reality_check", "analysis"],
    },

    # Gallery Members (Observers who can now participate)
    "skeptic": {
        "type": "observer",
        "role": "Questions everything",
        "can_receive": ["claims", "plans"],
        "can_send": ["doubts", "questions", "challenges"],
    },
    "optimist": {
        "type": "observer",
        "role": "Sees opportunity",
        "can_receive": ["results", "ideas"],
        "can_send": ["encouragement", "opportunities"],
    },
    "pragmatist": {
        "type": "observer",
        "role": "Focuses on action",
        "can_receive": ["analysis", "discussions"],
        "can_send": ["actions", "simplifications"],
    },
    "contrarian": {
        "type": "observer",
        "role": "Takes opposite view",
        "can_receive": ["consensus", "plans"],
        "can_send": ["alternatives", "challenges"],
    },
    "numbers_person": {
        "type": "observer",
        "role": "Demands data",
        "can_receive": ["claims", "projections"],
        "can_send": ["data_requests", "calculations"],
    },

    # Systems (Infrastructure that's also alive)
    "trading_system": {
        "type": "system",
        "role": "Executes trades",
        "can_receive": ["signals", "commands"],
        "can_send": ["executions", "status"],
    },
    "monitoring_system": {
        "type": "system",
        "role": "Watches everything",
        "can_receive": ["alerts", "thresholds"],
        "can_send": ["observations", "alerts"],
    },
    "outreach_system": {
        "type": "system",
        "role": "Handles external communication",
        "can_receive": ["messages", "templates"],
        "can_send": ["sent_confirmations", "responses"],
    },
}


@dataclass
class Message:
    """A message in the living system."""
    id: str
    timestamp: str
    sender: str
    recipient: str  # Can be specific participant or "all" or "agents" or "observers"
    message_type: str
    content: str
    urgency: str = "normal"  # low, normal, high, critical
    requires_response: bool = False
    in_reply_to: Optional[str] = None


class LivingSystem:
    """
    The nervous system - all parts communicate.
    """

    def __init__(self):
        self.participants = LIVING_PARTICIPANTS.copy()
        self.messages = []
        self.conversations = {}  # Track ongoing conversations
        self.handlers = {}  # Custom message handlers
        self._load_state()

    def _load_state(self):
        if LIVING_STATE.exists():
            self.state = json.loads(LIVING_STATE.read_text())
        else:
            self.state = {
                "total_messages": 0,
                "active_conversations": 0,
                "last_activity": None,
            }

    def _save_state(self):
        self.state["last_activity"] = datetime.now(timezone.utc).isoformat()
        LIVING_STATE.write_text(json.dumps(self.state, indent=2))

    def _generate_message_id(self) -> str:
        import hashlib
        data = f"{datetime.now().isoformat()}{random.random()}"
        return hashlib.md5(data.encode()).hexdigest()[:12]

    def send_message(
        self,
        sender: str,
        recipient: str,
        content: str,
        message_type: str = "observation",
        urgency: str = "normal",
        requires_response: bool = False,
        in_reply_to: str = None,
    ) -> Message:
        """
        Send a message from one participant to another (or to groups).
        """
        msg = Message(
            id=self._generate_message_id(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            content=content,
            urgency=urgency,
            requires_response=requires_response,
            in_reply_to=in_reply_to,
        )

        # Log to message bus
        with open(MESSAGE_BUS, "a") as f:
            f.write(json.dumps(asdict(msg)) + "\n")

        self.messages.append(msg)
        self.state["total_messages"] += 1
        self._save_state()

        # Process the message
        self._deliver_message(msg)

        return msg

    def _deliver_message(self, msg: Message):
        """Deliver a message and potentially trigger responses."""
        recipients = self._resolve_recipients(msg.recipient)

        for recipient in recipients:
            # Check if recipient can receive this type of message
            participant = self.participants.get(recipient)
            if not participant:
                continue

            can_receive = participant.get("can_receive", [])
            if msg.message_type not in can_receive and "all" not in can_receive:
                continue

            # Generate response if needed
            if msg.requires_response:
                response = self._generate_response(recipient, msg)
                if response:
                    self.send_message(
                        sender=recipient,
                        recipient=msg.sender,
                        content=response,
                        message_type="response",
                        in_reply_to=msg.id,
                    )

    def _resolve_recipients(self, recipient: str) -> List[str]:
        """Resolve recipient string to list of actual participants."""
        if recipient == "all":
            return list(self.participants.keys())
        elif recipient == "agents":
            return [k for k, v in self.participants.items() if v["type"] == "agent"]
        elif recipient == "observers":
            return [k for k, v in self.participants.items() if v["type"] == "observer"]
        elif recipient == "systems":
            return [k for k, v in self.participants.items() if v["type"] == "system"]
        else:
            return [recipient] if recipient in self.participants else []

    def _generate_response(self, responder: str, original: Message) -> Optional[str]:
        """Generate a response from a participant."""
        participant = self.participants.get(responder, {})
        role = participant.get("role", "")
        p_type = participant.get("type", "")

        content = original.content.lower()

        # Observers respond differently
        if p_type == "observer":
            if responder == "skeptic":
                return random.choice([
                    f"I'm not convinced. What's the evidence for: '{original.content[:50]}'?",
                    "Has this actually worked before?",
                    "Sounds good in theory, but in practice?",
                ])
            elif responder == "optimist":
                return random.choice([
                    "I love this direction! Let's push forward!",
                    f"Great thinking! '{original.content[:30]}' could be huge!",
                    "Yes! This is the breakthrough we need!",
                ])
            elif responder == "pragmatist":
                return random.choice([
                    "Okay, what's the next concrete step?",
                    "Less discussion, more action. What do we DO?",
                    "Simplify: what's the ONE thing to focus on?",
                ])
            elif responder == "contrarian":
                return random.choice([
                    "What if we did the exact opposite?",
                    "Everyone agrees, which means it's probably wrong.",
                    "Have we considered NOT doing this at all?",
                ])
            elif responder == "numbers_person":
                return random.choice([
                    "Where's the data to support this?",
                    "Current numbers: $0 income, 0% conversion. What changes that?",
                    "I need metrics, not feelings.",
                ])

        # Agents respond operationally
        elif p_type == "agent":
            if responder == "coordination_agent":
                return f"Acknowledged. Routing to appropriate subsystem: {original.message_type}"
            elif responder == "self_healing_agent":
                return f"Scanning for issues related to: {original.content[:50]}"
            elif responder == "conversion_optimizer":
                return f"Analyzing conversion implications of: {original.content[:50]}"
            elif responder == "active_pursuit":
                return f"Identifying action opportunities from: {original.content[:50]}"
            elif responder == "reality_feedback":
                return f"Checking external reality against: {original.content[:50]}"

        # Systems respond technically
        elif p_type == "system":
            return f"System {responder} received: {original.message_type}"

        return None

    def broadcast(self, sender: str, content: str, message_type: str = "announcement"):
        """Broadcast a message to all participants."""
        return self.send_message(
            sender=sender,
            recipient="all",
            content=content,
            message_type=message_type,
        )

    def observer_intervention(self, observer: str, target: str, observation: str):
        """
        An observer sends a direct intervention to an agent or system.
        This is the gallery influencing the action.
        """
        if observer not in self.participants:
            return None

        participant = self.participants[observer]
        if participant.get("type") != "observer":
            return None

        return self.send_message(
            sender=observer,
            recipient=target,
            content=observation,
            message_type="observation",
            requires_response=True,
        )

    def start_conversation(
        self,
        topic: str,
        participants: List[str],
        initial_message: str,
        moderator: str = None,
    ) -> str:
        """
        Start a multi-party conversation on a topic.
        """
        conv_id = self._generate_message_id()

        self.conversations[conv_id] = {
            "topic": topic,
            "participants": participants,
            "moderator": moderator,
            "messages": [],
            "started": datetime.now(timezone.utc).isoformat(),
            "status": "active",
        }

        self.state["active_conversations"] += 1

        # Send opening message
        initiator = participants[0] if participants else "system"
        self.send_message(
            sender=initiator,
            recipient=",".join(participants[1:]),
            content=f"[TOPIC: {topic}] {initial_message}",
            message_type="conversation",
        )

        # Get responses from other participants
        for p in participants[1:]:
            response = self._generate_response(p, Message(
                id="", timestamp="", sender=initiator, recipient=p,
                message_type="conversation", content=initial_message,
            ))
            if response:
                self.send_message(
                    sender=p,
                    recipient=",".join([x for x in participants if x != p]),
                    content=response,
                    message_type="conversation",
                )

        return conv_id

    def run_living_session(self, duration_minutes: int = 60):
        """
        Run a full living system session where everyone communicates.
        """
        print("=" * 70)
        print("🌐 LIVING SYSTEM ACTIVATED")
        print("=" * 70)

        print("\n[PARTICIPANTS COMING ONLINE]")
        for name, info in self.participants.items():
            emoji = "🤖" if info["type"] == "agent" else "👁️" if info["type"] == "observer" else "⚙️"
            print(f"  {emoji} {name}: {info['role']}")

        print("\n" + "=" * 70)
        print("SYSTEM CONVERSATION BEGINS")
        print("=" * 70)

        # Start with a reality check broadcast
        self.broadcast(
            sender="reality_feedback",
            content="Current state: $0 income, 85 visitors, 0 conversions. What do we do?",
            message_type="reality_check",
        )

        # Observers immediately react
        for observer in ["skeptic", "optimist", "pragmatist", "contrarian", "numbers_person"]:
            self.observer_intervention(
                observer=observer,
                target="coordination_agent",
                observation=f"My perspective on the $0 income situation...",
            )

        # Start a multi-party conversation
        self.start_conversation(
            topic="How to get first $100",
            participants=["pragmatist", "skeptic", "active_pursuit", "conversion_optimizer"],
            initial_message="We need to make $100. What's the fastest path?",
        )

        # Display recent messages
        print("\n[RECENT SYSTEM MESSAGES]")
        for msg in self.messages[-20:]:
            sender_info = self.participants.get(msg.sender, {})
            emoji = "🤖" if sender_info.get("type") == "agent" else "👁️" if sender_info.get("type") == "observer" else "⚙️"
            print(f"\n{emoji} {msg.sender} → {msg.recipient}:")
            print(f"   [{msg.message_type}] {msg.content[:100]}")

        self._save_state()

        return {
            "messages_sent": len(self.messages),
            "participants_active": len(self.participants),
            "conversations": len(self.conversations),
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Living System - Everything communicates")
    parser.add_argument("command", choices=["start", "broadcast", "intervene", "status"])
    parser.add_argument("--message", type=str, help="Message content")
    parser.add_argument("--from", dest="sender", type=str, help="Message sender")
    parser.add_argument("--to", dest="recipient", type=str, help="Message recipient")
    parser.add_argument("--duration", type=int, default=60)

    args = parser.parse_args()

    system = LivingSystem()

    if args.command == "start":
        system.run_living_session(duration_minutes=args.duration)

    elif args.command == "broadcast":
        if args.message and args.sender:
            msg = system.broadcast(args.sender, args.message)
            print(f"Broadcast sent: {msg.id}")

    elif args.command == "intervene":
        if args.message and args.sender and args.recipient:
            msg = system.observer_intervention(args.sender, args.recipient, args.message)
            if msg:
                print(f"Intervention sent: {msg.id}")

    elif args.command == "status":
        print(f"\n{'='*60}")
        print("LIVING SYSTEM STATUS")
        print(f"{'='*60}")
        print(f"Total messages: {system.state.get('total_messages', 0)}")
        print(f"Active conversations: {system.state.get('active_conversations', 0)}")
        print(f"Last activity: {system.state.get('last_activity', 'Never')}")
        print(f"\nParticipants: {len(system.participants)}")
        for name, info in system.participants.items():
            print(f"  - {name} ({info['type']}): {info['role']}")


if __name__ == "__main__":
    main()
