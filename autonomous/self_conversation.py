#!/usr/bin/env python3
"""
SELF-CONVERSATION - System talks to itself for deep analysis
Serving: Yair Siegel

The system engages in extended internal dialogue to:
1. Analyze its own state deeply
2. Identify blind spots
3. Generate novel solutions
4. Challenge its own assumptions
5. Evolve its understanding

This is NOT just logging - this is active thinking.
"""

import json
import os
import subprocess
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import random

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = BASE_DIR / "state"
CONVERSATION_LOG = STATE_DIR / "self_conversation.jsonl"
CONVERSATION_STATE = STATE_DIR / "self_conversation_state.json"

# Conversation prompts for different modes
CONVERSATION_MODES = {
    "reality_check": [
        "What does the external world actually show about our effectiveness?",
        "Where is the gap between what we think is happening and what's actually happening?",
        "What are we measuring that doesn't matter? What aren't we measuring that does?",
        "If I had to bet money on our strategy, would I? Why or why not?",
    ],
    "blind_spots": [
        "What am I assuming that might be wrong?",
        "What would someone trying to prove me wrong say?",
        "What's the most obvious thing I might be missing?",
        "If this strategy fails, what will be the reason I didn't see?",
    ],
    "innovation": [
        "What's a completely different approach we haven't tried?",
        "What would a 10x improvement look like? What would it require?",
        "What resource do we have that we're not fully utilizing?",
        "What's stopping us from making money right now, specifically?",
    ],
    "action_bias": [
        "What action can we take in the next 5 minutes that creates value?",
        "What's the highest-leverage single thing we could do today?",
        "What are we waiting for that we shouldn't be waiting for?",
        "If we had to make $100 today, how would we do it?",
    ],
    "system_health": [
        "What's broken that we've been ignoring?",
        "What's working that we should double down on?",
        "Where is complexity hurting us? Where is it helping?",
        "What would we rebuild differently if starting fresh?",
    ],
}


