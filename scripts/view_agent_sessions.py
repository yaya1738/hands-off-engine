#!/usr/bin/env python3
"""
View Agent Sessions - Monitor Failed and Timed-Out Copilot Agent Sessions

Queries GitHub Actions workflow runs for the Copilot agent and displays
failed, cancelled (timed-out), and error sessions for review and action.

Usage:
    python scripts/view_agent_sessions.py --list          # List recent sessions
    python scripts/view_agent_sessions.py --failed        # Show only failed/timed-out
    python scripts/view_agent_sessions.py --summary       # Show summary statistics
    python scripts/view_agent_sessions.py --react         # React to failed sessions
    python scripts/view_agent_sessions.py --json          # Output as JSON

Environment:
    GITHUB_TOKEN: GitHub API token (optional, for higher rate limits)

See: ai/coordination/messages.jsonl for agent coordination logs
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)

# Configuration
REPO_ROOT = Path(__file__).parent.parent
OWNER = "yaya1738"
REPO = "hands-off-engine"
WORKFLOW_ID = "208529335"  # Copilot coding agent workflow ID
API_BASE = "https://api.github.com"
SESSION_LOG = REPO_ROOT / "logs" / "agent_sessions.jsonl"

# Conclusions that indicate failure or timeout
FAILED_CONCLUSIONS = {"failure", "cancelled", "timed_out"}


@dataclass
class AgentSession:
    """Represents a Copilot agent session (workflow run)."""
    run_id: int
    run_number: int
    branch: str
    status: str
    conclusion: Optional[str]
    created_at: str
    updated_at: str
    pr_number: Optional[int]
    pr_title: Optional[str]
    html_url: str
    duration_seconds: Optional[float] = None
    head_sha: str = ""
    head_commit_message: str = ""
    
    def is_failed(self) -> bool:
        """Check if this session failed or timed out."""
        return self.conclusion in FAILED_CONCLUSIONS
    
    def is_in_progress(self) -> bool:
        """Check if this session is still running."""
        return self.status == "in_progress"
    
    def status_emoji(self) -> str:
        """Return an emoji representing the session status."""
        if self.is_in_progress():
            return "🔄"
        if self.conclusion == "success":
            return "✅"
        if self.conclusion == "cancelled":
            return "⏹️"
        if self.conclusion == "failure":
            return "❌"
        if self.conclusion == "timed_out":
            return "⏰"
        return "❓"
    
    def format_duration(self) -> str:
        """Format duration in human-readable format."""
        if self.duration_seconds is None:
            return "N/A"
        minutes = int(self.duration_seconds // 60)
        seconds = int(self.duration_seconds % 60)
        return f"{minutes}m {seconds}s"


class AgentSessionViewer:
    """Fetches and displays Copilot agent sessions from GitHub."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
    
    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a request to the GitHub API."""
        url = f"{API_BASE}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            # Handle rate limiting
            if response.status_code == 403:
                remaining = response.headers.get("X-RateLimit-Remaining", "?")
                if remaining == "0":
                    print("⚠️ GitHub API rate limit exceeded. Set GITHUB_TOKEN for higher limits.", file=sys.stderr)
                else:
                    print(f"⚠️ Access denied. This repo may be private. Set GITHUB_TOKEN env var.", file=sys.stderr)
                return {}
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}", file=sys.stderr)
            return {}
    
    def fetch_workflow_runs(self, per_page: int = 30, page: int = 1) -> List[Dict]:
        """Fetch workflow runs for the Copilot agent."""
        endpoint = f"/repos/{OWNER}/{REPO}/actions/workflows/{WORKFLOW_ID}/runs"
        params = {"per_page": per_page, "page": page}
        result = self._request(endpoint, params)
        return result.get("workflow_runs", [])
    
    def parse_session(self, run: Dict) -> AgentSession:
        """Parse a workflow run into an AgentSession."""
        # Calculate duration
        duration = None
        if run.get("created_at") and run.get("updated_at"):
            try:
                created = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
                updated = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
                duration = (updated - created).total_seconds()
            except (ValueError, TypeError):
                pass
        
        # Extract PR info
        pr_number = None
        pr_title = None
        if run.get("pull_requests"):
            pr = run["pull_requests"][0]
            pr_number = pr.get("number")
            # PR title not directly available, use branch name
            pr_title = run.get("head_branch", "").replace("copilot/", "").replace("-", " ")
        
        return AgentSession(
            run_id=run.get("id", 0),
            run_number=run.get("run_number", 0),
            branch=run.get("head_branch", ""),
            status=run.get("status", ""),
            conclusion=run.get("conclusion"),
            created_at=run.get("created_at", ""),
            updated_at=run.get("updated_at", ""),
            pr_number=pr_number,
            pr_title=pr_title,
            html_url=run.get("html_url", ""),
            duration_seconds=duration,
            head_sha=run.get("head_sha", "")[:7],
            head_commit_message=run.get("head_commit", {}).get("message", "")[:50],
        )
    
    def get_sessions(self, limit: int = 30, failed_only: bool = False) -> List[AgentSession]:
        """Get agent sessions, optionally filtering to failed/timed-out only."""
        runs = self.fetch_workflow_runs(per_page=limit)
        sessions = [self.parse_session(run) for run in runs]
        
        if failed_only:
            sessions = [s for s in sessions if s.is_failed()]
        
        return sessions
    
    def get_summary(self, limit: int = 50) -> Dict[str, Any]:
        """Get summary statistics for agent sessions."""
        runs = self.fetch_workflow_runs(per_page=limit)
        sessions = [self.parse_session(run) for run in runs]
        
        # Count by conclusion
        conclusion_counts: Dict[str, int] = {}
        total_duration = 0.0
        duration_count = 0
        
        for s in sessions:
            conclusion = s.conclusion or "in_progress"
            conclusion_counts[conclusion] = conclusion_counts.get(conclusion, 0) + 1
            if s.duration_seconds:
                total_duration += s.duration_seconds
                duration_count += 1
        
        avg_duration = total_duration / duration_count if duration_count > 0 else 0
        
        # Calculate failure rate
        total_completed = sum(v for k, v in conclusion_counts.items() if k != "in_progress")
        failed = sum(v for k, v in conclusion_counts.items() if k in FAILED_CONCLUSIONS)
        failure_rate = (failed / total_completed * 100) if total_completed > 0 else 0
        
        return {
            "total_sessions": len(sessions),
            "by_conclusion": conclusion_counts,
            "failure_rate_pct": round(failure_rate, 1),
            "avg_duration_minutes": round(avg_duration / 60, 1),
            "failed_sessions": [asdict(s) for s in sessions if s.is_failed()],
        }
    
    def react_to_failures(self, sessions: List[AgentSession]) -> List[Dict[str, str]]:
        """
        React to failed sessions with suggestions and actions.
        
        Returns a list of suggested actions for each failed session.
        """
        reactions: List[Dict[str, str]] = []
        
        for session in sessions:
            if not session.is_failed():
                continue
            
            reaction = {
                "run_id": session.run_id,
                "branch": session.branch,
                "conclusion": session.conclusion,
                "suggestion": "",
                "action": "",
            }
            
            if session.conclusion == "cancelled":
                # Likely timed out or manually cancelled
                reaction["suggestion"] = (
                    "Session was cancelled (possibly timed out). Consider:\n"
                    "  1. Breaking task into smaller chunks\n"
                    "  2. Providing clearer requirements\n"
                    "  3. Checking if the task scope was too large"
                )
                reaction["action"] = "review_and_reopen"
            
            elif session.conclusion == "failure":
                reaction["suggestion"] = (
                    "Session failed. Check:\n"
                    "  1. Workflow logs for error details\n"
                    "  2. PR comments for context\n"
                    "  3. If tests or linting failed"
                )
                reaction["action"] = "investigate_logs"
            
            elif session.conclusion == "timed_out":
                reaction["suggestion"] = (
                    "Session timed out. The task may be too complex or:\n"
                    "  1. Infinite loop in code\n"
                    "  2. Network/API issues\n"
                    "  3. Resource constraints"
                )
                reaction["action"] = "review_and_simplify"
            
            reactions.append(reaction)
        
        # Log reactions to file
        self._log_reactions(reactions)
        
        return reactions
    
    def _log_reactions(self, reactions: List[Dict[str, str]]):
        """Log reactions to the session log file."""
        SESSION_LOG.parent.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        with open(SESSION_LOG, 'a') as f:
            for reaction in reactions:
                entry = {
                    "timestamp": timestamp,
                    "type": "reaction",
                    **reaction,
                }
                f.write(json.dumps(entry) + "\n")


def format_session_table(sessions: List[AgentSession]) -> str:
    """Format sessions as a text table."""
    if not sessions:
        return "No sessions found."
    
    lines = []
    lines.append("=" * 100)
    lines.append(f"{'Run #':<8} {'Status':<10} {'Branch':<40} {'Duration':<12} {'PR':<6}")
    lines.append("-" * 100)
    
    for s in sessions:
        pr_str = f"#{s.pr_number}" if s.pr_number else "-"
        status_str = f"{s.status_emoji()} {s.conclusion or s.status}"
        branch_str = s.branch[:38] if len(s.branch) > 38 else s.branch
        lines.append(
            f"{s.run_number:<8} {status_str:<10} {branch_str:<40} "
            f"{s.format_duration():<12} {pr_str:<6}"
        )
    
    lines.append("=" * 100)
    return "\n".join(lines)


def format_summary(summary: Dict[str, Any]) -> str:
    """Format summary as readable text."""
    lines = []
    lines.append("\n📊 AGENT SESSION SUMMARY")
    lines.append("=" * 50)
    lines.append(f"Total Sessions: {summary['total_sessions']}")
    lines.append(f"Failure Rate: {summary['failure_rate_pct']}%")
    lines.append(f"Avg Duration: {summary['avg_duration_minutes']} minutes")
    lines.append("")
    lines.append("By Conclusion:")
    for conclusion, count in sorted(summary["by_conclusion"].items()):
        emoji = "✅" if conclusion == "success" else "❌" if conclusion in FAILED_CONCLUSIONS else "🔄"
        lines.append(f"  {emoji} {conclusion}: {count}")
    
    if summary["failed_sessions"]:
        lines.append("")
        lines.append("⚠️ Failed Sessions:")
        for s in summary["failed_sessions"][:5]:
            lines.append(f"  - Run #{s['run_number']}: {s['branch']} ({s['conclusion']})")
    
    lines.append("=" * 50)
    return "\n".join(lines)


def format_reactions(reactions: List[Dict[str, str]]) -> str:
    """Format reactions as readable text."""
    if not reactions:
        return "✅ No failed sessions require attention."
    
    lines = []
    lines.append("\n🔧 REACTIONS TO FAILED SESSIONS")
    lines.append("=" * 60)
    
    for r in reactions:
        lines.append(f"\n📌 Run ID: {r['run_id']} (Branch: {r['branch']})")
        lines.append(f"   Conclusion: {r['conclusion']}")
        lines.append(f"   Suggestion:\n{r['suggestion']}")
        lines.append(f"   Recommended Action: {r['action']}")
        lines.append("-" * 60)
    
    return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="View and react to failed/timed-out Copilot agent sessions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List recent sessions",
    )
    parser.add_argument(
        "--failed", "-f",
        action="store_true",
        help="Show only failed/timed-out sessions",
    )
    parser.add_argument(
        "--summary", "-s",
        action="store_true",
        help="Show summary statistics",
    )
    parser.add_argument(
        "--react", "-r",
        action="store_true",
        help="React to failed sessions with suggestions",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--limit", "-n",
        type=int,
        default=30,
        help="Number of sessions to fetch (default: 30)",
    )
    
    args = parser.parse_args()
    
    # Default to --list if no action specified
    if not any([args.list, args.failed, args.summary, args.react]):
        args.list = True
    
    viewer = AgentSessionViewer()
    
    if args.summary:
        summary = viewer.get_summary(limit=args.limit)
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print(format_summary(summary))
    
    elif args.react:
        sessions = viewer.get_sessions(limit=args.limit, failed_only=True)
        reactions = viewer.react_to_failures(sessions)
        if args.json:
            print(json.dumps(reactions, indent=2))
        else:
            print(format_reactions(reactions))
    
    else:
        # --list or --failed
        sessions = viewer.get_sessions(limit=args.limit, failed_only=args.failed)
        if args.json:
            print(json.dumps([asdict(s) for s in sessions], indent=2))
        else:
            print(format_session_table(sessions))
            if args.failed and sessions:
                print(f"\n⚠️ Found {len(sessions)} failed/timed-out sessions")


if __name__ == "__main__":
    main()
