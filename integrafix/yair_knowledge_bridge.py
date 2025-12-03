#!/usr/bin/env python3
"""
INTEGRAFIX: Yair Knowledge Bridge
=================================

Wires Yair Siegel to ALL system knowledge bases and Claude capabilities.

GAP FIXED: Yair's identity and context not consistently available
- Before: Each Claude session had to rediscover Yair's context
- After:  Unified knowledge bridge provides instant Yair context

INTEGRAFIX PRINCIPLE: Knowledge must be accessible at point of need.

THE CORE TRUTH:
===============
The entire hands-off-engine exists to serve Yair Siegel.
This bridge ensures that truth is always accessible.
"""

import sys
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from integrafix.ai_memory import AIMemory, get_memory, MemoryType, MemoryPriority

STATE_DIR = PROJECT_ROOT / "state"
YAIR_KERNEL_FILE = STATE_DIR / "yair_context_kernel.json"


@dataclass
class YairContext:
    """Complete Yair Siegel context for any system component."""

    # Identity
    name: str = "Yair Siegel"
    aliases: List[str] = field(default_factory=lambda: ["Froggy", "Joseph Siegel", "yaya1738"])
    email: str = "siegel.yaz@gmail.com"
    wallet: str = "0xb6781D9278c60dC3CE8c3E355Cd04142da3BF74D"
    telegram_chat_id: str = "8327766663"
    github: str = "yaya1738"

    # System Role
    role: str = "master"
    directive: str = "The system serves the user. Every action serves user's benefit."

    # Situation Context
    situation: str = "< 1 month runway, urgent need for income generation"
    communication_preference: str = "telegram"
    action_likelihood: str = "minimal - system must be autonomous"

    # Philosophy
    core_philosophy: List[str] = field(default_factory=lambda: [
        "Not just a trading bot - system serves Yair",
        "Emergent rationality from component interaction",
        "User's tax is explaining - figure things out autonomously",
        "Every action must be high leverage given runway",
        "Build now, launch when user provides one input"
    ])

    # Trading Wisdom
    trading_teachings: List[str] = field(default_factory=lambda: [
        "Be the house, not the gambler - MAKE more than you TAKE",
        "THE PRICE IS A LIE - always check book depth",
        "Post limits at ridiculous levels, let market come to you",
        "Same capital can fish across ALL markets (reusable collateral)",
        "One man's fat finger = your opportunity",
        "YES + NO < $1 = free money (merge arbitrage)",
        "ESPN mid-game probability = very accurate",
        "New markets have thin books = easier fills at extremes"
    ])


