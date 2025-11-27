#!/usr/bin/env python3
"""
PR Auto-Manager - Zero-touch PR management for hands-off-engine

Provides automated PR management capabilities:
1. List open PRs with status
2. Assess PR safety for auto-merge
3. Trigger PR merges via GitHub API or dispatch
4. Handle Telegram commands for PR management

This enables fully autonomous repo management where user
only needs to approve/reject via Telegram when needed.
"""

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent


class PRAutoManager:
    """Manages PRs automatically for zero-touch operation."""

    # Safe patterns that can be auto-merged without review
    SAFE_PATH_PATTERNS = [
        'docs/',
        'README',
        '.md',
        'logs/',
        'state/performance',
        'ai/coordination/',
        'tests/',
    ]

    # Risky patterns that always require approval
    RISKY_PATH_PATTERNS = [
        'executor/',
        'alpha/',
        'decider/',
        'config/',
        '.env',
        'requirements.txt',
        'package.json',
        '.github/workflows/',
        'telegram/',
    ]

    # Labels that indicate auto-merge is OK
    AUTO_MERGE_LABELS = ['auto-merge', 'safe-to-merge', 'docs-only']

    def __init__(self):
        self.gh_token = os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
        self.repo = os.getenv('GITHUB_REPOSITORY', 'yaya1738/hands-off-engine')

    def _run_gh_command(self, args: List[str]) -> Tuple[bool, str]:
        """Run a gh CLI command and return success status and output."""
        try:
            result = subprocess.run(
                ['gh'] + args,
                capture_output=True,
                text=True,
                timeout=60,
                env={**os.environ, 'GH_TOKEN': self.gh_token or ''}
            )
            return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except FileNotFoundError:
            return False, "gh CLI not installed"
        except Exception as e:
            return False, str(e)

    def list_prs(self, state: str = 'open') -> List[Dict]:
        """List PRs with their status."""
        success, output = self._run_gh_command([
            'pr', 'list',
            '--state', state,
            '--json', 'number,title,author,createdAt,labels,reviewDecision,statusCheckRollup,mergeable,headRefName',
            '--limit', '20'
        ])

        if not success:
            logger.error(f"Failed to list PRs: {output}")
            return []

        try:
            prs = json.loads(output) if output else []
            return prs
        except json.JSONDecodeError:
            logger.error(f"Failed to parse PR list: {output}")
            return []

    def get_pr_details(self, pr_number: int) -> Optional[Dict]:
        """Get detailed information about a specific PR."""
        success, output = self._run_gh_command([
            'pr', 'view', str(pr_number),
            '--json', 'number,title,body,author,state,mergeable,mergeStateStatus,reviewDecision,'
                      'statusCheckRollup,labels,changedFiles,additions,deletions,files'
        ])

        if not success:
            logger.error(f"Failed to get PR #{pr_number}: {output}")
            return None

        try:
            return json.loads(output)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse PR details: {output}")
            return None

    def assess_pr_safety(self, pr_number: int) -> Dict:
        """
        Assess if a PR is safe to auto-merge.

        Returns dict with:
            - safe: bool
            - reason: str
            - risk_level: low/medium/high
            - can_auto_merge: bool
        """
        pr = self.get_pr_details(pr_number)
        if not pr:
            return {
                'safe': False,
                'reason': 'Could not retrieve PR details',
                'risk_level': 'unknown',
                'can_auto_merge': False
            }

        # Check basic merge eligibility
        if pr.get('state') != 'OPEN':
            return {
                'safe': False,
                'reason': f"PR is not open (state: {pr.get('state')})",
                'risk_level': 'low',
                'can_auto_merge': False
            }

        if pr.get('mergeable') != 'MERGEABLE':
            return {
                'safe': False,
                'reason': 'PR has merge conflicts',
                'risk_level': 'low',
                'can_auto_merge': False
            }

        # Check labels
        labels = [l.get('name', '') for l in pr.get('labels', [])]
        has_auto_merge_label = any(l in self.AUTO_MERGE_LABELS for l in labels)
        has_do_not_merge = 'do-not-merge' in labels or 'wip' in labels

        if has_do_not_merge:
            return {
                'safe': False,
                'reason': 'PR is marked as work-in-progress or do-not-merge',
                'risk_level': 'low',
                'can_auto_merge': False
            }

        # Check review status
        review_decision = pr.get('reviewDecision')
        is_approved = review_decision == 'APPROVED'
        needs_review = review_decision in ['REVIEW_REQUIRED', 'CHANGES_REQUESTED']

        # Check CI status
        checks = pr.get('statusCheckRollup', [])
        all_checks_pass = all(
            c.get('conclusion') in ['SUCCESS', 'SKIPPED', 'NEUTRAL', None]
            for c in checks if c.get('status') == 'COMPLETED'
        )
        has_pending_checks = any(c.get('status') == 'PENDING' for c in checks)

        # Analyze changed files for risk
        files = pr.get('files', [])
        file_paths = [f.get('path', '') for f in files]

        is_docs_only = all(
            any(pattern in path for pattern in ['.md', 'docs/', 'README'])
            for path in file_paths
        )

        has_risky_files = any(
            any(pattern in path for pattern in self.RISKY_PATH_PATTERNS)
            for path in file_paths
        )

        # Determine risk level
        if is_docs_only:
            risk_level = 'low'
        elif has_risky_files:
            risk_level = 'high'
        else:
            risk_level = 'medium'

        # Determine if can auto-merge
        can_auto_merge = False
        reason = ""

        if is_approved and all_checks_pass:
            can_auto_merge = True
            reason = "PR is approved with passing checks"
        elif has_auto_merge_label and all_checks_pass and not has_risky_files:
            can_auto_merge = True
            reason = "PR has auto-merge label and passing checks"
        elif is_docs_only and all_checks_pass:
            can_auto_merge = True
            reason = "PR is docs-only with passing checks"
        elif has_pending_checks:
            reason = "PR has pending CI checks"
        elif needs_review:
            reason = "PR requires review approval"
        elif has_risky_files:
            reason = f"PR modifies risky files and needs approval"
        else:
            reason = "PR needs review or approval"

        return {
            'safe': can_auto_merge,
            'reason': reason,
            'risk_level': risk_level,
            'can_auto_merge': can_auto_merge,
            'is_approved': is_approved,
            'all_checks_pass': all_checks_pass,
            'is_docs_only': is_docs_only,
            'has_risky_files': has_risky_files,
            'file_count': len(file_paths),
            'labels': labels
        }

    def merge_pr(self, pr_number: int, method: str = 'squash') -> Dict:
        """
        Attempt to merge a PR.

        Args:
            pr_number: PR number to merge
            method: Merge method (squash, merge, rebase)

        Returns:
            Dict with success status and message
        """
        # First assess safety
        assessment = self.assess_pr_safety(pr_number)

        if not assessment['can_auto_merge']:
            return {
                'success': False,
                'message': f"Cannot auto-merge: {assessment['reason']}",
                'assessment': assessment
            }

        # Attempt merge
        success, output = self._run_gh_command([
            'pr', 'merge', str(pr_number),
            f'--{method}',
            '--admin',  # Use admin privileges if available
            '--delete-branch'
        ])

        if success:
            logger.info(f"Successfully merged PR #{pr_number}")
            return {
                'success': True,
                'message': f"PR #{pr_number} merged successfully",
                'assessment': assessment
            }
        else:
            # Try without admin flag
            success, output = self._run_gh_command([
                'pr', 'merge', str(pr_number),
                f'--{method}',
                '--delete-branch'
            ])

            if success:
                return {
                    'success': True,
                    'message': f"PR #{pr_number} merged successfully",
                    'assessment': assessment
                }
            else:
                return {
                    'success': False,
                    'message': f"Merge failed: {output}",
                    'assessment': assessment
                }

    def trigger_merge_workflow(self, pr_number: int) -> Dict:
        """
        Trigger the auto-merge workflow via repository dispatch.

        This is useful when you can't directly merge but can trigger workflows.
        """
        success, output = self._run_gh_command([
            'api',
            '--method', 'POST',
            f'/repos/{self.repo}/dispatches',
            '-f', 'event_type=merge_pr',
            '-f', f'client_payload[pr_number]={pr_number}'
        ])

        if success:
            return {
                'success': True,
                'message': f"Merge workflow triggered for PR #{pr_number}"
            }
        else:
            return {
                'success': False,
                'message': f"Failed to trigger merge workflow: {output}"
            }

    def format_pr_list_for_telegram(self, prs: List[Dict]) -> str:
        """Format PR list for Telegram message."""
        if not prs:
            return "📋 No open PRs"

        lines = [f"📋 **Open PRs** ({len(prs)})\n"]

        for pr in prs[:10]:  # Limit to 10 for Telegram
            num = pr.get('number', '?')
            title = pr.get('title', 'Unknown')[:50]
            author = pr.get('author', {}).get('login', 'unknown')
            review = pr.get('reviewDecision', 'PENDING')
            mergeable = pr.get('mergeable', 'UNKNOWN')

            # Status emoji
            if review == 'APPROVED':
                status = '✅'
            elif review == 'CHANGES_REQUESTED':
                status = '❌'
            elif mergeable == 'CONFLICTING':
                status = '⚠️'
            else:
                status = '⏳'

            lines.append(f"\n{status} **#{num}**: {title}")
            lines.append(f"   Author: {author}")

        lines.append("\n\nUse `/merge <number>` to merge a PR")

        return '\n'.join(lines)

    def format_pr_status_for_telegram(self, pr_number: int) -> str:
        """Format detailed PR status for Telegram."""
        pr = self.get_pr_details(pr_number)
        if not pr:
            return f"❌ Could not find PR #{pr_number}"

        assessment = self.assess_pr_safety(pr_number)

        risk_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}
        emoji = risk_emoji.get(assessment['risk_level'], '⚪')

        lines = [
            f"📝 **PR #{pr_number}**",
            f"**{pr.get('title', 'Unknown')}**\n",
            f"State: {pr.get('state', 'UNKNOWN')}",
            f"Mergeable: {pr.get('mergeable', 'UNKNOWN')}",
            f"Review: {pr.get('reviewDecision', 'PENDING')}",
            f"\n{emoji} Risk Level: {assessment['risk_level']}",
            f"Files Changed: {assessment.get('file_count', 0)}",
            f"\n**Assessment:** {assessment['reason']}"
        ]

        if assessment['can_auto_merge']:
            lines.append(f"\n✅ Ready to merge! Use `/merge {pr_number}`")
        else:
            lines.append(f"\n⚠️ Not ready for auto-merge")

        return '\n'.join(lines)