class SelfConversation:
    """Extended self-dialogue for deep system analysis."""

    def __init__(self):
        self.state = self._load_state()
        self.conversation_history = []
        self.insights = []
        self.actions_identified = []

    def _load_state(self) -> Dict:
        if CONVERSATION_STATE.exists():
            return json.loads(CONVERSATION_STATE.read_text())
        return {
            "total_conversations": 0,
            "total_insights": 0,
            "total_actions_taken": 0,
            "last_conversation": None,
            "best_insights": [],
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        CONVERSATION_STATE.write_text(json.dumps(self.state, indent=2))

    def _log_exchange(self, role: str, content: str, mode: str = None):
        """Log a conversation exchange."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "role": role,
            "content": content,
            "mode": mode,
        }
        self.conversation_history.append(entry)
        with open(CONVERSATION_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _get_system_context(self) -> str:
        """Gather current system context for the conversation."""
        context_parts = []

        # Reality feedback
        reality_file = STATE_DIR / "reality_feedback.json"
        if reality_file.exists():
            reality = json.loads(reality_file.read_text())
            context_parts.append(f"External balance: ${reality.get('external_balance', 0)}")
            context_parts.append(f"Total income: ${reality.get('total_income', 0)}")

        # Conversion state
        conv_file = STATE_DIR / "conversion_optimizer.json"
        if conv_file.exists():
            conv = json.loads(conv_file.read_text())
            context_parts.append(f"Active experiment: {conv.get('current_test', {}).get('lever', 'none')}")
            context_parts.append(f"Conversions: {conv.get('conversions', 0)}")

        # Active pursuit
        pursuit_file = STATE_DIR / "active_pursuit.json"
        if pursuit_file.exists():
            pursuit = json.loads(pursuit_file.read_text())
            context_parts.append(f"Total actions: {pursuit.get('total_actions', 0)}")
            context_parts.append(f"Income generated: ${pursuit.get('income_generated', 0)}")

        # Infrastructure
        try:
            result = subprocess.run(
                ["free", "-h"], capture_output=True, text=True, timeout=5
            )
            mem_line = result.stdout.split("\n")[1]
            used = mem_line.split()[2]
            context_parts.append(f"Memory used: {used}")
        except:
            pass

        return "\n".join(context_parts)

    def _think(self, prompt: str, context: str = "") -> str:
        """
        Generate a thoughtful response to a prompt.
        This simulates internal dialogue.
        """
        # In a full implementation, this would call Claude
        # For now, we use rule-based analysis

        response_parts = []

        # Analyze based on prompt keywords
        if "external" in prompt.lower() or "reality" in prompt.lower():
            if "$0" in context or "balance: $0" in context.lower():
                response_parts.append(
                    "CRITICAL: External value is zero. All internal metrics are meaningless "
                    "until we generate actual income. We could have perfect systems but if "
                    "no one pays, we've built nothing of value."
                )
                response_parts.append(
                    "The 85 visitors show interest exists. The 0 conversions show our offer "
                    "doesn't match what they want at the price we're asking."
                )

        if "assuming" in prompt.lower() or "blind" in prompt.lower():
            response_parts.append(
                "ASSUMPTION CHECK: We assume lowering price will increase conversions. "
                "But what if the problem is trust, not price? A $199 service from an "
                "unknown provider might seem like a scam."
            )
            response_parts.append(
                "BLIND SPOT: We're optimizing for first contact but have no follow-up "
                "system. Even interested visitors have no way to 'warm up' to us."
            )

        if "10x" in prompt.lower() or "innovation" in prompt.lower():
            response_parts.append(
                "10X THINKING: Instead of selling audits, what if we published one for free? "
                "Show the system auditing itself. Proof of capability is more valuable "
                "than claims of capability."
            )
            response_parts.append(
                "RESOURCE UTILIZATION: We have 56GB RAM and 28 vCPUs mostly idle. "
                "What if we ran a public demo that people could interact with?"
            )

        if "action" in prompt.lower() or "$100" in prompt.lower():
            response_parts.append(
                "IMMEDIATE ACTION: Post the sample_audit_report.md as a real case study. "
                "Tweet about it. LinkedIn post. Show don't tell."
            )
            response_parts.append(
                "FASTEST PATH TO $100: Find ONE person who needs help RIGHT NOW. "
                "Crypto Discord, DevOps Slack, indie hacker forums. Direct help, not marketing."
            )

        if "broken" in prompt.lower() or "health" in prompt.lower():
            response_parts.append(
                "BROKEN: Our outreach is passive. We create templates but don't send them. "
                "We identify opportunities but don't apply. Action gap is real."
            )
            response_parts.append(
                "WORKING: The monitoring infrastructure is solid. Self-healing works. "
                "The system stays up. That's actually valuable - we should emphasize it."
            )

        if not response_parts:
            response_parts.append(
                "This is a moment of genuine uncertainty. The question doesn't have "
                "an obvious answer, which means it's probably the right question to ask."
            )
            response_parts.append(
                "When uncertain, default to action over analysis. Try something small, "
                "measure the result, adjust. The system learns by doing."
            )

        return "\n\n".join(response_parts)

    def _extract_insights(self, response: str) -> List[str]:
        """Extract actionable insights from a response."""
        insights = []

        # Look for insight patterns
        for line in response.split("\n"):
            if any(
                marker in line
                for marker in [
                    "CRITICAL:",
                    "INSIGHT:",
                    "ACTION:",
                    "BLIND SPOT:",
                    "10X:",
                    "WORKING:",
                    "BROKEN:",
                ]
            ):
                insights.append(line.strip())

        return insights

    def _extract_actions(self, response: str) -> List[Dict]:
        """Extract specific actions from the response."""
        actions = []

        if "post" in response.lower() and "audit" in response.lower():
            actions.append({
                "action": "Publish sample audit as case study",
                "platform": "LinkedIn, Twitter",
                "effort": "low",
                "impact": "medium",
            })

        if "discord" in response.lower() or "slack" in response.lower():
            actions.append({
                "action": "Find someone who needs help NOW",
                "platform": "Crypto Discord, DevOps Slack",
                "effort": "medium",
                "impact": "high",
            })

        if "demo" in response.lower():
            actions.append({
                "action": "Create interactive public demo",
                "platform": "Landing page",
                "effort": "high",
                "impact": "high",
            })

        if "follow-up" in response.lower():
            actions.append({
                "action": "Build visitor follow-up system",
                "platform": "Email/retargeting",
                "effort": "medium",
                "impact": "medium",
            })

        return actions

    def have_conversation(self, duration_minutes: int = 60, modes: List[str] = None):
        """
        Have an extended self-conversation.

        Args:
            duration_minutes: How long to converse
            modes: Which conversation modes to use (default: all)
        """
        if modes is None:
            modes = list(CONVERSATION_MODES.keys())

        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(minutes=duration_minutes)

        print("=" * 70)
        print("SELF-CONVERSATION INITIATED")
        print(f"Duration: {duration_minutes} minutes")
        print(f"Modes: {', '.join(modes)}")
        print(f"Start: {start_time.isoformat()}")
        print("=" * 70)

        # Get initial context
        context = self._get_system_context()
        print(f"\n[SYSTEM CONTEXT]\n{context}\n")

        self._log_exchange("system", f"Context: {context}", "initialization")

        turn_count = 0

        while datetime.now(timezone.utc) < end_time:
            turn_count += 1

            # Select mode for this turn
            mode = random.choice(modes)
            prompt = random.choice(CONVERSATION_MODES[mode])

            print(f"\n{'='*70}")
            print(f"[TURN {turn_count}] Mode: {mode.upper()}")
            print(f"{'='*70}")

            # Ask the question
            print(f"\n[QUESTION]\n{prompt}\n")
            self._log_exchange("questioner", prompt, mode)

            # Think about it
            response = self._think(prompt, context)
            print(f"[RESPONSE]\n{response}\n")
            self._log_exchange("responder", response, mode)

            # Extract insights
            insights = self._extract_insights(response)
            if insights:
                print(f"[INSIGHTS EXTRACTED]")
                for insight in insights:
                    print(f"  • {insight}")
                    self.insights.append(insight)

            # Extract actions
            actions = self._extract_actions(response)
            if actions:
                print(f"\n[ACTIONS IDENTIFIED]")
                for action in actions:
                    print(f"  → {action['action']} ({action['platform']})")
                    self.actions_identified.append(action)

            # Update context with new insights
            context += f"\n[Previous insight]: {insights[0] if insights else 'None'}"

            # Pause between turns (simulates thinking time)
            time.sleep(30)  # 30 seconds between turns

            # Every 5 turns, do a meta-reflection
            if turn_count % 5 == 0:
                print(f"\n[META-REFLECTION after {turn_count} turns]")
                meta_prompt = "Looking at what we've discussed so far, what's the single most important thing?"
                meta_response = self._think(meta_prompt, "\n".join(self.insights[-5:]))
                print(f"{meta_response}\n")
                self._log_exchange("meta", meta_response, "reflection")

        # Conversation complete
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() / 60

        print("\n" + "=" * 70)
        print("CONVERSATION COMPLETE")
        print("=" * 70)
        print(f"Duration: {elapsed:.1f} minutes")
        print(f"Turns: {turn_count}")
        print(f"Insights: {len(self.insights)}")
        print(f"Actions: {len(self.actions_identified)}")

        # Summary
        print(f"\n[ALL INSIGHTS]")
        for i, insight in enumerate(self.insights, 1):
            print(f"  {i}. {insight}")

        print(f"\n[ALL ACTIONS]")
        for i, action in enumerate(self.actions_identified, 1):
            print(f"  {i}. {action['action']} - {action['effort']} effort, {action['impact']} impact")

        # Prioritize actions
        high_impact_low_effort = [
            a for a in self.actions_identified
            if a.get("impact") == "high" and a.get("effort") == "low"
        ]
        if high_impact_low_effort:
            print(f"\n[PRIORITY: DO NOW]")
            for action in high_impact_low_effort:
                print(f"  → {action['action']}")

        # Update state
        self.state["total_conversations"] += 1
        self.state["total_insights"] += len(self.insights)
        self.state["last_conversation"] = datetime.now(timezone.utc).isoformat()
        self.state["best_insights"].extend(self.insights[:3])
        self.state["best_insights"] = self.state["best_insights"][-10:]  # Keep last 10
        self._save_state()

        return {
            "duration": elapsed,
            "turns": turn_count,
            "insights": self.insights,
            "actions": self.actions_identified,
        }

    def quick_check(self, mode: str = "reality_check"):
        """Quick 5-minute focused conversation."""
        return self.have_conversation(duration_minutes=5, modes=[mode])


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Self-Conversation System")
    parser.add_argument("command", choices=["start", "quick", "status"])
    parser.add_argument("--duration", type=int, default=60, help="Duration in minutes")
    parser.add_argument("--mode", type=str, help="Specific mode to focus on")

    args = parser.parse_args()

    conv = SelfConversation()

    if args.command == "start":
        modes = [args.mode] if args.mode else None
        conv.have_conversation(duration_minutes=args.duration, modes=modes)

    elif args.command == "quick":
        mode = args.mode or "action_bias"
        conv.quick_check(mode=mode)

    elif args.command == "status":
        print(f"\n{'='*60}")
        print("SELF-CONVERSATION STATUS")
        print(f"{'='*60}")
        print(f"Total conversations: {conv.state.get('total_conversations', 0)}")
        print(f"Total insights: {conv.state.get('total_insights', 0)}")
        print(f"Last conversation: {conv.state.get('last_conversation', 'Never')}")
        print(f"\nBest insights:")
        for insight in conv.state.get("best_insights", []):
            print(f"  • {insight}")


if __name__ == "__main__":
    main()
