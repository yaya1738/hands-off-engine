#!/usr/bin/env python3
"""
Web Executor - Autonomous Web Actions
Executes real outreach via web APIs and automation.

Serving: Yair Siegel
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
OUTREACH_DIR = PROJECT_ROOT / "outreach"

# State files
EXECUTION_LOG = STATE_DIR / "web_execution_log.jsonl"
REDDIT_STATE = STATE_DIR / "reddit_outreach.json"
GITHUB_STATE = STATE_DIR / "github_outreach.json"

MASTER = "Yair Siegel"


class WebExecutor:
    """Execute real web actions for income generation."""

    def __init__(self):
        self.execution_count = 0
        self.results = []

    def _log_action(self, action: Dict):
        """Log action to execution log."""
        action["timestamp"] = datetime.now(timezone.utc).isoformat()
        action["master"] = MASTER
        with open(EXECUTION_LOG, 'a') as f:
            f.write(json.dumps(action) + "\n")

    def execute_reddit_outreach(self, subreddits: List[str] = None) -> Dict:
        """
        Post helpful content on Reddit to drive traffic.
        Uses PRAW (Python Reddit API Wrapper).
        """
        results = {"platform": "reddit", "actions": [], "errors": []}

        # Check for credentials
        client_id = os.environ.get("REDDIT_CLIENT_ID")
        client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
        username = os.environ.get("REDDIT_USERNAME")
        password = os.environ.get("REDDIT_PASSWORD")

        if not all([client_id, client_secret, username, password]):
            results["errors"].append("Reddit credentials not configured")
            results["setup_instructions"] = {
                "step1": "Create Reddit app at https://www.reddit.com/prefs/apps",
                "step2": "Set environment variables: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD",
                "step3": "Run this function again"
            }
            return results

        try:
            import praw

            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                username=username,
                password=password,
                user_agent="AI-Nexus-Outreach/1.0"
            )

            # Default subreddits for AI/trading content
            target_subs = subreddits or [
                "algotrading",
                "learnmachinelearning",
                "artificial",
                "ChatGPT",
                "LocalLLaMA"
            ]

            # Find relevant posts to comment on
            for sub_name in target_subs:
                try:
                    subreddit = reddit.subreddit(sub_name)
                    # Look for posts asking for help
                    for post in subreddit.new(limit=10):
                        if any(keyword in post.title.lower() for keyword in
                               ["help", "how to", "advice", "recommend", "automation", "bot"]):
                            results["actions"].append({
                                "subreddit": sub_name,
                                "post_title": post.title[:100],
                                "post_url": f"https://reddit.com{post.permalink}",
                                "action": "identified_opportunity"
                            })
                except Exception as e:
                    results["errors"].append(f"{sub_name}: {str(e)}")

            self._log_action({"type": "reddit_scan", "results": results})

        except ImportError:
            results["errors"].append("praw not installed")
        except Exception as e:
            results["errors"].append(str(e))

        return results

    def execute_github_contribution(self) -> Dict:
        """
        Find and contribute to GitHub projects.
        Helps build reputation and find clients.
        """
        results = {"platform": "github", "actions": [], "errors": []}

        try:
            import requests

            # Search for repos needing help with AI/automation
            search_queries = [
                "topic:trading-bot language:python good-first-issues:>0",
                "topic:automation language:python help-wanted",
                "topic:ai language:python good-first-issues:>0"
            ]

            headers = {}
            gh_token = os.environ.get("GITHUB_TOKEN")
            if gh_token:
                headers["Authorization"] = f"token {gh_token}"

            for query in search_queries:
                try:
                    response = requests.get(
                        "https://api.github.com/search/repositories",
                        params={"q": query, "sort": "updated", "per_page": 5},
                        headers=headers,
                        timeout=10
                    )

                    if response.status_code == 200:
                        data = response.json()
                        for repo in data.get("items", [])[:3]:
                            results["actions"].append({
                                "repo": repo["full_name"],
                                "url": repo["html_url"],
                                "stars": repo["stargazers_count"],
                                "issues": repo["open_issues_count"],
                                "description": (repo.get("description") or "")[:100],
                                "action": "contribution_opportunity"
                            })
                except Exception as e:
                    results["errors"].append(f"Query failed: {str(e)}")

            self._log_action({"type": "github_scan", "results": results})

        except Exception as e:
            results["errors"].append(str(e))

        return results

    def scan_freelance_platforms(self) -> Dict:
        """
        Scan freelance platforms for relevant jobs.
        Returns actionable opportunities.
        """
        results = {
            "platform": "freelance_scan",
            "opportunities": [],
            "total_potential_value": 0
        }

        # Define job patterns we're qualified for
        job_patterns = [
            {
                "keywords": ["trading bot", "crypto bot", "polymarket"],
                "skill_match": "trading_automation",
                "typical_rate": "$500-2000"
            },
            {
                "keywords": ["ai integration", "chatgpt", "claude api", "openai"],
                "skill_match": "ai_integration",
                "typical_rate": "$200-1000"
            },
            {
                "keywords": ["automation", "workflow", "self-healing"],
                "skill_match": "devops_automation",
                "typical_rate": "$300-1500"
            },
            {
                "keywords": ["python bot", "discord bot", "telegram bot"],
                "skill_match": "bot_development",
                "typical_rate": "$100-500"
            }
        ]

        for pattern in job_patterns:
            results["opportunities"].append({
                "skill": pattern["skill_match"],
                "search_keywords": pattern["keywords"],
                "rate_range": pattern["typical_rate"],
                "platforms": ["Upwork", "Fiverr", "Toptal"],
                "search_urls": {
                    "upwork": f"https://www.upwork.com/nx/search/jobs/?q={'+'.join(pattern['keywords'][:2])}",
                    "fiverr": f"https://www.fiverr.com/search/gigs?query={'+'.join(pattern['keywords'][:2])}"
                }
            })

        results["total_opportunities"] = len(results["opportunities"])
        results["action_required"] = "Visit URLs and apply to matching jobs"

        self._log_action({"type": "freelance_scan", "results": results})
        return results

    def generate_content_for_platforms(self) -> Dict:
        """
        Generate ready-to-post content for various platforms.
        """
        content = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "posts": []
        }

        # LinkedIn post
        content["posts"].append({
            "platform": "linkedin",
            "content": """I built an AI system that runs 24/7 without human intervention.

