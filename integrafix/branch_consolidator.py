#!/usr/bin/env python3
"""Legacy branch consolidator compatibility facade.

Branch fetching, repository mutation, branch deletion, and merge orchestration
belong to FactoryAuthorityGateway. This module provides only deterministic
read-only classification helpers and fails closed for privileged operations.
"""

from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List

_AUTHORITY = "FactoryAuthorityGateway"


@dataclass
class BranchInfo:
    name: str
    last_commit_date: str
    last_commit_msg: str
    commits_ahead: int
    category: str
    mergeable: bool
    reason: str


class BranchConsolidator:
    """Read-only compatibility facade for branch consolidation."""

    def __init__(self):
        self.branches: Dict[str, BranchInfo] = {}

    def fetch_branches(self) -> List[str]:
        """Legacy repository inspection is disabled; use the governed authority."""
        print(f"[FACTORY-AUTHORITY] branch discovery requires {_AUTHORITY}.")
        return []

    def analyze_branch(self, branch: str) -> BranchInfo:
        """Classify a supplied branch name without querying or mutating Git."""
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
        return BranchInfo(
            name=branch,
            last_commit_date="",
            last_commit_msg="",
            commits_ahead=0,
            category=category,
            mergeable=False,
            reason=f"Repository inspection requires {_AUTHORITY}",
        )

    def analyze_all_branches(self) -> Dict[str, List[BranchInfo]]:
        self.fetch_branches()
        return {}

    def get_merge_candidates(self) -> List[BranchInfo]:
        return [b for b in self.branches.values() if b.mergeable and b.commits_ahead > 0]

    def generate_merge_plan(self) -> str:
        candidates = self.get_merge_candidates()
        if not candidates:
            return f"No merge candidates available; repository inspection requires {_AUTHORITY}."
        return "\n".join(["BRANCH MERGE PLAN", *[f"  {b.name}" for b in candidates]])

    def cleanup_stale_branches(self, dry_run: bool = True) -> List[str]:
        """Never delete branches through this legacy path."""
        print(f"[FACTORY-AUTHORITY] branch cleanup requires {_AUTHORITY}.")
        return []

    def status(self) -> Dict:
        by_cat = {}
        for b in self.branches.values():
            entry = by_cat.setdefault(b.category, {"total": 0, "mergeable": 0})
            entry["total"] += 1
            entry["mergeable"] += int(b.mergeable)
        return {
            "total_branches": len(self.branches),
            "merge_candidates": len(self.get_merge_candidates()),
            "by_category": by_cat,
            "authority_required": True,
        }


def main():
    consolidator = BranchConsolidator()
    consolidator.analyze_all_branches()
    print(consolidator.generate_merge_plan())
    print(consolidator.status())
    return consolidator


if __name__ == "__main__":
    main()