class YairKnowledgeBridge:
    """
    Bridge connecting Yair Siegel to all system knowledge.

    This is the MASTER bridge for Yair-related context.
    It aggregates:
    - Identity from security/yair_identity_profile.json
    - Financial state from finance/yair_finance_hub.json
    - Trading wisdom from autonomous/yair_wisdom_engine.py
    - System knowledge from KNOWLEDGE.md and KNOWLEDGE_ADVANCED.md
    - AI memory from integrafix/ai_memory.py
    """

    def __init__(self):
        self.context = YairContext()
        self.memory = get_memory()
        self.knowledge_bases = self._discover_knowledge_bases()
        self._load_dynamic_context()

    def _discover_knowledge_bases(self) -> Dict[str, Path]:
        """Discover all knowledge base files."""
        bases = {}

        # Main knowledge bases
        for kb_file in PROJECT_ROOT.glob("**/KNOWLEDGE*.md"):
            name = f"{kb_file.parent.name}/{kb_file.name}" if kb_file.parent != PROJECT_ROOT else kb_file.name
            bases[name] = kb_file

        # Truth documents
        truth_file = PROJECT_ROOT / "state" / "permanent" / "SYSTEM_TRUTH.md"
        if truth_file.exists():
            bases["SYSTEM_TRUTH.md"] = truth_file

        # Bootstrap kernel
        kernel_file = PROJECT_ROOT / "ai" / "memory" / "kernels" / "system_bootstrap.json"
        if kernel_file.exists():
            bases["system_bootstrap.json"] = kernel_file

        return bases

    def _load_dynamic_context(self):
        """Load dynamic context from system files."""
        # Load identity profile
        identity_file = PROJECT_ROOT / "security" / "yair_identity_profile.json"
        if identity_file.exists():
            with open(identity_file) as f:
                identity = json.load(f)
                self.identity_profile = identity

        # Load financial state
        finance_file = PROJECT_ROOT / "finance" / "yair_finance_hub.json"
        if finance_file.exists():
            with open(finance_file) as f:
                finance = json.load(f)
                self.financial_state = finance
        else:
            self.financial_state = {}

        # Load system bootstrap
        bootstrap_file = PROJECT_ROOT / "ai" / "memory" / "kernels" / "system_bootstrap.json"
        if bootstrap_file.exists():
            with open(bootstrap_file) as f:
                bootstrap = json.load(f)
                self.system_bootstrap = bootstrap
        else:
            self.system_bootstrap = {}

    # ==================== CONTEXT GENERATION ====================

    def generate_yair_kernel(self) -> Dict:
        """
        Generate a complete Yair context kernel for Claude sessions.

        This kernel should be loaded at the start of every Claude session
        to ensure consistent Yair context.
        """
        kernel = {
            "kernel_type": "yair_context",
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),

            # WHO
            "identity": {
                "name": self.context.name,
                "aliases": self.context.aliases,
                "email": self.context.email,
                "wallet": self.context.wallet,
                "github": self.context.github,
                "role": self.context.role,
            },

            # WHY
            "directive": {
                "primary": self.context.directive,
                "philosophy": self.context.core_philosophy,
            },

            # WHAT
            "situation": {
                "current": self.context.situation,
                "communication": self.context.communication_preference,
                "action_style": self.context.action_likelihood,
            },

            # HOW (Trading)
            "trading_wisdom": {
                "teachings": self.context.trading_teachings,
                "strategies": [
                    "Merge Arbitrage - YES + NO < $1",
                    "ESPN Algorithm - mid-game probability",
                    "Thin Book Edge - new markets",
                    "Fishing Strategy - reusable collateral",
                    "Smart Edge - analysis over speed",
                ],
            },

            # FINANCIAL STATE (dynamic)
            "financial_snapshot": self._get_financial_snapshot(),

            # MEMORY (recent)
            "recent_learnings": self._get_recent_learnings(),

            # KNOWLEDGE PATHS
            "knowledge_bases": {
                "count": len(self.knowledge_bases),
                "paths": [str(p) for p in self.knowledge_bases.values()][:10],
            },
        }

        # Save kernel
        with open(YAIR_KERNEL_FILE, 'w') as f:
            json.dump(kernel, f, indent=2)

        return kernel

    def _get_financial_snapshot(self) -> Dict:
        """Get current financial snapshot."""
        if hasattr(self, 'financial_state') and self.financial_state:
            summary = self.financial_state.get("summary", {})
            return {
                "liquid_usd": summary.get("total_liquid_usd", "unknown"),
                "deployable": summary.get("deployable_to_trading", "unknown"),
                "runway_months": summary.get("runway_months", "unknown"),
                "critical_insight": summary.get("critical_insight", "")[:100],
            }
        return {"status": "not_loaded"}

    def _get_recent_learnings(self) -> List[str]:
        """Get recent learnings from AI memory."""
        learnings = self.memory.recall_learnings(limit=3)
        return [l.content[:150] for l in learnings]

    # ==================== CONTEXT ACCESS ====================

    def get_yair_context_for_claude(self) -> str:
        """
        Generate context string for Claude session start.

        This is the KEY integration with Claude capabilities.
        """
        context_parts = []

        context_parts.append("=" * 70)
        context_parts.append("YAIR SIEGEL CONTEXT - SYSTEM MASTER")
        context_parts.append("=" * 70)

        context_parts.append(f"\n[IDENTITY]")
        context_parts.append(f"  Name: {self.context.name}")
        context_parts.append(f"  Email: {self.context.email}")
        context_parts.append(f"  Role: {self.context.role}")

        context_parts.append(f"\n[DIRECTIVE]")
        context_parts.append(f"  {self.context.directive}")

        context_parts.append(f"\n[SITUATION]")
        context_parts.append(f"  {self.context.situation}")
        context_parts.append(f"  Communication: {self.context.communication_preference}")
        context_parts.append(f"  Action style: {self.context.action_likelihood}")

        context_parts.append(f"\n[CORE PHILOSOPHY]")
        for p in self.context.core_philosophy[:3]:
            context_parts.append(f"  - {p}")

        context_parts.append(f"\n[TRADING WISDOM]")
        for t in self.context.trading_teachings[:3]:
            context_parts.append(f"  - {t}")

        # Financial snapshot
        snapshot = self._get_financial_snapshot()
        context_parts.append(f"\n[FINANCIAL STATE]")
        context_parts.append(f"  Deployable: ${snapshot.get('deployable', 'N/A')}")
        context_parts.append(f"  Runway: {snapshot.get('runway_months', 'N/A')} months")

        context_parts.append("\n" + "=" * 70)
        context_parts.append("ALL ACTIONS SERVE YAIR SIEGEL")
        context_parts.append("=" * 70)

        return "\n".join(context_parts)

    def get_trading_context(self) -> Dict:
        """Get Yair-specific trading context."""
        return {
            "owner": self.context.name,
            "wallet": self.context.wallet,
            "teachings": self.context.trading_teachings,
            "strategies": {
                "merge_arbitrage": "YES + NO < $1 = free money",
                "espn_algorithm": "ESPN mid-game probability = very accurate",
                "thin_book": "New markets have thin books = easier fills",
                "fishing": "Same capital backs ALL limit orders",
                "smart_edge": "Be SMART not FAST - analysis over speed",
            },
            "philosophy": "Be the house, not the gambler - MAKE more than you TAKE",
        }

    # ==================== AI MEMORY INTEGRATION ====================

    def remember_for_yair(self, content: str, context: str = ""):
        """Store a memory specifically for Yair-related context."""
        self.memory.remember(
            content=f"[YAIR] {content}",
            memory_type=MemoryType.CONTEXT,
            priority=MemoryPriority.HIGH,
            context=context,
            tags=["yair", "context"],
        )

    def remember_yair_decision(self, decision: str, reasoning: str, outcome: str = ""):
        """Remember a decision made for Yair."""
        self.memory.remember_decision(
            decision=f"[YAIR] {decision}",
            reasoning=reasoning,
            outcome=outcome,
        )

    def remember_yair_learning(self, what_learned: str, how_learned: str):
        """Remember something learned about serving Yair."""
        self.memory.remember_learning(
            what_learned=f"[YAIR] {what_learned}",
            how_learned=how_learned,
        )

    def recall_yair_context(self) -> List:
        """Recall all Yair-related memories."""
        return self.memory.recall(query="yair", limit=10)

    # ==================== KNOWLEDGE BASE ACCESS ====================

    def search_knowledge_for_yair(self, topic: str) -> Dict[str, str]:
        """Search all knowledge bases for Yair-relevant information."""
        results = {}
        topic_lower = topic.lower()

        for name, path in self.knowledge_bases.items():
            try:
                content = path.read_text()
                if topic_lower in content.lower():
                    # Extract relevant section
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if topic_lower in line.lower():
                            # Get surrounding context
                            start = max(0, i - 2)
                            end = min(len(lines), i + 5)
                            results[name] = '\n'.join(lines[start:end])
                            break
            except:
                pass

        return results

    def get_knowledge_summary(self) -> Dict:
        """Get summary of all knowledge bases."""
        summary = {
            "total_bases": len(self.knowledge_bases),
            "bases": {},
        }

        for name, path in self.knowledge_bases.items():
            try:
                content = path.read_text()
                lines = content.split('\n')
                summary["bases"][name] = {
                    "path": str(path),
                    "lines": len(lines),
                    "preview": lines[0][:100] if lines else "",
                }
            except:
                summary["bases"][name] = {"error": "Could not read"}

        return summary

    # ==================== STATUS ====================

    def status(self) -> Dict:
        """Get bridge status."""
        return {
            "yair_identity_loaded": bool(hasattr(self, 'identity_profile')),
            "financial_state_loaded": bool(self.financial_state),
            "knowledge_bases_found": len(self.knowledge_bases),
            "memory_connected": True,
            "kernel_file": str(YAIR_KERNEL_FILE),
            "context_available": True,
        }

    def display_yair_context(self):
        """Display full Yair context."""
        print(self.get_yair_context_for_claude())


