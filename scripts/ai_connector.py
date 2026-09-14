#!/usr/bin/env python3
"""
AI Agent Connector — Universal AI dispatch for the autonomous system.

Routes tasks to available AI backends and collects responses:
1. Direct API (OpenAI, Anthropic, OpenRouter) if keys are present
2. Telegram operator relay (sends task to Yair's Telegram, gets response)
3. Messages.jsonl coordination (async agent-to-agent handoff)
4. AnyClaw/Codex bridge (sends notification, awaits callback)

Usage:
    from scripts.ai_connector import AIConnector
    ai = AIConnector()
    result = ai.dispatch(task="Analyze ETH/USD position risk", context={...}, prefer="openai")
"""

import json
import os
import sys
import uuid
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [AIConnector] %(message)s')
log = logging.getLogger("AIConnector")

REPO_ROOT = Path.home() / "hands-off-engine"
STATE_DIR = REPO_ROOT / "state"
TASK_DIR = STATE_DIR / "ai_tasks"
RESULTS_DIR = STATE_DIR / "ai_results"
PENDING_REQUESTS = STATE_DIR / "ai_pending_requests.json"

# Auto-detect available API keys
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")


# ──────────────────────────────────────────────────────────────────────
# Available AI backends with their capabilities
# ──────────────────────────────────────────────────────────────────────

AI_BACKENDS = {
    "openai": {
        "name": "OpenAI",
        "requires_key": "OPENAI_API_KEY",
        "capabilities": ["chat", "analysis", "code", "reasoning", "vision"],
        "max_tokens": 128000,
        "supports_tools": True,
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "requires_key": "ANTHROPIC_API_KEY",
        "capabilities": ["chat", "analysis", "code", "reasoning", "long_context"],
        "max_tokens": 200000,
        "supports_tools": True,
    },
    "openrouter": {
        "name": "OpenRouter (multi-model)",
        "requires_key": "OPENROUTER_KEY",
        "capabilities": ["chat", "analysis", "code", "reasoning"],
        "max_tokens": 128000,
        "supports_tools": True,
    },
    "codex_anyclaw": {
        "name": "Codex/AnyClaw (local)",
        "requires_key": None,
        "capabilities": ["chat", "analysis", "code", "reasoning", "device_control", "file_access"],
        "max_tokens": 100000,
        "supports_tools": True,
    },
    "telegram_relay": {
        "name": "Telegram Operator Relay",
        "requires_key": None,
        "capabilities": ["human_approval", "decision_making", "clarification"],
        "max_tokens": 4000,
        "supports_tools": False,
    },
    "messages_jsonl": {
        "name": "Agent Coordination Bus",
        "requires_key": None,
        "capabilities": ["async_handoff", "task_distribution", "status_updates"],
        "max_tokens": None,
        "supports_tools": False,
    },
}


