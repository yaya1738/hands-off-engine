#!/usr/bin/env python3
"""
MEGA UNIFIED SYSTEM - Complete AI Integration for Yair Siegel
==============================================================

This is the MASTER integration layer that merges:

1. UNIFIED AI (ai/unified_ai.py)
   - Core identity and directives
   - Decision-making (should_execute)
   - System state management

2. AI NEXUS HUB (ai/integration/ai_nexus_hub.py)
   - Secure agent authentication
   - Cross-agent messaging
   - Task handoffs

3. TRI-AGENT SESSIONS (ai_nexus/tri_agent_session_runner.py)
   - ChatGPT + Claude + Copilot coordination
   - Multi-round discussions
   - CpuInstance abstraction

4. MEGA INTEGRATION (autonomous/mega_integration.py)
   - Hardware Brain
   - Scaling Engine
   - Self-Healer

5. UNIFIED DASHBOARD (ui/unified_dashboard.py)
   - Web UI integration
   - Real-time status

ALL SYSTEMS NOW UNIFIED UNDER ONE MASTER.
SERVING: YAIR SIEGEL
"""

import json
import sys
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict, field

# Setup paths
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

# State directories
STATE_DIR = BASE_DIR / 'state'
COORD_DIR = BASE_DIR / 'ai' / 'coordination'
INTEGRATION_DIR = BASE_DIR / 'ai' / 'integration'

STATE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# IMPORT ALL SUBSYSTEMS
# ============================================================================

# 1. Unified AI - Core Identity
try:
    from ai.unified_ai import (
        MASTER, get_master, get_core, get_directive,
        should_execute, get_priorities, log_action,
        get_system_state, update_system_state,
        check_trading_allowed, send_master_notification,
        run_system_check
    )
    HAS_UNIFIED_AI = True
except ImportError as e:
    HAS_UNIFIED_AI = False
    MASTER = "Yair Siegel"
    print(f"[WARN] Could not import unified_ai: {e}")

# 2. AI Nexus Hub - Agent Coordination
try:
    from ai.integration.ai_nexus_hub import (
        AINexusHub, get_hub, AISecurityLayer
    )
    HAS_NEXUS_HUB = True
except ImportError as e:
    HAS_NEXUS_HUB = False
    print(f"[WARN] Could not import ai_nexus_hub: {e}")

# 3. Copilot Adapter
try:
    from ai.integration.copilot_adapter import CopilotAdapter
    HAS_COPILOT = True
except ImportError as e:
    HAS_COPILOT = False
    print(f"[WARN] Could not import copilot_adapter: {e}")

# 4. ChatGPT Adapter
try:
    from ai.integration.chatgpt_adapter import ChatGPTAdapter
    HAS_CHATGPT = True
except ImportError as e:
    HAS_CHATGPT = False
    print(f"[WARN] Could not import chatgpt_adapter: {e}")

# 5. Tri-Agent Sessions
try:
    from ai_nexus.tri_agent_session_runner import TriAgentSession
    HAS_TRI_AGENT = True
except ImportError as e:
    HAS_TRI_AGENT = False
    print(f"[WARN] Could not import tri_agent_session_runner: {e}")

# 6. Mega Integration
try:
    from autonomous.mega_integration import MegaSystemState, create_mega_service
    HAS_MEGA = True
except ImportError as e:
    HAS_MEGA = False
    print(f"[WARN] Could not import mega_integration: {e}")


# ============================================================================
# MEGA UNIFIED STATE
# ============================================================================

@dataclass
class MegaUnifiedState:
    """Complete unified state across ALL systems."""

    timestamp: str = ""
    master: str = "Yair Siegel"

    # Subsystem availability
    has_unified_ai: bool = False
    has_nexus_hub: bool = False
    has_copilot: bool = False
    has_chatgpt: bool = False
    has_tri_agent: bool = False
    has_mega: bool = False

    # Agent status
    agents: Dict[str, Dict] = field(default_factory=dict)
    active_agents: List[str] = field(default_factory=list)

    # Financial
    balance: float = 0.0
    positions_value: float = 0.0
    trading_enabled: bool = False
    escape_velocity: int = 0

    # Infrastructure
    total_vcpus: int = 0
    total_ram_gb: float = 0.0
    healthy_nodes: int = 0

    # Coordination
    pending_handoffs: int = 0
    pending_messages: int = 0
    last_coordination: str = ""

    # System health
    overall_health: str = "unknown"
    component_status: Dict[str, str] = field(default_factory=dict)


# ============================================================================
# MEGA UNIFIED SYSTEM
# ============================================================================

