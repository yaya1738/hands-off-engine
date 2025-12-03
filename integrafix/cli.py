#!/usr/bin/env python3
"""
INTEGRAFIX CLI - Unified Command Interface
==========================================

Full CLI for the hands-off-engine with:

1. DUAL SESSIONS
   - Trading Session: Market monitoring, signal generation, execution
   - Dev Session: GitHub integration, code management, CI/CD

2. GITHUB AGENTS
   - Issue tracking & auto-labeling
   - PR management & auto-review
   - Commit automation
   - Branch workflow orchestration

3. AUTOMATIONS
   - Cron job management
   - Background daemon control
   - Health monitoring
   - Self-healing triggers

Commands:
  integrafix status          - Full system status
  integrafix session trading - Start trading session
  integrafix session dev     - Start dev session
  integrafix github sync     - Sync with GitHub
  integrafix auto run        - Run all automations
  integrafix bridge <name>   - Run specific bridge
  integrafix map             - Show system map
  integrafix health          - Health check

Serving: Yair Siegel
"""

import json
import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum
import threading
import time

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
INTEGRAFIX_DIR = PROJECT_ROOT / "integrafix"


# =============================================================================
# SESSION TYPES
# =============================================================================

class SessionType(Enum):
    TRADING = "trading"
    DEV = "dev"
    DUAL = "dual"


class SessionState:
    """Track session state."""

    def __init__(self):
        self.state_path = STATE_DIR / "integrafix_session.json"
        self.state = self._load()

    def _load(self) -> Dict:
        if self.state_path.exists():
            with open(self.state_path) as f:
                return json.load(f)
        return {
            "active_sessions": [],
            "last_trading_session": None,
            "last_dev_session": None,
            "github_sync_at": None,
            "automations_last_run": None,
        }

    def save(self):
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        with open(self.state_path, 'w') as f:
            json.dump(self.state, f, indent=2)

    def start_session(self, session_type: SessionType):
        if session_type.value not in self.state["active_sessions"]:
            self.state["active_sessions"].append(session_type.value)
        self.state[f"last_{session_type.value}_session"] = datetime.now(timezone.utc).isoformat()
        self.save()

    def end_session(self, session_type: SessionType):
        if session_type.value in self.state["active_sessions"]:
            self.state["active_sessions"].remove(session_type.value)
        self.save()

    def get_active(self) -> List[str]:
        return self.state.get("active_sessions", [])


# =============================================================================
# GITHUB AGENTS
# =============================================================================