class AIConnector:
    """Universal AI dispatch — routes tasks to available backends."""

    def __init__(self, repo_root=None):
        self.repo_root = Path(repo_root) if repo_root else REPO_ROOT
        self.state_dir = self.repo_root / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        TASK_DIR.mkdir(parents=True, exist_ok=True)
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        self.available_backends = self._detect_backends()
        self.system_prompt = self._load_system_prompt()

    def _detect_backends(self):
        """Detect which AI backends are available."""
        available = {}
        for key, info in AI_BACKENDS.items():
            req = info.get("requires_key")
            if req is None or os.getenv(req, ""):
                available[key] = info
            else:
                log.debug(f"Backend {key} unavailable (missing {req})")
        return available

    def _load_system_prompt(self):
        """Load the system context from .claude/instructions.md."""
        instr = self.repo_root / ".claude" / "instructions.md"
        if instr.exists():
            return instr.read_text()[:4000]
        return "You are an AI assistant for the hands-off-engine autonomous system. All actions serve Yair Siegel."

    def list_backends(self):
        """List available AI backends."""
        return {
            k: {"name": v["name"], "capabilities": v["capabilities"]}
            for k, v in self.available_backends.items()
        }

    # ── dispatch ──

    def dispatch(self, task, context=None, prefer=None, timeout=120,
                 requires_approval=False, callback=None):
        """Send a task to the best available AI and return the response.

        Args:
            task: Natural language task description
            context: Additional context dict
            prefer: Preferred backend key (or None for auto-select)
            timeout: Max seconds to wait for response
            requires_approval: If True, route through operator via Telegram
            callback: Optional webhook URL for async response
        """
        task_id = str(uuid.uuid4())
        enriched_task = self._build_task(task, context, task_id)

        # If requires approval, always go through operator
        if requires_approval:
            return self._dispatch_to_operator(enriched_task, task_id)

        # Auto-select backend
        backend = prefer if prefer and prefer in self.available_backends else self._select_backend(task)

        log.info(f"Dispatching task {task_id[:8]}... to {backend}")

        if backend == "openai":
            return self._call_openai(enriched_task, task_id)
        elif backend == "anthropic":
            return self._call_anthropic(enriched_task, task_id)
        elif backend == "openrouter":
            return self._call_openrouter(enriched_task, task_id)
        elif backend == "telegram_relay":
            return self._dispatch_to_operator(enriched_task, task_id)
        elif backend == "codex_anyclaw":
            return self._dispatch_to_anyclaw(enriched_task, task_id)
        elif backend == "messages_jsonl":
            return self._dispatch_to_coordination(enriched_task, task_id)
        else:
            return {"status": "error", "error": "No AI backend available", "task_id": task_id}

    def _select_backend(self, task):
        """Auto-select the best backend for a task."""
        # Prefer direct API backends
        if "openai" in self.available_backends:
            return "openai"
        if "anthropic" in self.available_backends:
            return "anthropic"
        if "openrouter" in self.available_backends:
            return "openrouter"
        # Fall back to coordination/relay
        if "codex_anyclaw" in self.available_backends:
            return "codex_anyclaw"
        if "telegram_relay" in self.available_backends:
            return "telegram_relay"
        return "messages_jsonl"

    def _build_task(self, task, context, task_id):
        """Build enriched task dict with system context."""
        return {
            "task_id": task_id,
            "task": task,
            "context": context or {},
            "system_prompt": self.system_prompt,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "hands-off-engine",
        }

    # ── OpenAI API ──

    def _call_openai(self, task_dict, task_id):
        """Call OpenAI API directly."""
        try:
            import urllib.request
            payload = json.dumps({
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": task_dict["system_prompt"]},
                    {"role": "user", "content": self._format_task_prompt(task_dict)},
                ],
                "temperature": 0.3,
                "max_tokens": 4000,
            }).encode()

            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENAI_KEY}",
                },
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                content = data["choices"][0]["message"]["content"]
                result = {"status": "success", "response": content, "backend": "openai", "task_id": task_id}
                self._save_result(task_id, result)
                return result
        except Exception as e:
            log.error(f"OpenAI call failed: {e}")
            return {"status": "error", "error": str(e), "backend": "openai", "task_id": task_id}

    # ── Anthropic API ──

    def _call_anthropic(self, task_dict, task_id):
        """Call Anthropic Claude API directly."""
        try:
            import urllib.request
            payload = json.dumps({
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 4000,
                "system": task_dict["system_prompt"],
                "messages": [
                    {"role": "user", "content": self._format_task_prompt(task_dict)},
                ],
            }).encode()

            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": ANTHROPIC_KEY,
                    "anthropic-version": "2023-06-01",
                },
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                content = data["content"][0]["text"]
                result = {"status": "success", "response": content, "backend": "anthropic", "task_id": task_id}
                self._save_result(task_id, result)
                return result
        except Exception as e:
            log.error(f"Anthropic call failed: {e}")
            return {"status": "error", "error": str(e), "backend": "anthropic", "task_id": task_id}

    # ── OpenRouter (multi-model) ──

    def _call_openrouter(self, task_dict, task_id):
        """Call OpenRouter — access to many models."""
        try:
            import urllib.request
            payload = json.dumps({
                "model": "anthropic/claude-sonnet-4-20250514",
                "messages": [
                    {"role": "system", "content": task_dict["system_prompt"]},
                    {"role": "user", "content": self._format_task_prompt(task_dict)},
                ],
                "temperature": 0.3,
                "max_tokens": 4000,
            }).encode()

            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENROUTER_KEY}",
                },
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                content = data["choices"][0]["message"]["content"]
                result = {"status": "success", "response": content, "backend": "openrouter", "task_id": task_id}
                self._save_result(task_id, result)
                return result
        except Exception as e:
            log.error(f"OpenRouter call failed: {e}")
            return {"status": "error", "error": str(e), "backend": "openrouter", "task_id": task_id}

    # ── Telegram relay (ask operator) ──

    def _dispatch_to_operator(self, task_dict, task_id):
        """Send task to operator via Telegram and await response."""
        prompt = self._format_task_prompt(task_dict)
        msg = f"🤖 AI Task Request [{task_id[:8]}]\n\n{prompt}\n\nReply with your decision."

        try:
            # Send notification
            subprocess.run(
                ["termux-notification", "-t", "AI Task Request", "-c", msg[:200], "--id", f"ai-{task_id[:8]}"],
                capture_output=True, timeout=5,
            )

            # Write to inbound for when operator responds
            pending = self._load_pending()
            pending[task_id] = {
                "task": task_dict,
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "status": "awaiting_operator",
            }
            self._save_pending(pending)

            return {"status": "awaiting_operator", "task_id": task_id, "notification_sent": True}
        except Exception as e:
            return {"status": "error", "error": str(e), "task_id": task_id}

    # ── Coordination bus (async agent handoff) ──

    def _dispatch_to_anyclaw(self, task_dict, task_id):
        """Post task specifically to AnyClaw (Codex CLI) party."""
        try:
            from scripts.comm_hub import CommHub
            hub = CommHub(repo_root=self.repo_root)
            result = hub.send(
                "anyclaw", "task_assignment",
                {"task_id": task_id, "task": task_dict["task"], "context": task_dict.get("context", {})},
                source="ai_connector",
            )
            pending = self._load_pending()
            pending[task_id] = {
                "task": task_dict,
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "status": "awaiting_agent",
                "dispatched_to": "anyclaw",
            }
            self._save_pending(pending)
            return {"status": "dispatched", "task_id": task_id, "channel": "coordination_bus", "dispatched_to": "anyclaw", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e), "task_id": task_id}

    def _dispatch_to_coordination(self, task_dict, task_id):
        """Post task to coordination bus — routes to AnyClaw by default."""
        try:
            from scripts.comm_hub import CommHub
            hub = CommHub(repo_root=self.repo_root)
            result = hub.send(
                "anyclaw", "task_assignment",
                {"task_id": task_id, "task": task_dict["task"], "context": task_dict.get("context", {})},
                source="ai_connector",
            )
            pending = self._load_pending()
            pending[task_id] = {
                "task": task_dict,
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "status": "awaiting_agent",
                "dispatched_to": "anyclaw",
            }
            self._save_pending(pending)
            return {"status": "dispatched", "task_id": task_id, "channel": "coordination_bus", "dispatched_to": "anyclaw", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e), "task_id": task_id}

    # ── response handling ──

    def receive_response(self, task_id, response_text, source="operator"):
        """Receive an AI response for a pending task."""
        pending = self._load_pending()
        if task_id not in pending:
            return {"status": "error", "error": f"No pending task {task_id}"}

        task_entry = pending.pop(task_id)
        self._save_pending(pending)

        result = {
            "status": "success",
            "task_id": task_id,
            "response": response_text,
            "received_from": source,
            "received_at": datetime.now(timezone.utc).isoformat(),
            "original_task": task_entry["task"]["task"],
        }
        self._save_result(task_id, result)
        log.info(f"Received response for {task_id[:8]}... from {source}")
        return result

    def get_pending_tasks(self):
        """List tasks awaiting AI response."""
        return self._load_pending()

    def get_result(self, task_id):
        """Retrieve a completed task result."""
        result_file = RESULTS_DIR / f"{task_id}.json"
        if result_file.exists():
            return json.loads(result_file.read_text())
        return None

    def get_all_results(self, limit=20):
        """Get recent task results."""
        results = []
        for f in sorted(RESULTS_DIR.glob("*.json"), reverse=True)[:limit]:
            try:
                results.append(json.loads(f.read_text()))
            except Exception:
                pass
        return results

    # ── batch analysis ──

    def analyze(self, analysis_type, data, prefer=None):
        """Run a structured analysis through AI.

        Analysis types: risk, opportunity, market, performance, health
        """
        prompts = {
            "risk": "Analyze the following data for risks. Be specific about what could go wrong and recommended mitigations:\n\n",
            "opportunity": "Identify opportunities in the following data. Focus on actionable insights:\n\n",
            "market": "Analyze market conditions from this data. What are the key signals?\n\n",
            "performance": "Review performance metrics. What's working, what needs improvement?\n\n",
            "health": "Assess system health from this data. Any concerns?\n\n",
        }
        prompt = prompts.get(analysis_type, "Analyze this data:\n\n")
        prompt += json.dumps(data, indent=2, default=str)[:8000]
        return self.dispatch(task=prompt, prefer=prefer)

    # ── formatting ──

    def _format_task_prompt(self, task_dict):
        """Format task into a prompt for the AI."""
        parts = [
            f"TASK: {task_dict['task']}",
            f"Source: {task_dict.get('source', 'unknown')}",
            f"Time: {task_dict.get('timestamp', 'unknown')}",
        ]
        if task_dict.get("context"):
            parts.append(f"\nContext:\n{json.dumps(task_dict['context'], indent=2, default=str)[:4000]}")
        return "\n".join(parts)

    # ── persistence ──

    def _save_result(self, task_id, result):
        result_file = RESULTS_DIR / f"{task_id}.json"
        result_file.write_text(json.dumps(result, indent=2, default=str) + "\n")

    def _load_pending(self):
        if PENDING_REQUESTS.exists():
            try:
                return json.loads(PENDING_REQUESTS.read_text())
            except Exception:
                pass
        return {}

    def _save_pending(self, data):
        PENDING_REQUESTS.write_text(json.dumps(data, indent=2, default=str) + "\n")


