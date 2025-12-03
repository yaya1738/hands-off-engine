#!/usr/bin/env python3
"""
INTEGRAFIX: Branch Manager
==========================

Automates git branch cleanup and PR creation.

GAP FIXED: ai_no_branch_merge
- Before: 182 branches, 0 merged to main recently
- After:  Automated analysis, cleanup, and PR creation

INTEGRAFIX PRINCIPLE: Outputs need consumers (branches need merging or deletion).
"""

import subprocess
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
BRANCH_STATE = STATE_DIR / "branch_manager.json"


@dataclass
class BranchAction:
    """Action to take on a branch."""
    branch: str
    action: str  # "pr", "delete", "review", "keep"
    reason: str
    priority: int  # 1=high, 3=low
    pr_url: Optional[str] = None
    executed: bool = False
    executed_at: Optional[str] = None


class BranchManager:
    """
    Automated branch management for integrafix.

    Responsibilities:
    1. Analyze all branches
    2. Determine optimal action for each
    3. Execute actions (PRs, deletions)
    4. Track results
    """

    def __init__(self):
        self.state = self._load_state()
        self.actions: List[BranchAction] = []

    def _load_state(self) -> Dict:
        if BRANCH_STATE.exists():
            with open(BRANCH_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "branches_analyzed": 0,
            "prs_created": 0,
            "branches_deleted": 0,
            "last_cleanup": None,
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.state["actions"] = [asdict(a) for a in self.actions]
        with open(BRANCH_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _run_git(self, args: List[str]) -> str:
        """Run git command and return output."""
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        return result.stdout.strip()

    def _run_gh(self, args: List[str]) -> str:
        """Run gh command and return output."""
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        return result.stdout.strip()

    def analyze_branches(self) -> List[BranchAction]:
        """
        Analyze all branches and determine actions.
        """
        self.actions = []

        # Fetch latest
        self._run_git(["fetch", "--prune"])

        # Get all remote branches
        output = self._run_git(["branch", "-r"])
        branches = [b.strip() for b in output.split("\n") if b.strip()]
        branches = [b for b in branches if not b.startswith("origin/HEAD") and b != "origin/main"]

        self.state["branches_analyzed"] = len(branches)

        for branch in branches:
            action = self._analyze_branch(branch)
            if action:
                self.actions.append(action)

        self._save_state()
        return self.actions

    def _analyze_branch(self, branch: str) -> Optional[BranchAction]:
        """Analyze a single branch and determine action."""
        branch_name = branch.replace("origin/", "")

        # Get commits ahead of main
        commits_ahead_output = self._run_git(["rev-list", "--count", f"origin/main..{branch}"])
        try:
            commits_ahead = int(commits_ahead_output)
        except ValueError:
            commits_ahead = 0

        # Get last commit date and message
        log_output = self._run_git(["log", "-1", "--format=%ci|%s", branch])
        parts = log_output.split("|", 1)
        commit_date_str = parts[0] if parts else ""
        commit_msg = parts[1] if len(parts) > 1 else ""

        # Parse date
        try:
            commit_date = datetime.fromisoformat(commit_date_str.replace(" ", "T").split("+")[0])
            age_days = (datetime.now() - commit_date).days
        except:
            age_days = 999

        # Decision logic
        branch_lower = branch_name.lower()

        # Rule 1: No commits ahead = delete candidate
        if commits_ahead == 0:
            return BranchAction(
                branch=branch_name,
                action="delete",
                reason="No commits ahead of main - fully merged or empty",
                priority=1,
            )

        # Rule 2: Very old (>60 days) with small changes = delete
        if age_days > 60 and commits_ahead <= 2:
            return BranchAction(
                branch=branch_name,
                action="delete",
                reason=f"Stale ({age_days} days) with minimal changes ({commits_ahead} commits)",
                priority=2,
            )

        # Rule 3: Integration branches = high priority PR
        if "integra" in branch_lower or "connect" in branch_lower or "wire" in branch_lower:
            return BranchAction(
                branch=branch_name,
                action="pr",
                reason=f"Integration branch with {commits_ahead} commits - should merge",
                priority=1,
            )

        # Rule 4: Fix branches with small changes = PR
        if "fix" in branch_lower and commits_ahead <= 5:
            return BranchAction(
                branch=branch_name,
                action="pr",
                reason=f"Fix branch with {commits_ahead} commits - likely ready",
                priority=2,
            )

        # Rule 5: Claude/copilot branches with 1 commit = quick PR
        if ("claude/" in branch_lower or "copilot/" in branch_lower) and commits_ahead == 1:
            return BranchAction(
                branch=branch_name,
                action="pr",
                reason=f"AI branch with single commit - quick review",
                priority=2,
            )

        # Rule 6: Large branches = manual review
        if commits_ahead > 10:
            return BranchAction(
                branch=branch_name,
                action="review",
                reason=f"Large branch ({commits_ahead} commits) - needs manual review",
                priority=3,
            )

        # Rule 7: Recent activity = keep for now
        if age_days < 7:
            return BranchAction(
                branch=branch_name,
                action="keep",
                reason=f"Recent activity ({age_days} days ago) - keep for now",
                priority=3,
            )

        # Default: review
        return BranchAction(
            branch=branch_name,
            action="review",
            reason=f"{commits_ahead} commits, {age_days} days old - needs review",
            priority=3,
        )

    def execute_deletions(self, dry_run: bool = True) -> List[str]:
        """
        Execute branch deletions.

        Args:
            dry_run: If True, only report what would be deleted
        """
        results = []
        delete_actions = [a for a in self.actions if a.action == "delete" and not a.executed]

        for action in delete_actions:
            if dry_run:
                results.append(f"[DRY RUN] Would delete: {action.branch}")
            else:
                output = self._run_git(["push", "origin", "--delete", action.branch])
                if "error" not in output.lower():
                    action.executed = True
                    action.executed_at = datetime.now(timezone.utc).isoformat()
                    self.state["branches_deleted"] += 1
                    results.append(f"Deleted: {action.branch}")
                else:
                    results.append(f"Failed: {action.branch} - {output}")

        self._save_state()
        return results

    def create_prs(self, dry_run: bool = True, max_prs: int = 3) -> List[str]:
        """
        Create PRs for branches marked for PR.

        Args:
            dry_run: If True, only report what PRs would be created
            max_prs: Maximum PRs to create in one run
        """
        results = []
        pr_actions = [a for a in self.actions if a.action == "pr" and not a.executed]
        pr_actions = sorted(pr_actions, key=lambda a: a.priority)[:max_prs]

        for action in pr_actions:
            if dry_run:
                results.append(f"[DRY RUN] Would create PR: {action.branch}")
                results.append(f"  Reason: {action.reason}")
            else:
                # Get commit message for PR title
                log = self._run_git(["log", "-1", "--format=%s", f"origin/{action.branch}"])
                title = log[:80] if log else action.branch

                # Create PR
                output = self._run_gh([
                    "pr", "create",
                    "--head", action.branch,
                    "--base", "main",
                    "--title", title,
                    "--body", f"## Auto-generated PR\n\n{action.reason}\n\n🤖 Created by integrafix branch_manager"
                ])

                if "github.com" in output:
                    action.executed = True
                    action.executed_at = datetime.now(timezone.utc).isoformat()
                    action.pr_url = output.strip()
                    self.state["prs_created"] += 1
                    results.append(f"Created PR: {action.pr_url}")
                else:
                    results.append(f"Failed to create PR for {action.branch}: {output}")

        self._save_state()
        return results

    def get_summary(self) -> Dict:
        """Get summary of branch analysis."""
        by_action = {}
        for action in self.actions:
            if action.action not in by_action:
                by_action[action.action] = []
            by_action[action.action].append(action.branch)

        return {
            "total_branches": len(self.actions),
            "by_action": {k: len(v) for k, v in by_action.items()},
            "delete_candidates": by_action.get("delete", []),
            "pr_candidates": by_action.get("pr", []),
            "state": self.state,
        }


def main():
    """Run branch management."""
    print("=" * 70)
    print("INTEGRAFIX: BRANCH MANAGER")
    print("Automated branch cleanup and PR creation")
    print("=" * 70)
    print()

    manager = BranchManager()

    # Analyze
    print("Analyzing branches...")
    actions = manager.analyze_branches()
    print(f"Total branches analyzed: {len(actions)}")
    print()

    # Summary
    summary = manager.get_summary()
    print("Action breakdown:")
    for action_type, count in summary["by_action"].items():
        print(f"  {action_type}: {count}")
    print()

    # Show delete candidates
    print("-" * 70)
    print("DELETE CANDIDATES (no commits ahead or stale):")
    print("-" * 70)
    delete_actions = [a for a in actions if a.action == "delete"][:10]
    for action in delete_actions:
        print(f"  {action.branch}")
        print(f"    Reason: {action.reason}")
    if len(summary.get("delete_candidates", [])) > 10:
        print(f"  ... and {len(summary['delete_candidates']) - 10} more")
    print()

    # Show PR candidates
    print("-" * 70)
    print("PR CANDIDATES (valuable changes):")
    print("-" * 70)
    pr_actions = [a for a in actions if a.action == "pr"][:10]
    pr_actions = sorted(pr_actions, key=lambda a: a.priority)
    for action in pr_actions:
        print(f"  [{action.priority}] {action.branch}")
        print(f"      Reason: {action.reason}")
    if len(summary.get("pr_candidates", [])) > 10:
        print(f"  ... and {len(summary['pr_candidates']) - 10} more")
    print()

    # Dry run
    print("-" * 70)
    print("DRY RUN - What would happen:")
    print("-" * 70)
    deletions = manager.execute_deletions(dry_run=True)
    for d in deletions[:5]:
        print(f"  {d}")
    if len(deletions) > 5:
        print(f"  ... and {len(deletions) - 5} more deletions")
    print()

    prs = manager.create_prs(dry_run=True)
    for p in prs:
        print(f"  {p}")
    print()

    print("=" * 70)
    print("To execute: manager.execute_deletions(dry_run=False)")
    print("To create PRs: manager.create_prs(dry_run=False)")
    print("=" * 70)

    return manager


if __name__ == "__main__":
    main()
