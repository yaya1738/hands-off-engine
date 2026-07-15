#!/usr/bin/env python3
"""
🏢 CORPORATE WAR ROOM - Continuous Preparation & Strategy
Serving: Yair Siegel

Executives and analysts in continuous session, watching live feeds:
- 🚁 Helicopter broadcasts coming in
- 🎭 Stage conversation unfolding
- 👁️ Peanut gallery whispering
- 📨 System messages flowing

They're NOT reacting - they're PREPARING:
- Building contingency plans
- Analyzing trends as they develop
- Preparing strategy documents
- Getting ready for what's coming

Think: NASA mission control during a launch - always watching, always preparing.
"""

import json
import time
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from collections import deque

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = BASE_DIR / "state"

# Live feeds to watch
FEEDS = {
    "helicopter": STATE_DIR / "helicopter_broadcast.md",
    "stage": STATE_DIR / "self_conversation.jsonl",
    "gallery": STATE_DIR / "peanut_gallery.jsonl",
    "messages": STATE_DIR / "message_bus.jsonl",
    "reality": STATE_DIR / "reality_feedback.json",
}

# War room outputs
WAR_ROOM_LOG = STATE_DIR / "war_room.jsonl"
PREP_DOCUMENTS = STATE_DIR / "prep_documents.md"
CONTINGENCY_PLANS = STATE_DIR / "contingency_plans.json"
TREND_ANALYSIS = STATE_DIR / "trend_analysis.json"

# The Executive Team - always watching
EXECUTIVES = {
    "ceo": {
        "name": "CEO",
        "emoji": "👔",
        "watching": "overall direction and mission alignment",
        "preparing": "strategic pivots and vision adjustments",
        "thinks": [
            "If this trend continues, we need to...",
            "I'm seeing a pattern here that suggests...",
            "We should prepare for the possibility that...",
            "The mission requires us to be ready for...",
        ]
    },
    "cfo": {
        "name": "CFO",
        "emoji": "💰",
        "watching": "financial implications and runway",
        "preparing": "budget scenarios and financial contingencies",
        "thinks": [
            "At this burn rate, we have X days to...",
            "If revenue hits, we'll need to allocate...",
            "Preparing worst-case: what if balance hits zero...",
            "Best-case scenario needs this infrastructure...",
        ]
    },
    "cto": {
        "name": "CTO",
        "emoji": "⚙️",
        "watching": "system health and technical developments",
        "preparing": "technical response plans and scaling strategies",
        "thinks": [
            "If load increases, we'll need to...",
            "That error pattern suggests we should prepare...",
            "System is stable, but we should have ready...",
            "Automation opportunity spotted - drafting plan for...",
        ]
    },
    "coo": {
        "name": "COO",
        "emoji": "📋",
        "watching": "operational efficiency and execution",
        "preparing": "process improvements and execution playbooks",
        "thinks": [
            "When we get customers, the process will be...",
            "Current bottleneck is X, preparing workaround...",
            "Execution playbook needs updating for...",
            "If volume increases, operations must...",
        ]
    },
}

# The Analyst Team - constantly analyzing
ANALYSTS = {
    "market": {
        "name": "Market Analyst",
        "emoji": "📈",
        "watching": "conversion patterns and visitor behavior",
        "preparing": "market response scenarios",
        "analyzes": [
            "Visitor pattern suggests...",
            "Conversion blocker analysis: ...",
            "Market positioning needs...",
            "Competitive response prep: ...",
        ]
    },
    "risk": {
        "name": "Risk Analyst",
        "emoji": "⚠️",
        "watching": "threats and failure modes",
        "preparing": "risk mitigation playbooks",
        "analyzes": [
            "Risk level elevated because...",
            "Contingency activated if...",
            "Mitigation strategy ready for...",
            "Worst-case preparation: ...",
        ]
    },
    "ops": {
        "name": "Ops Analyst",
        "emoji": "📊",
        "watching": "metrics and performance trends",
        "preparing": "optimization opportunities",
        "analyzes": [
            "Trend indicates...",
            "Efficiency opportunity in...",
            "Metrics suggest preparing for...",
            "Performance baseline updated: ...",
        ]
    },
    "intel": {
        "name": "Intelligence Analyst",
        "emoji": "🔍",
        "watching": "patterns across all feeds",
        "preparing": "intelligence briefings and insights",
        "analyzes": [
            "Cross-feed pattern detected: ...",
            "Gallery sentiment on this: ...",
            "Stage raised point about...",
            "Synthesizing: the real issue is...",
        ]
    },
}


