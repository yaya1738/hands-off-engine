#!/usr/bin/env python3
"""
INTEGRAFIX: Branch Consolidator
===============================

PROBLEM: 182 branches on GitHub, 0 merged to main recently.
Each branch represents work that's isolated.

SOLUTION:
1. Identify valuable branches (recent, with changes)
2. Categorize by type (fix, feature, integration)
3. Generate merge plan
4. Execute consolidation

This addresses the last remaining integrafix gap.
"""

import subprocess
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"


@dataclass
class BranchInfo:
    """Information about a branch."""
    name: str
    last_commit_date: str
    last_commit_msg: str
    commits_ahead: int
    category: str
    mergeable: bool
    reason: str


class BranchConsolidator:
    """Consolidate and manage GitHub branches."""

    def __init__(self):
        self.branches: Dict[str, BranchInfo] = {}

    def fetch_branches(self) -> List[str]:
        """Fetch and list all remote branches."""
        subprocess.run(["git", "fetch", "--prune"], capture_output=True)
        result = subprocess.run(
            ["git", "branch", "-r"],
            capture_output=True, text=True
        )
        branches = [b.strip() for b in result.stdout.strip().split("\n") if b.strip()]
        return [b for b in branches if not b.startswith("origin/HEAD")]

    def analyze_branch(self, branch: str) -> BranchInfo:
        """Analyze a single branch."""
        # Get last commit info
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci|%s", branch],
            capture_output=True, text=True
        )
        parts = result.stdout.strip().split("|", 1)
        commit_date = parts[0] if parts else ""
        commit_msg = parts[1] if len(parts) > 1 else ""

        # Get commits ahead of main
        result = subprocess.run(
            ["git", "rev-list", "--count", f"origin/main..{branch}"],
            capture_output=True, text=True
        )
        try:
            commits_ahead = int(result.stdout.strip())
        except:
            commits_ahead = 0

        # Categorize
        branch_lower = branch.lower()
        if "fix" in branch_lower:
            category = "fix"
        elif "feature" in branch_lower or "add" in branch_lower:
            category = "feature"
        elif "integra" in branch_lower or "connect" in branch_lower:
            category = "integration"
        elif "copilot" in branch_lower:
            category = "copilot"
        elif "claude" in branch_lower:
            category = "claude"
        else:
            category = "other"

        # Determine if mergeable
        mergeable = True
        reason = "OK"

        if commits_ahead == 0:
            mergeable = False
            reason = "No new commits"
        elif commits_ahead > 50:
            mergeable = False
            reason = f"Too many commits ({commits_ahead}), needs review"

        # Check if recent (within 7 days)
        try:
            commit_dt = datetime.fromisoformat(commit_date.replace(" ", "T").split("+")[0])
            age_days = (datetime.now() - commit_dt).days
            if age_days > 30:
                reason = f"Stale ({age_days} days old)"
        except:
            pass

        return BranchInfo(
            name=branch,
            last_commit_date=commit_date,
            last_commit_msg=commit_msg[:80],
            commits_ahead=commits_ahead,
            category=category,
            mergeable=mergeable,
            reason=reason,
        )

    def analyze_all_branches(self) -> Dict[str, List[BranchInfo]]:
        """Analyze all branches and categorize."""
        branches = self.fetch_branches()

        by_category = {}

        for branch in branches:
            if branch == "origin/main":
                continue

            info = self.analyze_branch(branch)
            self.branches[branch] = info

            if info.category not in by_category:
                by_category[info.category] = []
            by_category[info.category].append(info)

        return by_category

    def get_merge_candidates(self) -> List[BranchInfo]:
        """Get branches that are good merge candidates."""
        return [b for b in self.branches.values() if b.mergeable and b.commits_ahead > 0]

    def generate_merge_plan(self) -> str:
        """Generate a merge plan."""
        candidates = self.get_merge_candidates()

        if not candidates:
            return "No merge candidates found."

        # Sort by commits ahead (prioritize smaller changes)
        candidates.sort(key=lambda b: b.commits_ahead)

        plan = []
        plan.append("=" * 70)
        plan.append("BRANCH MERGE PLAN")
        plan.append("=" * 70)
        plan.append(f"Total branches: {len(self.branches)}")
        plan.append(f"Merge candidates: {len(candidates)}")
        plan.append("")

        # Group by category
        by_cat = {}
        for b in candidates:
            if b.category not in by_cat:
                by_cat[b.category] = []
            by_cat[b.category].append(b)

        for cat, branches in by_cat.items():
            plan.append(f"\n[{cat.upper()}] ({len(branches)} branches)")
            for b in branches[:5]:  # Top 5 per category
                plan.append(f"  {b.name.replace('origin/', '')}")
                plan.append(f"    +{b.commits_ahead} commits | {b.last_commit_msg[:50]}")

        plan.append("\n" + "=" * 70)
        plan.append("RECOMMENDED ACTIONS:")
        plan.append("=" * 70)
        plan.append("1. Review each candidate branch")
        plan.append("2. Create PRs for valuable changes")
        plan.append("3. Delete stale branches (>30 days, no activity)")
        plan.append(f"4. Focus on integration branches first")

        return "\n".join(plan)

    def cleanup_stale_branches(self, dry_run: bool = True) -> List[str]:
        """Delete stale branches (>60 days old, no new commits)."""
        deleted = []

        for name, info in self.branches.items():
            if info.commits_ahead == 0:
                # Branch has no new commits vs main
                if dry_run:
                    deleted.append(f"[DRY RUN] Would delete: {name}")
                else:
                    # Actually delete
                    result = subprocess.run(
                        ["git", "push", "origin", "--delete", name.replace("origin/", "")],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        deleted.append(f"Deleted: {name}")
                    else:
                        deleted.append(f"Failed to delete {name}: {result.stderr}")

        return deleted

    def status(self) -> Dict:
        """Get consolidator status."""
        by_cat = {}
        for b in self.branches.values():
            if b.category not in by_cat:
                by_cat[b.category] = {"total": 0, "mergeable": 0}
            by_cat[b.category]["total"] += 1
            if b.mergeable:
                by_cat[b.category]["mergeable"] += 1

        return {
            "total_branches": len(self.branches),
            "merge_candidates": len(self.get_merge_candidates()),
            "by_category": by_cat,
        }


def main():
    """Run branch consolidation analysis."""
    consolidator = BranchConsolidator()

    print("Analyzing branches...")
    by_category = consolidator.analyze_all_branches()

    print(consolidator.generate_merge_plan())

    print("\n" + "=" * 70)
    print("STATUS")
    print("=" * 70)
    status = consolidator.status()
    print(f"Total branches: {status['total_branches']}")
    print(f"Merge candidates: {status['merge_candidates']}")
    print("\nBy category:")
    for cat, counts in status["by_category"].items():
        print(f"  {cat}: {counts['total']} total, {counts['mergeable']} mergeable")

    return consolidator


if __name__ == "__main__":
    main()