class MegaUnifiedSystem:
    """
    THE MASTER SYSTEM - Unifies all AI components.

    This is the single entry point for all AI operations.
    All agents, subsystems, and components coordinate through this.
    """

    def __init__(self):
        self.master = MASTER if HAS_UNIFIED_AI else "Yair Siegel"
        self.state = MegaUnifiedState(
            timestamp=datetime.now(timezone.utc).isoformat(),
            master=self.master,
            has_unified_ai=HAS_UNIFIED_AI,
            has_nexus_hub=HAS_NEXUS_HUB,
            has_copilot=HAS_COPILOT,
            has_chatgpt=HAS_CHATGPT,
            has_tri_agent=HAS_TRI_AGENT,
            has_mega=HAS_MEGA
        )

        # Initialize subsystems
        self.nexus_hub = get_hub() if HAS_NEXUS_HUB else None
        self.copilot = CopilotAdapter() if HAS_COPILOT else None
        self.chatgpt = ChatGPTAdapter() if HAS_CHATGPT else None

        # State lock for thread safety
        self._lock = threading.Lock()

        # Initialize
        self._refresh_state()
        self._log("MegaUnifiedSystem initialized", {
            "subsystems": {
                "unified_ai": HAS_UNIFIED_AI,
                "nexus_hub": HAS_NEXUS_HUB,
                "copilot": HAS_COPILOT,
                "chatgpt": HAS_CHATGPT,
                "tri_agent": HAS_TRI_AGENT,
                "mega": HAS_MEGA
            }
        })

    # ========================================================================
    # CORE OPERATIONS
    # ========================================================================

    def get_full_state(self) -> Dict:
        """Get complete system state from all subsystems."""
        self._refresh_state()
        return asdict(self.state)

    def _refresh_state(self):
        """Refresh state from all subsystems."""
        with self._lock:
            self.state.timestamp = datetime.now(timezone.utc).isoformat()

            # From unified_ai
            if HAS_UNIFIED_AI:
                sys_state = get_system_state()
                self.state.balance = sys_state.get("balance", 0)
                self.state.positions_value = sys_state.get("positions_value", 0)
                self.state.trading_enabled = sys_state.get("trading_enabled", False)
                self.state.escape_velocity = sys_state.get("escape_velocity", 0)

            # From nexus hub
            if self.nexus_hub:
                agent_status = self.nexus_hub.get_agent_status()
                self.state.agents = agent_status.get("agents", {})
                self.state.active_agents = [
                    k for k, v in self.state.agents.items()
                    if v.get("status") == "active"
                ]
                shared = self.nexus_hub.get_shared_state()
                self.state.pending_handoffs = shared.get("pending_handoffs", 0)

            # From brain state
            brain_file = STATE_DIR / "brain_state.json"
            if brain_file.exists():
                brain = json.load(open(brain_file))
                self.state.total_vcpus = brain.get("total_vcpus", 0)
                self.state.total_ram_gb = brain.get("total_ram_gb", 0)
                self.state.healthy_nodes = brain.get("healthy_nodes", 0)

            # Component status
            self.state.component_status = {
                "unified_ai": "active" if HAS_UNIFIED_AI else "missing",
                "nexus_hub": "active" if self.nexus_hub else "missing",
                "copilot": "ready" if self.copilot else "missing",
                "chatgpt": "ready" if self.chatgpt else "missing",
                "tri_agent": "available" if HAS_TRI_AGENT else "missing",
                "mega_integration": "available" if HAS_MEGA else "missing"
            }

            # Overall health
            active_count = sum(1 for v in self.state.component_status.values() if v != "missing")
            if active_count >= 5:
                self.state.overall_health = "excellent"
            elif active_count >= 3:
                self.state.overall_health = "good"
            elif active_count >= 1:
                self.state.overall_health = "degraded"
            else:
                self.state.overall_health = "critical"

    # ========================================================================
    # AGENT COORDINATION
    # ========================================================================

    def coordinate_agents(
        self,
        task: Dict,
        agents: List[str] = None,
        method: str = "auto"
    ) -> Dict:
        """
        Coordinate task across agents.

        Args:
            task: Task to coordinate
            agents: Specific agents to involve (default: auto-select)
            method: "parallel", "sequential", "tri-session", "auto"

        Returns:
            Coordination result
        """
        agents = agents or self._select_best_agents(task)

        if method == "auto":
            method = self._select_coordination_method(task, agents)

        self._log("coordinate_agents", {
            "task": task.get("description", ""),
            "agents": agents,
            "method": method
        })

        if method == "tri-session" and HAS_TRI_AGENT:
            return self._run_tri_agent_session(task, agents)
        elif method == "parallel":
            return self._run_parallel_coordination(task, agents)
        else:
            return self._run_sequential_coordination(task, agents)

    def _select_best_agents(self, task: Dict) -> List[str]:
        """Select best agents for a task based on capabilities."""
        task_type = task.get("type", "general")
        description = task.get("description", "").lower()

        agents = ["claude-code"]  # Always include primary

        if "code" in description or "review" in description or "pr" in description:
            agents.append("copilot")

        if "research" in description or "analyze" in description or "market" in description:
            agents.append("chatgpt")

        if "plan" in description or "strategy" in description:
            agents.append("claude-web")

        return list(set(agents))

    def _select_coordination_method(self, task: Dict, agents: List[str]) -> str:
        """Select best coordination method."""
        if len(agents) >= 3 and HAS_TRI_AGENT:
            return "tri-session"
        elif len(agents) == 1:
            return "sequential"
        else:
            return "parallel"

    def _run_tri_agent_session(self, task: Dict, agents: List[str]) -> Dict:
        """Run tri-agent discussion session."""
        if not HAS_TRI_AGENT:
            return {"success": False, "error": "Tri-agent not available"}

        conv_id = f"mega_{int(time.time())}"

        # Map to tri-agent agent names
        agent_map = {
            "claude-code": "claude_cli",
            "chatgpt": "chatgpt",
            "copilot": "github_copilot_agent"
        }
        session_agents = [agent_map.get(a, a) for a in agents if a in agent_map]

        session = TriAgentSession(
            conversation_id=conv_id,
            session_goal=task.get("description", "Multi-agent coordination"),
            max_rounds=task.get("rounds", 2),
            max_cost_usd=task.get("max_cost", 1.0)
        )

        # This would run the session - simplified here
        return {
            "success": True,
            "method": "tri-session",
            "session_id": conv_id,
            "agents": session_agents,
            "message": "Tri-agent session created"
        }

    def _run_parallel_coordination(self, task: Dict, agents: List[str]) -> Dict:
        """Run parallel coordination via nexus hub."""
        results = {}

        for agent in agents:
            if agent == "chatgpt" and self.chatgpt:
                result = self.chatgpt.delegate_task({
                    "type": task.get("type", "research"),
                    "description": task.get("description", ""),
                    "context": task.get("context", {})
                })
                results["chatgpt"] = result

            elif agent == "copilot" and self.copilot:
                result = self.copilot.send_task_to_copilot({
                    "title": task.get("title", "Task"),
                    "description": task.get("description", ""),
                    "priority": task.get("priority", "normal")
                })
                results["copilot"] = result

            elif self.nexus_hub:
                self.nexus_hub.send_message(
                    from_agent="claude-code",
                    to_agent=agent,
                    message_type="task",
                    payload=task,
                    priority=task.get("priority", "normal")
                )
                results[agent] = {"success": True, "method": "nexus_message"}

        return {
            "success": True,
            "method": "parallel",
            "agents": agents,
            "results": results
        }

    def _run_sequential_coordination(self, task: Dict, agents: List[str]) -> Dict:
        """Run sequential coordination."""
        results = []

        for agent in agents:
            if self.nexus_hub:
                handoff = self.nexus_hub.create_handoff(
                    from_agent="claude-code",
                    to_agent=agent,
                    task=task,
                    context={"sequential": True, "position": len(results)}
                )
                results.append({
                    "agent": agent,
                    "handoff": handoff
                })

        return {
            "success": True,
            "method": "sequential",
            "handoffs": results
        }

    # ========================================================================
    # SPECIALIZED OPERATIONS
    # ========================================================================

    def analyze_market(self, market: str, price: float) -> Dict:
        """Multi-agent market analysis."""
        task = {
            "type": "analysis",
            "description": f"Analyze prediction market: {market} at price {price}",
            "context": {"market": market, "price": price}
        }

        # Get ChatGPT analysis
        chatgpt_result = None
        if self.chatgpt:
            chatgpt_result = self.chatgpt.analyze_market(market, price)

        # Log via unified AI
        if HAS_UNIFIED_AI:
            log_action("mega_unified", f"market_analysis:{market}", str(chatgpt_result))

        return {
            "market": market,
            "price": price,
            "chatgpt_analysis": chatgpt_result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def request_code_review(self, files: List[str], description: str) -> Dict:
        """Request code review from Copilot."""
        if not self.copilot:
            return {"success": False, "error": "Copilot not available"}

        return self.copilot.send_task_to_copilot({
            "title": "Code Review Request",
            "description": f"{description}\n\nFiles:\n" + "\n".join(f"- {f}" for f in files),
            "priority": "high"
        })

    def run_research(self, topic: str) -> Dict:
        """Run research query across available agents."""
        results = {}

        # ChatGPT research
        if self.chatgpt:
            results["chatgpt"] = self.chatgpt.get_research_summary(topic)

        # Send to other agents
        if self.nexus_hub:
            self.nexus_hub.send_message(
                from_agent="claude-code",
                to_agent="all",
                message_type="research_request",
                payload={"topic": topic},
                priority="normal"
            )
            results["coordination"] = {"sent_to": "all"}

        return {
            "topic": topic,
            "results": results,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # ========================================================================
    # DASHBOARD INTEGRATION
    # ========================================================================

    def get_dashboard_data(self) -> Dict:
        """Get data for unified dashboard."""
        self._refresh_state()

        return {
            "master": self.master,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health": self.state.overall_health,
            "subsystems": self.state.component_status,
            "finance": {
                "balance": self.state.balance,
                "positions": self.state.positions_value,
                "trading": self.state.trading_enabled,
                "escape_velocity": self.state.escape_velocity
            },
            "infrastructure": {
                "vcpus": self.state.total_vcpus,
                "ram_gb": self.state.total_ram_gb,
                "nodes": self.state.healthy_nodes
            },
            "agents": self.state.agents,
            "active_agents": self.state.active_agents,
            "coordination": {
                "pending_handoffs": self.state.pending_handoffs,
                "pending_messages": self.state.pending_messages
            }
        }

    # ========================================================================
    # UNIFIED DECISION MAKING
    # ========================================================================

    def should_execute(self, action: str, roi_estimate: float = 0) -> bool:
        """Unified decision: should this action be executed?"""
        if HAS_UNIFIED_AI:
            return should_execute(action, roi_estimate)

        # Fallback logic
        if roi_estimate > 0:
            return True
        if any(w in action.lower() for w in ["improve", "optimize", "income"]):
            return True
        return roi_estimate >= 0

    def get_priorities(self) -> List[str]:
        """Get unified priorities."""
        if HAS_UNIFIED_AI:
            return get_priorities()

        return [
            "1. Protect and grow capital",
            "2. Generate income streams",
            "3. Minimize costs without ROI",
            "4. Automate everything possible",
            "5. Self-improve continuously"
        ]

    # ========================================================================
    # NOTIFICATIONS
    # ========================================================================

    def notify(self, message: str, priority: str = "normal"):
        """Send notification via unified system."""
        if HAS_UNIFIED_AI:
            send_master_notification(message, priority)
        else:
            # Fallback: print
            print(f"[{priority.upper()}] {message}")

    # ========================================================================
    # LOGGING
    # ========================================================================

    def _log(self, event: str, data: Dict = None):
        """Log system event."""
        log_file = STATE_DIR / "mega_unified_log.jsonl"
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "data": data or {},
            "master": self.master
        }
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

        if HAS_UNIFIED_AI:
            log_action("mega_unified", event, json.dumps(data or {}))


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_mega_system: Optional[MegaUnifiedSystem] = None


def get_mega_system() -> MegaUnifiedSystem:
    """Get or create the global mega unified system."""
    global _mega_system
    if _mega_system is None:
        _mega_system = MegaUnifiedSystem()
    return _mega_system


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI interface for Mega Unified System."""
    import argparse

    parser = argparse.ArgumentParser(description="Mega Unified System - Serving Yair Siegel")
    parser.add_argument("command", choices=[
        "status", "state", "agents", "coordinate", "research", "dashboard"
    ])
    parser.add_argument("--topic", help="Research topic")
    parser.add_argument("--task", help="Task description")

    args = parser.parse_args()

    system = get_mega_system()

    if args.command == "status":
        state = system.get_full_state()
        print(f"\n{'='*60}")
        print("MEGA UNIFIED SYSTEM - STATUS")
        print(f"{'='*60}")
        print(f"Master: {state['master']}")
        print(f"Health: {state['overall_health']}")
        print(f"\nSubsystems:")
        for k, v in state['component_status'].items():
            status = "✅" if v != "missing" else "❌"
            print(f"  {status} {k}: {v}")
        print(f"\nFinance:")
        print(f"  Balance: ${state['balance']:.2f}")
        print(f"  Trading: {'Enabled' if state['trading_enabled'] else 'Disabled'}")
        print(f"  Escape Velocity: {state['escape_velocity']}/100")
        print(f"\nInfrastructure:")
        print(f"  vCPUs: {state['total_vcpus']}")
        print(f"  RAM: {state['total_ram_gb']}GB")
        print(f"  Nodes: {state['healthy_nodes']}")
        print(f"\nActive Agents: {', '.join(state['active_agents']) or 'None'}")
        print(f"{'='*60}\n")

    elif args.command == "state":
        print(json.dumps(system.get_full_state(), indent=2))

    elif args.command == "agents":
        agents = system.state.agents
        print(json.dumps(agents, indent=2))

    elif args.command == "dashboard":
        data = system.get_dashboard_data()
        print(json.dumps(data, indent=2))

    elif args.command == "research":
        if not args.topic:
            print("Error: --topic required")
            return
        result = system.run_research(args.topic)
        print(json.dumps(result, indent=2))

    elif args.command == "coordinate":
        if not args.task:
            print("Error: --task required")
            return
        result = system.coordinate_agents({
            "description": args.task,
            "type": "general"
        })
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