def main():
    """CLI for PR management."""
    import sys

    manager = PRAutoManager()

    if len(sys.argv) < 2:
        print("Usage: pr_auto_manager.py [list|status|assess|merge] [args...]")
        print("\nCommands:")
        print("  list              - List open PRs")
        print("  status <number>   - Get detailed PR status")
        print("  assess <number>   - Assess PR safety for auto-merge")
        print("  merge <number>    - Attempt to merge PR")
        return

    command = sys.argv[1]

    if command == 'list':
        prs = manager.list_prs()
        print(manager.format_pr_list_for_telegram(prs))

    elif command == 'status':
        if len(sys.argv) < 3:
            print("Usage: pr_auto_manager.py status <pr_number>")
            return
        pr_num = int(sys.argv[2])
        print(manager.format_pr_status_for_telegram(pr_num))

    elif command == 'assess':
        if len(sys.argv) < 3:
            print("Usage: pr_auto_manager.py assess <pr_number>")
            return
        pr_num = int(sys.argv[2])
        assessment = manager.assess_pr_safety(pr_num)
        print(json.dumps(assessment, indent=2))

    elif command == 'merge':
        if len(sys.argv) < 3:
            print("Usage: pr_auto_manager.py merge <pr_number>")
            return
        pr_num = int(sys.argv[2])
        result = manager.merge_pr(pr_num)
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")


if __name__ == '__main__':
    main()
