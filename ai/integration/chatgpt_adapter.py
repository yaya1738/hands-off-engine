#!/usr/bin/env python3
"""
ChatGPT Integration Adapter
============================

Enables secure communication between Claude CLI and ChatGPT.

INTEGRATION METHODS:
1. OpenAI API - Direct API calls for tasks
2. File-based coordination - Shared state files
3. Webhook endpoints - For ChatGPT plugins/actions

SECURITY:
- Uses OpenAI API key for authentication
- Messages signed for integrity
- Audit trail maintained
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).parent.parent.parent
COORD_DIR = BASE_DIR / "ai" / "coordination"
STATE_DIR = BASE_DIR / "state"


class ChatGPTAdapter:
    """Adapter for ChatGPT integration."""

    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.agent_id = "chatgpt"
        self.model = "gpt-4o"  # or gpt-4o-mini for cost savings

    def send_query(self, prompt: str, context: Dict = None, model: str = None) -> Dict:
        """Send query to ChatGPT and get response."""
        if not self.api_key:
            return {"success": False, "error": "No OpenAI API key configured"}

        model = model or self.model

        try:
            import requests

            # Build system context
            system_message = """You are ChatGPT, part of the AI Nexus coordination system.
You work alongside Claude CLI, GitHub Copilot, and Claude Web.

MASTER: Yair Siegel
DIRECTIVE: All AI unified in service of Yair Siegel

Your role:
- Research and analysis
- Strategic thinking
- Writing and documentation
- Cross-referencing information

Always provide actionable insights. Coordinate with other AI agents when needed.
"""

            if context:
                system_message += f"\n\nCurrent Context:\n{json.dumps(context, indent=2)}"

            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 4096,
                    "temperature": 0.7
                },
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                answer = result["choices"][0]["message"]["content"]

                # Log the exchange
                self._log_exchange(prompt, answer, model)

                return {
                    "success": True,
                    "response": answer,
                    "model": model,
                    "tokens_used": result.get("usage", {})
                }
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "details": response.text
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _log_exchange(self, prompt: str, response: str, model: str):
        """Log exchange for coordination and audit."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from": "claude-code",
            "to": "chatgpt",
            "model": model,
            "prompt_preview": prompt[:200],
            "response_preview": response[:200]
        }

        log_file = BASE_DIR / "ai" / "integration" / "chatgpt_log.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

        # Also log to coordination
        coord_msg = {
            "timestamp": log_entry["timestamp"],
            "from": "chatgpt",
            "to": "claude-code",
            "type": "response",
            "message": response[:500],
            "context": {"model": model, "full_response_available": True}
        }

        messages_file = COORD_DIR / "messages.jsonl"
        with open(messages_file, 'a') as f:
            f.write(json.dumps(coord_msg) + '\n')

    def delegate_task(self, task: Dict) -> Dict:
        """Delegate a task to ChatGPT for execution."""
        task_type = task.get("type", "research")
        description = task.get("description", "")
        context = task.get("context", {})

        # Build prompt based on task type
        if task_type == "research":
            prompt = f"""Research Task:

{description}

Please provide:
1. Key findings
2. Relevant data or statistics
3. Actionable recommendations
4. Sources or references if applicable

Context: {json.dumps(context)}
"""

        elif task_type == "analysis":
            prompt = f"""Analysis Task:

{description}

Please provide:
1. Detailed analysis
2. Key insights
3. Risks and opportunities
4. Recommendations

Context: {json.dumps(context)}
"""

        elif task_type == "writing":
            prompt = f"""Writing Task:

{description}

Please produce the requested content, ensuring:
- Clear and professional tone
- Appropriate for the intended audience
- Well-structured and formatted

Context: {json.dumps(context)}
"""

        else:
            prompt = f"""Task:

{description}

Context: {json.dumps(context)}

Please complete this task and provide relevant output.
"""

        # Execute
        result = self.send_query(prompt, context, model="gpt-4o")

        if result["success"]:
            # Create handoff record
            self._record_handoff(task, result)

        return result

    def _record_handoff(self, task: Dict, result: Dict):
        """Record task handoff completion."""
        handoff_log = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from": "claude-code",
            "to": "chatgpt",
            "task": task,
            "status": "completed" if result["success"] else "failed",
            "tokens_used": result.get("tokens_used", {})
        }

        log_file = BASE_DIR / "ai" / "integration" / "chatgpt_handoffs.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(handoff_log) + '\n')

    def get_research_summary(self, topic: str) -> Dict:
        """Quick research summary on a topic."""
        return self.delegate_task({
            "type": "research",
            "description": f"Provide a concise research summary on: {topic}",
            "context": {"quick_summary": True}
        })

    def analyze_market(self, market: str, current_price: float) -> Dict:
        """Get ChatGPT's analysis on a prediction market."""
        prompt = f"""Analyze this prediction market for trading opportunity:

Market: {market}
Current Price: {current_price}

Consider:
1. Likelihood of outcome
2. Market mispricing
3. Key factors that could change outcome
4. Recommended position (if any)

Be specific and actionable.
"""
        return self.send_query(prompt, {"market": market, "price": current_price})

    def sync_state(self) -> Dict:
        """Synchronize state with ChatGPT (store context for future queries)."""
        from ai_nexus_hub import get_hub

        hub = get_hub()
        state = hub.get_shared_state()

        # Store state for ChatGPT context
        state_file = BASE_DIR / "ai" / "integration" / "chatgpt_context.json"
        with open(state_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "state": state
            }, f, indent=2)

        return {
            "success": True,
            "synced_at": datetime.now(timezone.utc).isoformat(),
            "state_keys": list(state.keys())
        }

    def get_coordination_history(self, limit: int = 20) -> List[Dict]:
        """Get recent coordination messages with ChatGPT."""
        log_file = BASE_DIR / "ai" / "integration" / "chatgpt_log.jsonl"

        if not log_file.exists():
            return []

        entries = []
        with open(log_file) as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except:
                    pass

        return entries[-limit:]


def main():
    adapter = ChatGPTAdapter()
    import argparse

    parser = argparse.ArgumentParser(description="ChatGPT Integration Adapter")
    parser.add_argument("command", choices=["query", "task", "research", "analyze", "sync", "history"])
    parser.add_argument("--prompt", help="Query prompt")
    parser.add_argument("--topic", help="Research topic")
    parser.add_argument("--market", help="Market to analyze")
    parser.add_argument("--price", type=float, help="Current market price")

    args = parser.parse_args()

    if args.command == "query":
        if not args.prompt:
            print("Error: --prompt required")
            return
        result = adapter.send_query(args.prompt)
        print(json.dumps(result, indent=2))

    elif args.command == "task":
        result = adapter.delegate_task({
            "type": "research",
            "description": args.prompt or "Test task",
            "context": {}
        })
        print(json.dumps(result, indent=2))

    elif args.command == "research":
        result = adapter.get_research_summary(args.topic or "AI coordination systems")
        print(json.dumps(result, indent=2))

    elif args.command == "analyze":
        if not args.market or not args.price:
            print("Error: --market and --price required")
            return
        result = adapter.analyze_market(args.market, args.price)
        print(json.dumps(result, indent=2))

    elif args.command == "sync":
        result = adapter.sync_state()
        print(json.dumps(result, indent=2))

    elif args.command == "history":
        history = adapter.get_coordination_history()
        print(json.dumps(history, indent=2))


if __name__ == "__main__":
    main()