class GitHubAgent:
    """GitHub automation agent."""

    def __init__(self):
        self.repo_path = PROJECT_ROOT
        self.remote = "origin"
        self.main_branch = "main"

    def _run_git(self, *args) -> Dict:
        """Run git command and return result."""
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _run_gh(self, *args) -> Dict:
        """Run gh CLI command."""
        try:
            result = subprocess.run(
                ["gh"] + list(args),
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_status(self) -> Dict:
        """Get git status."""
        status = self._run_git("status", "--porcelain")
        branch = self._run_git("branch", "--show-current")
        remote = self._run_git("remote", "get-url", "origin")

        modified = []
        untracked = []

        if status["success"]:
            for line in status["stdout"].split("\n"):
                if line.startswith(" M") or line.startswith("M "):
                    modified.append(line[3:])
                elif line.startswith("??"):
                    untracked.append(line[3:])

        return {
            "branch": branch.get("stdout", "unknown"),
            "remote": remote.get("stdout", "unknown"),
            "modified_files": len(modified),
            "untracked_files": len(untracked),
            "files": {
                "modified": modified[:10],
                "untracked": untracked[:10]
            }
        }

    def sync(self) -> Dict:
        """Sync with remote."""
        results = []

        # Fetch
        fetch = self._run_git("fetch", "--all")
        results.append({"action": "fetch", **fetch})

        # Status check
        status = self._run_git("status", "-uno")
        results.append({"action": "status", **status})

        return {
            "success": all(r.get("success") for r in results),
            "actions": results
        }

    def list_issues(self, state: str = "open", limit: int = 10) -> Dict:
        """List GitHub issues."""
        result = self._run_gh("issue", "list", "--state", state, "--limit", str(limit), "--json",
                             "number,title,labels,createdAt")
        if result["success"] and result["stdout"]:
            try:
                issues = json.loads(result["stdout"])
                return {"success": True, "issues": issues}
            except:
                pass
        return {"success": False, "issues": []}

    def list_prs(self, state: str = "open", limit: int = 10) -> Dict:
        """List pull requests."""
        result = self._run_gh("pr", "list", "--state", state, "--limit", str(limit), "--json",
                             "number,title,state,createdAt,headRefName")
        if result["success"] and result["stdout"]:
            try:
                prs = json.loads(result["stdout"])
                return {"success": True, "prs": prs}
            except:
                pass
        return {"success": False, "prs": []}

    def create_commit(self, message: str, files: List[str] = None) -> Dict:
        """Create a commit."""
        if files:
            for f in files:
                self._run_git("add", f)
        else:
            self._run_git("add", "-A")

        return self._run_git("commit", "-m", message)

    def create_pr(self, title: str, body: str, base: str = "main") -> Dict:
        """Create a pull request."""
        return self._run_gh("pr", "create", "--title", title, "--body", body, "--base", base)

    def auto_label_issues(self) -> Dict:
        """Auto-label issues based on content."""
        issues_result = self.list_issues()
        if not issues_result["success"]:
            return {"success": False, "labeled": 0}

        labeled = []
        label_rules = {
            "bug": ["error", "crash", "fail", "broken", "fix"],
            "enhancement": ["feature", "add", "improve", "new"],
            "documentation": ["doc", "readme", "guide"],
            "integrafix": ["integrafix", "bridge", "wire"],
            "trading": ["trade", "market", "position", "polymarket"],
        }

        for issue in issues_result["issues"]:
            title = issue.get("title", "").lower()
            current_labels = [l.get("name", "") for l in issue.get("labels", [])]

            for label, keywords in label_rules.items():
                if label not in current_labels and any(kw in title for kw in keywords):
                    result = self._run_gh("issue", "edit", str(issue["number"]), "--add-label", label)
                    if result["success"]:
                        labeled.append({"issue": issue["number"], "label": label})

        return {"success": True, "labeled": len(labeled), "details": labeled}


# =============================================================================
# AUTOMATION ORCHESTRATOR
# =============================================================================

class AutomationOrchestrator:
    """Orchestrate all automations."""

    def __init__(self):
        self.automations = {
            "health_check": self._health_check,
            "bridge_sync": self._bridge_sync,
            "cron_verify": self._cron_verify,
            "daemon_check": self._daemon_check,
        }

    def _health_check(self) -> Dict:
        """Run health checks."""
        checks = {}

        # Check key modules import
        modules = [
            "autonomous.self_healer",
            "autonomous.hardware_brain",
            "integrafix.outcome_tracker",
            "integrafix.yair_abcfc_bridge",
        ]

        for mod in modules:
            try:
                __import__(mod)
                checks[mod] = "ok"
            except Exception as e:
                checks[mod] = f"fail: {str(e)[:50]}"

        return {
            "success": all("ok" in v for v in checks.values()),
            "checks": checks
        }

    def _bridge_sync(self) -> Dict:
        """Sync all INTEGRAFIX bridges."""
        bridges = list(INTEGRAFIX_DIR.glob("*.py"))
        bridge_names = [b.stem for b in bridges if not b.stem.startswith("_")]

        synced = []
        for name in bridge_names[:5]:  # Limit to 5
            try:
                mod = __import__(f"integrafix.{name}", fromlist=[name])
                if hasattr(mod, "get_status"):
                    status = mod.get_status()
                    synced.append({"bridge": name, "status": "synced"})
                else:
                    synced.append({"bridge": name, "status": "no get_status"})
            except Exception as e:
                synced.append({"bridge": name, "status": f"error: {str(e)[:30]}"})

        return {"success": True, "bridges_synced": len(synced), "details": synced}

    def _cron_verify(self) -> Dict:
        """Verify cron jobs."""
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                timeout=10
            )
            lines = [l for l in result.stdout.split("\n") if l.strip() and not l.startswith("#")]
            integrafix_jobs = [l for l in lines if "integrafix" in l.lower()]

            return {
                "success": True,
                "total_jobs": len(lines),
                "integrafix_jobs": len(integrafix_jobs)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _daemon_check(self) -> Dict:
        """Check background daemons."""
        daemons = ["hardware_brain", "self_healer", "backend_loop"]
        running = []

        for daemon in daemons:
            try:
                result = subprocess.run(
                    ["pgrep", "-f", daemon],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    running.append(daemon)
            except:
                pass

        return {
            "success": len(running) > 0,
            "running": running,
            "expected": daemons
        }

    def run_all(self) -> Dict:
        """Run all automations."""
        results = {}
        for name, func in self.automations.items():
            try:
                results[name] = func()
            except Exception as e:
                results[name] = {"success": False, "error": str(e)}

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total": len(results),
            "passed": sum(1 for r in results.values() if r.get("success")),
            "results": results
        }


# =============================================================================
# TRADING SESSION
# =============================================================================

class TradingSession:
    """Trading session manager."""

    def __init__(self):
        self.active = False
        self.start_time = None

    def start(self) -> Dict:
        """Start trading session."""
        self.active = True
        self.start_time = datetime.now(timezone.utc)

        # Initialize components
        components = {
            "market_data": False,
            "wisdom_engine": False,
            "outcome_tracker": False,
            "abcfc_bridge": False,
        }

        try:
            from trading.market_data_pipeline import MarketDataPipeline
            components["market_data"] = True
        except:
            pass

        try:
            from autonomous.yair_wisdom_engine import YairWisdomEngine
            components["wisdom_engine"] = True
        except:
            pass

        try:
            from integrafix.outcome_tracker import get_tracker
            components["outcome_tracker"] = True
        except:
            pass

        try:
            from integrafix.yair_abcfc_bridge import get_bridge
            components["abcfc_bridge"] = True
        except:
            pass

        return {
            "session": "trading",
            "started_at": self.start_time.isoformat(),
            "components": components,
            "ready": all(components.values())
        }

    def get_signals(self) -> Dict:
        """Get current trading signals."""
        signals = []

        try:
            from autonomous.yair_wisdom_engine import YairWisdomEngine
            wisdom = YairWisdomEngine()

            # Get merge arbs
            arbs = wisdom.scan_merge_arbitrage()
            for arb in arbs[:3]:
                signals.append({
                    "type": "merge_arb",
                    "market": arb["market"][:40],
                    "profit": arb["profit_per_pair"],
                    "teaching": "YES + NO < $1"
                })

            # Get new market edges
            edges = wisdom.find_new_market_edge()
            for edge in edges[:3]:
                signals.append({
                    "type": "thin_book",
                    "market": edge["market"][:40],
                    "spread_bps": edge["spread_bps"],
                    "teaching": "Thin books = easier fills"
                })
        except Exception as e:
            signals.append({"type": "error", "message": str(e)})

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "signal_count": len(signals),
            "signals": signals
        }


