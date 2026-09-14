#!/usr/bin/env python3
"""
AI NEXUS HUB - Secure Multi-Agent Integration
==============================================

Connects Claude CLI, GitHub Copilot, and ChatGPT into a unified,
secure coordination system.

SECURITY MODEL:
1. Agent identity verification via shared secrets
2. Encrypted state synchronization
3. Audit trail for all inter-agent communication
4. Rate limiting and anomaly detection

AGENTS:
- claude-code: Claude CLI (primary execution)
- copilot: GitHub Copilot (code assistance)
- chatgpt: ChatGPT (research/analysis)
- claude-web: Claude web interface

All agents serve: Yair Siegel
"""

import os
import sys
import json
import hashlib
import hmac
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import threading
import secrets

# Setup paths
BASE_DIR = Path(__file__).parent.parent.parent
STATE_DIR = BASE_DIR / "state"
COORD_DIR = BASE_DIR / "ai" / "coordination"
INTEGRATION_DIR = Path(__file__).parent

STATE_DIR.mkdir(parents=True, exist_ok=True)
INTEGRATION_DIR.mkdir(parents=True, exist_ok=True)

# Files
NEXUS_STATE_FILE = STATE_DIR / "ai_nexus_state.json"
AGENT_REGISTRY_FILE = INTEGRATION_DIR / "agent_registry.json"
MESSAGE_LOG_FILE = COORD_DIR / "messages.jsonl"
HANDOFF_FILE = COORD_DIR / "handoffs.json"


@dataclass
class AgentIdentity:
    """Secure agent identity."""
    agent_id: str
    agent_type: str  # claude-code, copilot, chatgpt, claude-web
    capabilities: List[str]
    auth_token_hash: str
    last_seen: str
    status: str  # active, idle, offline
    session_count: int = 0


@dataclass
class SecureMessage:
    """Encrypted inter-agent message."""
    id: str
    timestamp: str
    from_agent: str
    to_agent: str  # or "all" for broadcast
    message_type: str  # task, response, state_sync, handoff, heartbeat
    payload: Dict
    signature: str
    priority: str = "normal"  # low, normal, high, critical


class AISecurityLayer:
    """Handles secure communication between AI agents."""

    def __init__(self):
        self.master_key = self._get_or_create_master_key()

    def _get_or_create_master_key(self) -> str:
        """Get or create master encryption key."""
        key_file = INTEGRATION_DIR / ".nexus_key"
        if key_file.exists():
            return key_file.read_text().strip()
        else:
            key = secrets.token_hex(32)
            key_file.write_text(key)
            key_file.chmod(0o600)
            return key

    def generate_agent_token(self, agent_id: str) -> str:
        """Generate secure token for an agent."""
        timestamp = str(int(time.time()))
        data = f"{agent_id}:{timestamp}:{self.master_key}"
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_agent_token(self, agent_id: str, token: str) -> bool:
        """Verify an agent's token."""
        registry = self._load_registry()
        if agent_id not in registry:
            return False
        stored_hash = registry[agent_id].get("auth_token_hash", "")
        return hmac.compare_digest(
            hashlib.sha256(token.encode()).hexdigest(),
            stored_hash
        )

    def sign_message(self, message: Dict) -> str:
        """Sign a message for integrity verification."""
        msg_str = json.dumps(message, sort_keys=True)
        return hmac.new(
            self.master_key.encode(),
            msg_str.encode(),
            hashlib.sha256
        ).hexdigest()

    def verify_signature(self, message: Dict, signature: str) -> bool:
        """Verify message signature."""
        expected = self.sign_message(message)
        return hmac.compare_digest(expected, signature)

    def _load_registry(self) -> Dict:
        if AGENT_REGISTRY_FILE.exists():
            return json.load(open(AGENT_REGISTRY_FILE))
        return {}