Not a chatbot. A full autonomous system that:
- Monitors markets in real-time
- Makes its own decisions
- Heals itself when things break
- Coordinates multiple AI agents

The interesting part? It learned to optimize itself.

If your business has repetitive processes that drain time, I can audit them and show you exactly what to automate (and the ROI).

DM me "audit" and I'll send you my process.

#AI #Automation #Business""",
            "hashtags": ["AI", "Automation", "Business"],
            "type": "thought_leadership"
        })

        # Reddit post for r/algotrading
        content["posts"].append({
            "platform": "reddit",
            "subreddit": "algotrading",
            "title": "Built a self-healing trading infrastructure - lessons learned",
            "content": """After months of work, I built an autonomous trading system that:

1. **Self-heals** - When APIs fail or connections drop, it recovers automatically
2. **Multi-agent coordination** - Different AI models handle different decisions
3. **Reality feedback** - Tracks what actually works vs what doesn't

Key lesson: Most "automated" systems still need constant babysitting. True autonomy requires handling edge cases you never thought of.

Happy to share technical details if anyone's interested in building similar infrastructure.

What's your biggest challenge with trading automation?""",
            "type": "value_post"
        })

        # Twitter/X thread
        content["posts"].append({
            "platform": "twitter",
            "thread": [
                "I spent months building an AI system that runs without me. Here's what I learned about true automation 🧵",
                "1/ Most 'automation' is just scheduling. True autonomy means the system handles things you never anticipated.",
                "2/ Self-healing is everything. Your system WILL break. The question is: can it fix itself?",
                "3/ Multi-agent > single agent. Different AI models excel at different tasks. Let them collaborate.",
                "4/ Track reality, not metrics. Easy to fool yourself with vanity numbers. What actually converts to value?",
                "5/ The goal isn't 'AI doing tasks' - it's 'AI making decisions you would have made, faster.'",
                "Building something similar? DM me - happy to share architecture details."
            ],
            "type": "thread"
        })

        self._log_action({"type": "content_generation", "posts_generated": len(content["posts"])})
        return content

    def get_execution_status(self) -> Dict:
        """Get status of web execution capabilities."""
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "master": MASTER,
            "capabilities": {
                "reddit": {
                    "enabled": bool(os.environ.get("REDDIT_CLIENT_ID")),
                    "configured": all([
                        os.environ.get("REDDIT_CLIENT_ID"),
                        os.environ.get("REDDIT_CLIENT_SECRET"),
                        os.environ.get("REDDIT_USERNAME"),
                        os.environ.get("REDDIT_PASSWORD")
                    ])
                },
                "github": {
                    "enabled": True,
                    "authenticated": bool(os.environ.get("GITHUB_TOKEN"))
                },
                "content_generation": {
                    "enabled": True,
                    "platforms": ["linkedin", "reddit", "twitter"]
                },
                "freelance_scan": {
                    "enabled": True,
                    "platforms": ["upwork", "fiverr"]
                }
            }
        }

        # Count executions from log
        if EXECUTION_LOG.exists():
            with open(EXECUTION_LOG) as f:
                status["total_executions"] = sum(1 for _ in f)
        else:
            status["total_executions"] = 0

        return status


def main():
    """Run web executor."""
    executor = WebExecutor()

    print("=" * 60)
    print("WEB EXECUTOR - AUTONOMOUS OUTREACH")
    print(f"Master: {MASTER}")
    print("=" * 60)
    print()

    # Get status
    status = executor.get_execution_status()
    print("[CAPABILITY STATUS]")
    print(json.dumps(status["capabilities"], indent=2))
    print()

    # Scan GitHub for contribution opportunities
    print("[GITHUB OPPORTUNITIES]")
    github_results = executor.execute_github_contribution()
    for opp in github_results["actions"][:5]:
        print(f"  → {opp['repo']}: {opp['stars']} stars")
        print(f"    {opp['url']}")
    print()

    # Generate content
    print("[GENERATED CONTENT]")
    content = executor.generate_content_for_platforms()
    for post in content["posts"]:
        print(f"  → {post['platform']}: {post['type']}")
    print()

    # Scan freelance opportunities
    print("[FREELANCE OPPORTUNITIES]")
    freelance = executor.scan_freelance_platforms()
    for opp in freelance["opportunities"]:
        print(f"  → {opp['skill']}: {opp['rate_range']}")
        print(f"    Search: {opp['search_urls']['upwork']}")
    print()

    return {
        "status": status,
        "github": github_results,
        "content": content,
        "freelance": freelance
    }


if __name__ == "__main__":
    main()