# =============================================================================
# DEV SESSION
# =============================================================================

class DevSession:
    """Development session manager."""

    def __init__(self):
        self.active = False
        self.github = GitHubAgent()

    def start(self) -> Dict:
        """Start dev session."""
        self.active = True

        # Get git status
        git_status = self.github.get_status()

        # Get issues
        issues = self.github.list_issues(limit=5)

        # Get PRs
        prs = self.github.list_prs(limit=5)

        return {
            "session": "dev",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "git": git_status,
            "issues": issues.get("issues", [])[:3],
            "prs": prs.get("prs", [])[:3],
        }

    def sync(self) -> Dict:
        """Sync with GitHub."""
        return self.github.sync()


# =============================================================================
# INTEGRAFIX CLI
# =============================================================================

class IntegraFixCLI:
    """Main CLI interface."""

    def __init__(self):
        self.session_state = SessionState()
        self.github = GitHubAgent()
        self.automations = AutomationOrchestrator()
        self.trading = TradingSession()
        self.dev = DevSession()

    def status(self) -> Dict:
        """Get full system status."""
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_sessions": self.session_state.get_active(),
        }

        # Git status
        status["git"] = self.github.get_status()

        # Bridge count
        bridges = list(INTEGRAFIX_DIR.glob("*.py"))
        status["bridges"] = {
            "count": len([b for b in bridges if not b.stem.startswith("_")]),
            "path": str(INTEGRAFIX_DIR)
        }

        # Quick health
        status["health"] = self.automations._health_check()

        return status

    def session_command(self, session_type: str, action: str = "start") -> Dict:
        """Handle session commands."""
        if session_type == "trading":
            if action == "start":
                self.session_state.start_session(SessionType.TRADING)
                return self.trading.start()
            elif action == "signals":
                return self.trading.get_signals()

        elif session_type == "dev":
            if action == "start":
                self.session_state.start_session(SessionType.DEV)
                return self.dev.start()
            elif action == "sync":
                return self.dev.sync()

        elif session_type == "dual":
            # Start both sessions
            self.session_state.start_session(SessionType.TRADING)
            self.session_state.start_session(SessionType.DEV)

            trading_result = self.trading.start()
            dev_result = self.dev.start()

            return {
                "sessions": ["trading", "dev"],
                "trading": trading_result,
                "dev": dev_result
            }

        return {"error": f"Unknown session type: {session_type}"}

    def github_command(self, action: str) -> Dict:
        """Handle GitHub commands."""
        if action == "sync":
            return self.github.sync()
        elif action == "status":
            return self.github.get_status()
        elif action == "issues":
            return self.github.list_issues()
        elif action == "prs":
            return self.github.list_prs()
        elif action == "auto-label":
            return self.github.auto_label_issues()
        else:
            return {"error": f"Unknown GitHub action: {action}"}

    def auto_command(self, action: str) -> Dict:
        """Handle automation commands."""
        if action == "run":
            return self.automations.run_all()
        elif action == "health":
            return self.automations._health_check()
        elif action == "cron":
            return self.automations._cron_verify()
        elif action == "daemons":
            return self.automations._daemon_check()
        else:
            return {"error": f"Unknown automation action: {action}"}

    def bridge_command(self, bridge_name: str) -> Dict:
        """Run a specific bridge."""
        try:
            mod = __import__(f"integrafix.{bridge_name}", fromlist=[bridge_name])

            if hasattr(mod, "get_status"):
                return {"bridge": bridge_name, "status": mod.get_status()}
            elif hasattr(mod, "main"):
                mod.main()
                return {"bridge": bridge_name, "status": "executed main()"}
            else:
                return {"bridge": bridge_name, "status": "loaded (no get_status or main)"}
        except Exception as e:
            return {"bridge": bridge_name, "error": str(e)}

    def map_command(self) -> Dict:
        """Show system map."""
        try:
            from integrafix.system_map import get_system_map
            smap = get_system_map()
            report = smap.generate_report()
            return {
                "summary": report["summary"],
                "scores": report["scores"],
                "entry_points": report["entry_points"]
            }
        except Exception as e:
            return {"error": str(e)}

    def print_status(self):
        """Print formatted status."""
        status = self.status()

        print("=" * 70)
        print("INTEGRAFIX CLI - System Status")
        print(f"Time: {status['timestamp']}")
        print("=" * 70)

        # Sessions
        sessions = status.get("active_sessions", [])
        print(f"\nACTIVE SESSIONS: {', '.join(sessions) if sessions else 'None'}")

        # Git
        git = status.get("git", {})
        print(f"\nGIT:")
        print(f"  Branch: {git.get('branch', 'unknown')}")
        print(f"  Modified: {git.get('modified_files', 0)} files")
        print(f"  Untracked: {git.get('untracked_files', 0)} files")

        # Bridges
        bridges = status.get("bridges", {})
        print(f"\nINTEGRAFIX BRIDGES: {bridges.get('count', 0)}")

        # Health
        health = status.get("health", {})
        health_icon = "[+]" if health.get("success") else "[-]"
        print(f"\nHEALTH: {health_icon}")
        for mod, check in health.get("checks", {}).items():
            icon = "[+]" if check == "ok" else "[-]"
            print(f"  {icon} {mod.split('.')[-1]}")

        print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="INTEGRAFIX CLI - Unified Command Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  integrafix status                  - Full system status
  integrafix session trading         - Start trading session
  integrafix session dev             - Start dev session
  integrafix session dual            - Start both sessions
  integrafix github sync             - Sync with GitHub
  integrafix github issues           - List issues
  integrafix github auto-label       - Auto-label issues
  integrafix auto run                - Run all automations
  integrafix auto health             - Health check
  integrafix bridge outcome_tracker  - Run specific bridge
  integrafix map                     - Show system map
        """
    )

    parser.add_argument("command", choices=[
        "status", "session", "github", "auto", "bridge", "map", "health"
    ], help="Command to run")

    parser.add_argument("subcommand", nargs="?", help="Subcommand")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    cli = IntegraFixCLI()

    # Execute command
    if args.command == "status":
        if args.json:
            print(json.dumps(cli.status(), indent=2))
        else:
            cli.print_status()

    elif args.command == "session":
        sub = args.subcommand or "trading"
        result = cli.session_command(sub)
        print(json.dumps(result, indent=2))

    elif args.command == "github":
        sub = args.subcommand or "status"
        result = cli.github_command(sub)
        print(json.dumps(result, indent=2))

    elif args.command == "auto":
        sub = args.subcommand or "run"
        result = cli.auto_command(sub)
        print(json.dumps(result, indent=2))

    elif args.command == "bridge":
        if not args.subcommand:
            # List bridges
            bridges = list(INTEGRAFIX_DIR.glob("*.py"))
            print("Available bridges:")
            for b in bridges:
                if not b.stem.startswith("_"):
                    print(f"  - {b.stem}")
        else:
            result = cli.bridge_command(args.subcommand)
            print(json.dumps(result, indent=2))

    elif args.command == "map":
        result = cli.map_command()
        print(json.dumps(result, indent=2))

    elif args.command == "health":
        result = cli.auto_command("health")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
