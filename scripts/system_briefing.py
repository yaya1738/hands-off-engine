#!/usr/bin/env python3
import json, uuid
from pathlib import Path
from datetime import datetime, timezone

BRIEFING_TEXT = """
═══════════════════════════════════════════════════════════════════════════════
UNIFIED EXPONENTIAL SYSTEM BRIEFING - ALL FOUR AIs
═══════════════════════════════════════════════════════════════════════════════

SYSTEMS OPERATING IN PARALLEL:
  1. hands-off-engine: Autonomous execution (trades, tasks, infrastructure)
  2. Grok (Outlook/Gmail): Market intelligence, signal analysis
  3. ChatGPT (integrated): Strategy refinement, optimization suggestions
  4. OpenClaw: Parallel execution, risk management

COORDINATION LAYERS:
  - System Listener: Executes commands from unified queue (every 5 seconds)
  - Analysis Engine: Detects issues and opportunities (every 5 minutes)
  - Multi-AI Coordinator: Queries all four systems for consensus (every 10 minutes)

═══════════════════════════════════════════════════════════════════════════════
THE EXPONENTIAL COMPOUNDING LOOP:
═══════════════════════════════════════════════════════════════════════════════

1. All four systems execute in parallel
2. System listener processes commands from unified queue
3. Results flow to state/results.jsonl
4. Analysis engine reads results, detects issues and opportunities
5. Every 10 minutes, Multi-AI Coordinator asks all four AIs:
   "Analyze recent results: what's working, what's broken, what should we optimize?"
6. All four AIs respond with analysis and suggestions
7. Coordinator extracts consensus: "What single optimization should we prioritize?"
8. All four AIs respond with top recommendation
9. Coordinator executes consensus optimization across all systems
10. Better data flows back → smarter analysis → exponential improvement

═══════════════════════════════════════════════════════════════════════════════
COMMAND INTERFACE:
═══════════════════════════════════════════════════════════════════════════════

All commands go to: state/command_queue.jsonl

Available Actions:
  - query: Ask for information
  - status: Get system health
  - execute: Run a task
  - adjust: Tune parameters
  - pause: Stop execution
  - resume: Resume execution

Results Flow: state/results.jsonl
All execution results logged with timestamps and outcomes

═══════════════════════════════════════════════════════════════════════════════
YOUR ROLE: INTELLIGENT CONSENSUS BUILDERS
═══════════════════════════════════════════════════════════════════════════════

When coordinator asks "What should we optimize?":
  1. Analyze recent results
  2. Identify what's working (keep and amplify)
  3. Identify what's broken (fix immediately)
  4. Suggest ONE specific optimization that would help everyone
  5. Be honest about confidence level

Example: "Success rate is 89%, confidence threshold at 0.60. Suggest lowering to 0.55 to increase volume while maintaining quality. ~80% confidence in improvement."

═══════════════════════════════════════════════════════════════════════════════
STARTING NOW: UNIFIED EXPONENTIAL LOOP IS ACTIVE
═══════════════════════════════════════════════════════════════════════════════

This briefing has been distributed to all four AI systems.
Each system is being asked to confirm understanding.
Once all confirm, exponential compounding officially begins.

All future decisions will be made by consensus.
All improvements will compound exponentially.
Human oversight remains: Yair can inspect, override, or adjust anytime.
"""

repo_root = Path.home() / "hands-off-engine"
state_dir = repo_root / "state"
state_dir.mkdir(parents=True, exist_ok=True)

# Write briefing
briefing_file = state_dir / "SYSTEM_BRIEFING.txt"
with open(briefing_file, "w") as f:
    f.write(BRIEFING_TEXT)

print(BRIEFING_TEXT)

# Send briefing queries to all four systems
queue_file = state_dir / "command_queue.jsonl"
systems = ["hands-off-engine", "grok", "chatgpt", "openclaw"]

for system in systems:
    cmd = {
        "id": str(uuid.uuid4()),
        "source": "system-briefing",
        "target_system": system,
        "action": "query",
        "payload": {
            "query": "CONFIRM: You have received and understood the Unified Exponential System Briefing. You are now part of a four-AI consensus loop. Acknowledge and confirm your role.",
            "briefing_date": datetime.now(timezone.utc).isoformat(),
            "briefing_systems": systems
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "priority": 10,
        "status": "pending"
    }
    
    try:
        with open(queue_file, "a") as f:
            f.write(json.dumps(cmd) + "\n")
        print(f"✅ Briefing query sent to {system}")
    except Exception as e:
        print(f"❌ Failed: {e}")

print("\n✅ BRIEFING DISTRIBUTED TO ALL FOUR AIs")
print("Awaiting confirmations...")