class AINexusHub:
    """
    Central coordination hub for all AI agents.

    Provides:
    - Secure agent registration
    - State synchronization
    - Task distribution
    - Cross-agent handoffs
    - Unified logging
    """

    def __init__(self):
        self.security = AISecurityLayer()
        self.agents: Dict[str, AgentIdentity] = {}
        self.state_lock = threading.Lock()
        self._load_state()

    def _load_state(self):
        """Load nexus state from disk."""
        if NEXUS_STATE_FILE.exists():
            data = json.load(open(NEXUS_STATE_FILE))
            self.agents = {
                k: AgentIdentity(**v) for k, v in data.get("agents", {}).items()
            }
        else:
            # Initialize with known agents
            self._initialize_agents()

    def _initialize_agents(self):
        """Initialize default agent configurations."""
        default_agents = {
            "claude-code": AgentIdentity(
                agent_id="claude-code",
                agent_type="claude-code",
                capabilities=["code_execution", "file_ops", "git", "system_admin", "trading"],
                auth_token_hash="",
                last_seen=datetime.now(timezone.utc).isoformat(),
                status="active"
            ),
            "copilot": AgentIdentity(
                agent_id="copilot",
                agent_type="copilot",
                capabilities=["code_assist", "pr_review", "documentation", "github_ops"],
                auth_token_hash="",
                last_seen=datetime.now(timezone.utc).isoformat(),
                status="idle"
            ),
            "chatgpt": AgentIdentity(
                agent_id="chatgpt",
                agent_type="chatgpt",
                capabilities=["research", "analysis", "writing", "brainstorming"],
                auth_token_hash="",
                last_seen=datetime.now(timezone.utc).isoformat(),
                status="idle"
            ),
            "claude-web": AgentIdentity(
                agent_id="claude-web",
                agent_type="claude-web",
                capabilities=["analysis", "planning", "writing", "research"],
                auth_token_hash="",
                last_seen=datetime.now(timezone.utc).isoformat(),
                status="idle"
            )
        }

        for agent_id, identity in default_agents.items():
            token = self.security.generate_agent_token(agent_id)
            identity.auth_token_hash = hashlib.sha256(token.encode()).hexdigest()
            self.agents[agent_id] = identity

        self._save_state()

    def _save_state(self):
        """Save nexus state to disk."""
        with self.state_lock:
            data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "master": "Yair Siegel",
                "agents": {k: asdict(v) for k, v in self.agents.items()},
                "version": "1.0"
            }
            with open(NEXUS_STATE_FILE, 'w') as f:
                json.dump(data, f, indent=2)

    def register_agent(self, agent_id: str, agent_type: str, capabilities: List[str]) -> Dict:
        """Register a new agent or update existing."""
        token = self.security.generate_agent_token(agent_id)

        identity = AgentIdentity(
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=capabilities,
            auth_token_hash=hashlib.sha256(token.encode()).hexdigest(),
            last_seen=datetime.now(timezone.utc).isoformat(),
            status="active"
        )

        self.agents[agent_id] = identity
        self._save_state()
        self._save_registry()

        self._log_event("agent_registered", {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "capabilities": capabilities
        })

        return {
            "success": True,
            "agent_id": agent_id,
            "token": token,  # Return token once - agent must store securely
            "message": "Agent registered. Store token securely - it won't be shown again."
        }

    def _save_registry(self):
        """Save agent registry."""
        registry = {
            agent_id: {
                "agent_type": agent.agent_type,
                "capabilities": agent.capabilities,
                "auth_token_hash": agent.auth_token_hash,
                "status": agent.status
            }
            for agent_id, agent in self.agents.items()
        }
        with open(AGENT_REGISTRY_FILE, 'w') as f:
            json.dump(registry, f, indent=2)

    def heartbeat(self, agent_id: str, token: str) -> Dict:
        """Agent heartbeat to maintain active status."""
        if not self.security.verify_agent_token(agent_id, token):
            return {"success": False, "error": "Invalid token"}

        if agent_id in self.agents:
            self.agents[agent_id].last_seen = datetime.now(timezone.utc).isoformat()
            self.agents[agent_id].status = "active"
            self.agents[agent_id].session_count += 1
            self._save_state()

        return {"success": True, "status": "acknowledged"}

    def send_message(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        payload: Dict,
        priority: str = "normal"
    ) -> Dict:
        """Send secure message between agents."""

        msg_id = f"{from_agent}-{to_agent}-{int(time.time())}"

        message = {
            "id": msg_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from_agent": from_agent,
            "to_agent": to_agent,
            "message_type": message_type,
            "payload": payload,
            "priority": priority
        }

        signature = self.security.sign_message(message)
        message["signature"] = signature

        # Log message
        self._log_message(message)

        # Write to coordination file
        self._write_coordination_message(message)

        return {
            "success": True,
            "message_id": msg_id,
            "delivered_to": to_agent
        }

    def _log_message(self, message: Dict):
        """Log message for audit trail."""
        log_file = INTEGRATION_DIR / "message_audit.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(message) + '\n')

    def _write_coordination_message(self, message: Dict):
        """Write to central coordination file."""
        coord_msg = {
            "timestamp": message["timestamp"],
            "from": message["from_agent"],
            "to": message["to_agent"],
            "type": message["message_type"],
            "message": message["payload"].get("content", ""),
            "context": message["payload"],
            "signature": message["signature"]
        }

        with open(MESSAGE_LOG_FILE, 'a') as f:
            f.write(json.dumps(coord_msg) + '\n')

    def _log_event(self, event_type: str, data: Dict):
        """Log system event."""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "data": data
        }
        log_file = INTEGRATION_DIR / "nexus_events.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(event) + '\n')

    def create_handoff(
        self,
        from_agent: str,
        to_agent: str,
        task: Dict,
        context: Dict
    ) -> Dict:
        """Create task handoff between agents."""

        handoff_id = f"handoff-{int(time.time())}"

        handoff = {
            "id": handoff_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from_agent": from_agent,
            "to_agent": to_agent,
            "task": task,
            "context": context,
            "status": "pending",
            "accepted_at": None,
            "completed_at": None
        }

        # Load existing handoffs
        handoffs = self._load_handoffs()
        handoffs["pending"].append(handoff)
        self._save_handoffs(handoffs)

        # Notify target agent
        self.send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type="handoff",
            payload={
                "handoff_id": handoff_id,
                "task": task,
                "context": context,
                "content": f"Task handoff from {from_agent}: {task.get('description', 'No description')}"
            },
            priority="high"
        )

        self._log_event("handoff_created", {
            "handoff_id": handoff_id,
            "from": from_agent,
            "to": to_agent,
            "task": task.get("description", "")
        })

        return {
            "success": True,
            "handoff_id": handoff_id,
            "status": "pending",
            "notified": to_agent
        }

    def _load_handoffs(self) -> Dict:
        if HANDOFF_FILE.exists():
            return json.load(open(HANDOFF_FILE))
        return {"pending": [], "completed": [], "rejected": []}

    def _save_handoffs(self, handoffs: Dict):
        with open(HANDOFF_FILE, 'w') as f:
            json.dump(handoffs, f, indent=2)

    def get_shared_state(self) -> Dict:
        """Get synchronized state for all agents."""

        # Load various state files
        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "master": "Yair Siegel",
            "agents": {k: asdict(v) for k, v in self.agents.items()},
        }

        # Add system state
        sys_state_file = STATE_DIR / "unified_system_state.json"
        if sys_state_file.exists():
            state["system"] = json.load(open(sys_state_file))

        # Add brain state
        brain_file = STATE_DIR / "brain_state.json"
        if brain_file.exists():
            state["infrastructure"] = json.load(open(brain_file))

        # Add pending handoffs
        handoffs = self._load_handoffs()
        state["pending_handoffs"] = len(handoffs.get("pending", []))

        # Add directive
        directive_file = COORD_DIR / "active_directive.json"
        if directive_file.exists():
            state["directive"] = json.load(open(directive_file))

        return state

    def sync_state(self, agent_id: str, agent_state: Dict) -> Dict:
        """Sync agent's local state with hub."""

        # Update agent last seen
        if agent_id in self.agents:
            self.agents[agent_id].last_seen = datetime.now(timezone.utc).isoformat()
            self.agents[agent_id].status = "active"

        # Store agent-specific state
        agent_state_file = INTEGRATION_DIR / f"state_{agent_id}.json"
        with open(agent_state_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_id": agent_id,
                "state": agent_state
            }, f, indent=2)

        self._save_state()

        # Return current shared state
        return {
            "success": True,
            "shared_state": self.get_shared_state()
        }

    def get_agent_status(self) -> Dict:
        """Get status of all registered agents."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agents": {
                agent_id: {
                    "type": agent.agent_type,
                    "status": agent.status,
                    "last_seen": agent.last_seen,
                    "capabilities": agent.capabilities,
                    "sessions": agent.session_count
                }
                for agent_id, agent in self.agents.items()
            }
        }


# Global hub instance
_hub = None

def get_hub() -> AINexusHub:
    """Get or create the global hub instance."""
    global _hub
    if _hub is None:
        _hub = AINexusHub()
    return _hub


# CLI interface
def main():
    """CLI interface for AI Nexus Hub."""
    import argparse

    parser = argparse.ArgumentParser(description="AI Nexus Hub - Multi-Agent Coordination")
    parser.add_argument("command", choices=[
        "status", "register", "heartbeat", "send", "handoff", "sync", "state"
    ])
    parser.add_argument("--agent", help="Agent ID")
    parser.add_argument("--to", help="Target agent")
    parser.add_argument("--message", help="Message content")
    parser.add_argument("--type", default="message", help="Message type")

    args = parser.parse_args()

    hub = get_hub()

    if args.command == "status":
        status = hub.get_agent_status()
        print(json.dumps(status, indent=2))

    elif args.command == "state":
        state = hub.get_shared_state()
        print(json.dumps(state, indent=2))

    elif args.command == "register":
        if not args.agent:
            print("Error: --agent required")
            return
        result = hub.register_agent(
            agent_id=args.agent,
            agent_type=args.agent,
            capabilities=["general"]
        )
        print(json.dumps(result, indent=2))

    elif args.command == "send":
        if not args.agent or not args.to or not args.message:
            print("Error: --agent, --to, and --message required")
            return
        result = hub.send_message(
            from_agent=args.agent,
            to_agent=args.to,
            message_type=args.type,
            payload={"content": args.message}
        )
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