# ── CLI ──

def cli():
    import argparse
    parser = argparse.ArgumentParser(description="AI Agent Connector")
    sub = parser.add_subparsers(dest="cmd")

    dispatch_p = sub.add_parser("dispatch", help="Send task to AI")
    dispatch_p.add_argument("task", help="Task description")
    dispatch_p.add_argument("--prefer", help="Preferred backend")
    dispatch_p.add_argument("--approval", action="store_true", help="Require operator approval")

    sub.add_parser("backends", help="List available backends")
    sub.add_parser("pending", help="List pending AI tasks")
    sub.add_parser("results", help="List recent results")

    analyze_p = sub.add_parser("analyze", help="Run analysis")
    analyze_p.add_argument("type", choices=["risk", "opportunity", "market", "performance", "health"])
    analyze_p.add_argument("data", help="JSON data file or inline JSON")

    receive_p = sub.add_parser("receive", help="Receive AI response for a task")
    receive_p.add_argument("task_id", help="Task ID")
    receive_p.add_argument("response", help="Response text")

    args = parser.parse_args()
    ai = AIConnector()

    if args.cmd == "dispatch":
        result = ai.dispatch(args.task, prefer=args.prefer, requires_approval=args.approval)
        print(json.dumps(result, indent=2))
    elif args.cmd == "backends":
        for k, v in ai.list_backends().items():
            print(f"  {k:20s} {v['name']} — {', '.join(v['capabilities'])}")
    elif args.cmd == "pending":
        pending = ai.get_pending_tasks()
        if pending:
            for tid, info in pending.items():
                print(f"  {tid[:8]}... status={info['status']} task={info['task']['task'][:60]}")
        else:
            print("  No pending tasks")
    elif args.cmd == "results":
        for r in ai.get_all_results():
            print(f"  {r.get('task_id', '?')[:8]}... status={r.get('status')} backend={r.get('backend', 'n/a')}")
    elif args.cmd == "analyze":
        try:
            data = json.loads(Path(args.data).read_text()) if Path(args.data).exists() else json.loads(args.data)
        except Exception:
            data = {"raw": args.data}
        result = ai.analyze(args.type, data, prefer=args.prefer if hasattr(args, 'prefer') else None)
        print(json.dumps(result, indent=2))
    elif args.cmd == "receive":
        result = ai.receive_response(args.task_id, args.response)
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    cli()