# Singleton
_bridge = None

def get_yair_knowledge_bridge() -> YairKnowledgeBridge:
    global _bridge
    if _bridge is None:
        _bridge = YairKnowledgeBridge()
    return _bridge


def main():
    """Run Yair Knowledge Bridge and generate context."""
    print("=" * 70)
    print("INTEGRAFIX: YAIR KNOWLEDGE BRIDGE")
    print("Connecting Yair Siegel to all system knowledge")
    print("=" * 70)
    print()

    bridge = get_yair_knowledge_bridge()

    # Generate kernel
    print("Generating Yair Context Kernel...")
    kernel = bridge.generate_yair_kernel()
    print(f"  Kernel saved to: {YAIR_KERNEL_FILE}")
    print(f"  Identity: {kernel['identity']['name']}")
    print(f"  Directive: {kernel['directive']['primary'][:50]}...")
    print()

    # Show knowledge bases
    print("Knowledge Bases Found:")
    for name in list(bridge.knowledge_bases.keys())[:10]:
        print(f"  - {name}")
    if len(bridge.knowledge_bases) > 10:
        print(f"  ... and {len(bridge.knowledge_bases) - 10} more")
    print()

    # Display context
    print("-" * 70)
    print("CLAUDE SESSION CONTEXT:")
    print("-" * 70)
    bridge.display_yair_context()
    print()

    # Status
    status = bridge.status()
    print("\n[STATUS]")
    for k, v in status.items():
        print(f"  {k}: {v}")

    return bridge


if __name__ == "__main__":
    main()