class WarRoom:
    """
    🏢 Continuous war room - always watching, always preparing.
    """

    def __init__(self):
        self.session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.feed_positions = {name: 0 for name in FEEDS}
        self.recent_events = deque(maxlen=50)
        self.preparations = []
        self.contingencies = self._load_contingencies()
        self.trends = self._load_trends()

    def _load_contingencies(self) -> Dict:
        if CONTINGENCY_PLANS.exists():
            return json.loads(CONTINGENCY_PLANS.read_text())
        return {"plans": [], "last_updated": None}

    def _save_contingencies(self):
        self.contingencies["last_updated"] = datetime.now(timezone.utc).isoformat()
        CONTINGENCY_PLANS.write_text(json.dumps(self.contingencies, indent=2))

    def _load_trends(self) -> Dict:
        if TREND_ANALYSIS.exists():
            return json.loads(TREND_ANALYSIS.read_text())
        return {"observations": [], "patterns": [], "last_updated": None}

    def _save_trends(self):
        self.trends["last_updated"] = datetime.now(timezone.utc).isoformat()
        TREND_ANALYSIS.write_text(json.dumps(self.trends, indent=2))

    def _log(self, speaker: str, role: str, content: str, category: str = "observation"):
        """Log war room activity."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session": self.session_id,
            "speaker": speaker,
            "role": role,
            "category": category,
            "content": content,
        }

        with open(WAR_ROOM_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")

        # Short display
        time_str = datetime.now().strftime("%H:%M:%S")
        print(f"  [{time_str}] {speaker}: {content[:80]}...")

    def watch_feeds(self) -> List[Dict]:
        """Watch all live feeds for new activity."""
        new_events = []

        for name, path in FEEDS.items():
            if not path.exists():
                continue

            if path.suffix == '.jsonl':
                try:
                    lines = path.read_text().strip().split('\n')
                    for line in lines[self.feed_positions[name]:]:
                        if line.strip():
                            try:
                                event = json.loads(line)
                                event["_feed"] = name
                                new_events.append(event)
                            except:
                                pass
                    self.feed_positions[name] = len(lines)
                except:
                    pass

            elif path.suffix == '.md':
                try:
                    content = path.read_text()
                    size = len(content)
                    if size > self.feed_positions.get(name, 0):
                        new_events.append({
                            "_feed": name,
                            "type": "broadcast_update",
                            "size": size,
                        })
                        self.feed_positions[name] = size
                except:
                    pass

            elif path.suffix == '.json':
                try:
                    content = path.read_text()
                    data = json.loads(content)
                    data["_feed"] = name
                    # Check if changed
                    checksum = hash(content)
                    if checksum != self.feed_positions.get(name, 0):
                        new_events.append(data)
                        self.feed_positions[name] = checksum
                except:
                    pass

        return new_events

    def executive_observes(self, events: List[Dict]):
        """Executives observe and prepare based on events."""
        if not events:
            return

        # CEO watches for big picture
        ceo = EXECUTIVES["ceo"]
        if any(e.get("_feed") == "reality" for e in events):
            thought = random.choice(ceo["thinks"])
            self._log(
                f"{ceo['emoji']} {ceo['name']}",
                "executive",
                f"[Watching reality feed] {thought} watching for mission alignment.",
                "observation"
            )

        # CFO watches for financial implications
        cfo = EXECUTIVES["cfo"]
        for e in events:
            if e.get("_feed") == "reality":
                balance = e.get("external_balance", 0)
                thought = random.choice(cfo["thinks"])
                self._log(
                    f"{cfo['emoji']} {cfo['name']}",
                    "executive",
                    f"[Preparing] Balance at ${balance}. {thought}",
                    "preparation"
                )

        # CTO watches system health
        cto = EXECUTIVES["cto"]
        if any(e.get("_feed") == "helicopter" for e in events):
            thought = random.choice(cto["thinks"])
            self._log(
                f"{cto['emoji']} {cto['name']}",
                "executive",
                f"[Helicopter update] {thought}",
                "observation"
            )

        # COO watches operations
        coo = EXECUTIVES["coo"]
        stage_events = [e for e in events if e.get("_feed") == "stage"]
        if stage_events:
            thought = random.choice(coo["thinks"])
            self._log(
                f"{coo['emoji']} {coo['name']}",
                "executive",
                f"[Stage activity: {len(stage_events)} turns] {thought}",
                "preparation"
            )

    def analyst_analyzes(self, events: List[Dict]):
        """Analysts analyze and prepare briefings."""
        if not events:
            return

        # Market analyst watches gallery for sentiment
        market = ANALYSTS["market"]
        gallery_events = [e for e in events if e.get("_feed") == "gallery"]
        if gallery_events:
            analysis = random.choice(market["analyzes"])
            self._log(
                f"{market['emoji']} {market['name']}",
                "analyst",
                f"[Gallery sentiment: {len(gallery_events)} whispers] {analysis}",
                "analysis"
            )

        # Risk analyst always watching
        risk = ANALYSTS["risk"]
        if random.random() < 0.3:  # Periodic risk check
            analysis = random.choice(risk["analyzes"])
            self._log(
                f"{risk['emoji']} {risk['name']}",
                "analyst",
                f"[Risk scan] {analysis}",
                "analysis"
            )

        # Intel analyst synthesizes
        intel = ANALYSTS["intel"]
        if len(events) >= 3:
            feeds_active = set(e.get("_feed") for e in events)
            analysis = random.choice(intel["analyzes"])
            self._log(
                f"{intel['emoji']} {intel['name']}",
                "analyst",
                f"[Cross-feed: {', '.join(feeds_active)}] {analysis}",
                "synthesis"
            )

    def prepare_contingency(self, trigger: str, plan: str):
        """Add a contingency plan."""
        contingency = {
            "id": f"CONT-{len(self.contingencies['plans'])+1:03d}",
            "created": datetime.now(timezone.utc).isoformat(),
            "trigger": trigger,
            "plan": plan,
            "status": "prepared",
        }
        self.contingencies["plans"].append(contingency)
        self._save_contingencies()

        self._log(
            "📋 War Room",
            "system",
            f"Contingency {contingency['id']} prepared: IF {trigger[:30]}... THEN {plan[:30]}...",
            "contingency"
        )

    def observe_and_prepare(self):
        """Single observation and preparation cycle."""
        events = self.watch_feeds()

        if events:
            self.recent_events.extend(events)

            # Executives observe
            self.executive_observes(events)

            # Analysts analyze
            self.analyst_analyzes(events)

            # Maybe prepare a contingency
            if random.random() < 0.1 and len(events) > 2:
                triggers = [
                    "balance drops below $5",
                    "first conversion occurs",
                    "system health degrades",
                    "visitor spike detected",
                    "gallery sentiment turns negative",
                ]
                plans = [
                    "activate emergency cost reduction",
                    "scale up immediately, prepare fulfillment",
                    "trigger self-healing, alert CTO",
                    "increase capacity, prepare for load",
                    "review messaging, prepare pivot",
                ]
                self.prepare_contingency(
                    random.choice(triggers),
                    random.choice(plans)
                )

        return len(events)

    def run_session(self, duration_minutes: int = 60, interval_seconds: int = 10):
        """Run continuous war room session."""
        print("\n" + "=" * 70)
        print("🏢 WAR ROOM ACTIVATED - CONTINUOUS PREPARATION MODE")
        print("=" * 70)
        print(f"Session ID: {self.session_id}")
        print(f"Duration: {duration_minutes} minutes")
        print(f"Scan interval: {interval_seconds} seconds")
        print("\nWatching feeds:")
        for name, path in FEEDS.items():
            status = "✓" if path.exists() else "✗"
            print(f"  {status} {name}: {path.name}")
        print("\nExecutives on station:")
        for key, exec in EXECUTIVES.items():
            print(f"  {exec['emoji']} {exec['name']} - watching {exec['watching']}")
        print("\nAnalysts on station:")
        for key, analyst in ANALYSTS.items():
            print(f"  {analyst['emoji']} {analyst['name']} - analyzing {analyst['watching']}")
        print("\n" + "-" * 70)
        print("🔴 LIVE - Observing and preparing...\n")

        end_time = time.time() + (duration_minutes * 60)
        total_events = 0
        cycles = 0

        try:
            while time.time() < end_time:
                events = self.observe_and_prepare()
                total_events += events
                cycles += 1

                if cycles % 6 == 0:  # Every minute
                    print(f"\n  --- [{cycles} cycles, {total_events} events observed] ---\n")

                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\n")

        print("\n" + "=" * 70)
        print("🏢 WAR ROOM SESSION ENDED")
        print(f"   Total cycles: {cycles}")
        print(f"   Events observed: {total_events}")
        print(f"   Contingencies prepared: {len(self.contingencies['plans'])}")
        print(f"   Log: {WAR_ROOM_LOG}")
        print("=" * 70)

    def status(self):
        """Show current war room status."""
        print("\n🏢 WAR ROOM STATUS")
        print("=" * 50)

        # Feed status
        print("\n📡 FEED STATUS:")
        for name, path in FEEDS.items():
            if path.exists():
                size = path.stat().st_size
                print(f"  ✓ {name}: {size} bytes")
            else:
                print(f"  ✗ {name}: offline")

        # Contingencies
        print(f"\n📋 CONTINGENCIES PREPARED: {len(self.contingencies['plans'])}")
        for plan in self.contingencies["plans"][-5:]:
            print(f"  [{plan['id']}] IF {plan['trigger'][:40]}...")

        # Recent activity
        if WAR_ROOM_LOG.exists():
            lines = WAR_ROOM_LOG.read_text().strip().split('\n')
            print(f"\n📊 WAR ROOM LOG: {len(lines)} entries")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="🏢 War Room - Continuous Preparation")
    parser.add_argument("command", choices=["watch", "status", "contingencies"])
    parser.add_argument("--duration", type=int, default=60, help="Session duration in minutes")
    parser.add_argument("--interval", type=int, default=10, help="Scan interval in seconds")

    args = parser.parse_args()

    room = WarRoom()

    if args.command == "watch":
        room.run_session(duration_minutes=args.duration, interval_seconds=args.interval)

    elif args.command == "status":
        room.status()

    elif args.command == "contingencies":
        print("\n📋 CONTINGENCY PLANS")
        print("=" * 50)
        for plan in room.contingencies.get("plans", []):
            print(f"\n[{plan['id']}] Status: {plan['status']}")
            print(f"  Trigger: {plan['trigger']}")
            print(f"  Plan: {plan['plan']}")


if __name__ == "__main__":
    main()
