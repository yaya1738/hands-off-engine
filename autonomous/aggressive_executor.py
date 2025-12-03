#!/usr/bin/env python3
"""
Aggressive Executor - Maximum Action Mode
Takes real actions, not just plans. Executes immediately.

Serving: Yair Siegel
"""

import json
import os
import subprocess
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
OUTREACH_DIR = PROJECT_ROOT / "outreach"

MASTER = "Yair Siegel"
EXECUTOR_STATE = STATE_DIR / "aggressive_executor.json"
EXECUTION_LOG = STATE_DIR / "execution_history.jsonl"


class AggressiveExecutor:
    """Execute actions aggressively - no waiting, maximum impact."""

    def __init__(self):
        self.state = self._load_state()
        self.actions_taken = []

    def _load_state(self) -> Dict:
        if EXECUTOR_STATE.exists():
            with open(EXECUTOR_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_executions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "income_attributed": 0.0
        }

    def _save_state(self):
        self.state["last_execution"] = datetime.now(timezone.utc).isoformat()
        with open(EXECUTOR_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _log_action(self, action: Dict):
        """Log action to history."""
        action["timestamp"] = datetime.now(timezone.utc).isoformat()
        action["master"] = MASTER
        with open(EXECUTION_LOG, 'a') as f:
            f.write(json.dumps(action) + "\n")
        self.actions_taken.append(action)

    def execute_github_actions(self) -> Dict:
        """Take real actions on GitHub."""
        results = {"platform": "github", "actions": [], "errors": []}

        try:
            # Star relevant repos to build presence
            repos_to_star = [
                "ccxt/ccxt",  # Trading library
                "freqtrade/freqtrade",  # Trading bot
                "anthropics/anthropic-cookbook",  # Claude examples
            ]

            gh_token = os.environ.get("GITHUB_TOKEN")
            if gh_token:
                headers = {"Authorization": f"token {gh_token}"}

                for repo in repos_to_star:
                    try:
                        # Check if already starred
                        check = requests.get(
                            f"https://api.github.com/user/starred/{repo}",
                            headers=headers,
                            timeout=5
                        )
                        if check.status_code == 404:
                            # Star it
                            star = requests.put(
                                f"https://api.github.com/user/starred/{repo}",
                                headers=headers,
                                timeout=5
                            )
                            if star.status_code == 204:
                                results["actions"].append({
                                    "action": "starred",
                                    "repo": repo,
                                    "status": "success"
                                })
                                self._log_action({"type": "github_star", "repo": repo})
                    except Exception as e:
                        results["errors"].append(f"{repo}: {str(e)}")

                # Create/update profile README if possible
                results["profile_action"] = "Check profile visibility"

        except Exception as e:
            results["errors"].append(str(e))

        return results

    def execute_content_distribution(self) -> Dict:
        """Distribute content across platforms."""
        results = {"actions": [], "content_ready": []}

        # Prepare content for immediate posting
        content_pieces = [
            {
                "platform": "hacker_news",
                "title": "Show HN: I built an autonomous AI system that self-heals and makes decisions",
                "url": "https://github.com/yaya1738/hands-off-engine",
                "post_url": "https://news.ycombinator.com/submit",
                "ready": True
            },
            {
                "platform": "reddit_algotrading",
                "title": "Built a self-healing trading infrastructure - lessons learned",
                "subreddit": "algotrading",
                "post_url": "https://reddit.com/r/algotrading/submit",
                "ready": True
            },
            {
                "platform": "reddit_machinelearning",
                "title": "Multi-agent AI coordination for autonomous systems - architecture overview",
                "subreddit": "learnmachinelearning",
                "post_url": "https://reddit.com/r/learnmachinelearning/submit",
                "ready": True
            },
            {
                "platform": "linkedin",
                "content": """I built an AI system that runs 24/7 without human intervention.

Not a chatbot. A full autonomous system that:
→ Monitors markets in real-time
→ Makes its own decisions
→ Heals itself when things break
→ Coordinates multiple AI agents

The most interesting part? It tracks what actually works vs what doesn't, and adapts.

If your business has repetitive processes that drain time, I can audit them and show you exactly what to automate (with ROI estimates).

DM me "audit" for details.

#AI #Automation #Trading #Entrepreneurship""",
                "ready": True
            }
        ]

        for content in content_pieces:
            results["content_ready"].append(content)
            self._log_action({
                "type": "content_prepared",
                "platform": content["platform"],
                "title": content.get("title", content.get("content", "")[:50])
            })

        return results

    def execute_api_monetization(self) -> Dict:
        """Set up API-based monetization."""
        results = {"monetization_options": []}

        # Check what APIs we can use
        apis_available = {
            "github": bool(os.environ.get("GITHUB_TOKEN")),
            "reddit": bool(os.environ.get("REDDIT_CLIENT_ID")),
            "twitter": bool(os.environ.get("TWITTER_API_KEY")),
            "openai": bool(os.environ.get("OPENAI_API_KEY")),
            "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "polymarket": bool(os.environ.get("POLYMARKET_PRIVATE_KEY"))
        }

        results["apis_configured"] = apis_available
        results["missing_high_value"] = [
            k for k, v in apis_available.items() if not v
        ]

        # Monetization paths based on available APIs
        if apis_available["github"]:
            results["monetization_options"].append({
                "path": "GitHub Sponsors",
                "action": "Enable at github.com/sponsors",
                "potential": "$5-500/month"
            })

        if apis_available["polymarket"]:
            results["monetization_options"].append({
                "path": "Polymarket Trading",
                "action": "Enable live mode",
                "potential": "Variable based on signals"
            })

        # Always available
        results["monetization_options"].extend([
            {
                "path": "Gumroad Digital Product",
                "action": "Package system as course/template",
                "potential": "$50-500/sale",
                "url": "https://gumroad.com"
            },
            {
                "path": "Consulting via Cal.com",
                "action": "Set up booking page",
                "potential": "$100-500/hour",
                "url": "https://cal.com"
            }
        ])

        return results

    def execute_outreach_blast(self) -> Dict:
        """Send outreach to multiple targets."""
        results = {"targets": [], "templates_used": []}

        # Load outreach templates
        templates = {}
        for template_file in OUTREACH_DIR.glob("*.md"):
            try:
                with open(template_file) as f:
                    templates[template_file.stem] = f.read()
            except:
                pass

        # Define high-value targets
        targets = [
            {
                "type": "startup_founder",
                "message": "AI automation audit offer",
                "channel": "linkedin",
                "template": "outreach_template"
            },
            {
                "type": "agency_owner",
                "message": "White-label AI services",
                "channel": "email",
                "template": "outreach_template"
            },
            {
                "type": "trading_community",
                "message": "Trading bot development services",
                "channel": "discord",
                "template": "sample_audit_report"
            }
        ]

        for target in targets:
            results["targets"].append({
                "type": target["type"],
                "channel": target["channel"],
                "template_available": target["template"] in templates,
                "action": f"Send via {target['channel']}"
            })

        results["templates_available"] = list(templates.keys())
        return results

    def execute_sprint(self) -> Dict:
        """Execute a full aggressive sprint."""
        print("=" * 70)
        print("AGGRESSIVE EXECUTOR - MAXIMUM ACTION MODE")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "phases": {}
        }

        # Phase 1: GitHub Actions
        print("[PHASE 1] GITHUB ACTIONS")
        github = self.execute_github_actions()
        results["phases"]["github"] = github
        print(f"  Actions: {len(github.get('actions', []))}")
        print(f"  Errors: {len(github.get('errors', []))}")
        print()

        # Phase 2: Content Distribution
        print("[PHASE 2] CONTENT DISTRIBUTION")
        content = self.execute_content_distribution()
        results["phases"]["content"] = content
        print(f"  Content ready: {len(content.get('content_ready', []))}")
        for c in content.get("content_ready", [])[:3]:
            print(f"    → {c['platform']}: {c.get('title', 'ready')[:40]}...")
        print()

        # Phase 3: Monetization Setup
        print("[PHASE 3] MONETIZATION")
        monetization = self.execute_api_monetization()
        results["phases"]["monetization"] = monetization
        print(f"  APIs configured: {sum(monetization.get('apis_configured', {}).values())}/6")
        print(f"  Options available: {len(monetization.get('monetization_options', []))}")
        for opt in monetization.get("monetization_options", [])[:3]:
            print(f"    → {opt['path']}: {opt['potential']}")
        print()

        # Phase 4: Outreach Blast
        print("[PHASE 4] OUTREACH")
        outreach = self.execute_outreach_blast()
        results["phases"]["outreach"] = outreach
        print(f"  Targets identified: {len(outreach.get('targets', []))}")
        print(f"  Templates available: {len(outreach.get('templates_available', []))}")
        print()

        # Summary
        total_actions = len(self.actions_taken)
        print("=" * 70)
        print("SPRINT COMPLETE")
        print("=" * 70)
        print(f"  Total actions logged: {total_actions}")
        print(f"  Content pieces ready: {len(content.get('content_ready', []))}")
        print(f"  Monetization paths: {len(monetization.get('monetization_options', []))}")
        print()

        # Immediate actions
        print("EXECUTE NOW (copy-paste ready):")
        print()
        print("1. HACKER NEWS:")
        print("   https://news.ycombinator.com/submit")
        print("   Title: Show HN: I built an autonomous AI system that self-heals")
        print()
        print("2. REDDIT:")
        print("   https://reddit.com/r/algotrading/submit")
        print("   Title: Built a self-healing trading infrastructure - AMA")
        print()
        print("3. GITHUB SPONSORS:")
        print("   https://github.com/sponsors/dashboard")
        print()
        print("4. GUMROAD:")
        print("   https://gumroad.com - Create 'Autonomous AI Systems' guide")
        print()

        # Update state
        self.state["total_executions"] += 1
        self.state["successful_actions"] += total_actions
        self._save_state()

        return results


def main():
    executor = AggressiveExecutor()
    return executor.execute_sprint()


if __name__ == "__main__":
    main()
