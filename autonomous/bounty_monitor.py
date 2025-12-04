#!/usr/bin/env python3
"""
Bounty PR Monitor - Autonomous PR Management
Monitors submitted PRs, responds to reviews, and tracks to payment.
"""

import os
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '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')
STATE_FILE = Path(__file__).parent.parent / 'state' / 'bounty_prs.json'

TRACKED_PRS = [
    {
        'pr_number': 239,
        'repo': 'cortexlinux/cortex',
        'bounty_value': 125,
        'title': 'KV Cache Manager',
        'issue': 223
    },
    {
        'pr_number': 240,
        'repo': 'cortexlinux/cortex',
        'bounty_value': 100,
        'title': 'LLM Device Abstraction',
        'issue': 222
    },
    {
        'pr_number': 241,
        'repo': 'cortexlinux/cortex',
        'bounty_value': 25,
        'title': 'Smart Package Search',
        'issue': 117
    }
]


def gh_api(pr_number: int, repo: str, fields: str = 'state,title,comments,reviews,updatedAt,mergeable,mergedAt'):
    """Query GitHub API for PR status."""
    cmd = [
        'gh', 'pr', 'view', str(pr_number),
        '--repo', repo,
        '--json', fields
    ]
    env = os.environ.copy()
    env['GITHUB_TOKEN'] = GITHUB_TOKEN

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode == 0:
        return json.loads(result.stdout)
    return None


def check_pr_status(pr_info: dict) -> dict:
    """Check current status of a PR."""
    pr_data = gh_api(pr_info['pr_number'], pr_info['repo'])
    if not pr_data:
        return {'status': 'error', 'message': 'Could not fetch PR data'}

    status = {
        'pr_number': pr_info['pr_number'],
        'bounty_value': pr_info['bounty_value'],
        'state': pr_data.get('state', 'UNKNOWN'),
        'mergeable': pr_data.get('mergeable', 'UNKNOWN'),
        'merged_at': pr_data.get('mergedAt'),
        'updated_at': pr_data.get('updatedAt'),
        'comment_count': len(pr_data.get('comments', [])),
        'review_count': len(pr_data.get('reviews', [])),
        'last_comment': None,
        'needs_response': False,
        'action_required': []
    }

    # Check latest comments
    comments = pr_data.get('comments', [])
    if comments:
        latest = comments[-1]
        status['last_comment'] = {
            'author': latest['author']['login'],
            'created': latest['createdAt'],
            'body_preview': latest['body'][:100]
        }

        # Check if we need to respond
        if latest['author']['login'] not in ['yaya1738', 'github-actions']:
            status['needs_response'] = True
            status['action_required'].append('Respond to latest comment')

    # Check reviews
    reviews = pr_data.get('reviews', [])
    if reviews:
        for review in reviews:
            if review.get('state') == 'CHANGES_REQUESTED':
                status['action_required'].append('Address requested changes')
                status['needs_response'] = True

    return status


def monitor_all_prs():
    """Check status of all tracked PRs."""
    results = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'total_bounty_value': sum(pr['bounty_value'] for pr in TRACKED_PRS),
        'prs': []
    }

    for pr_info in TRACKED_PRS:
        status = check_pr_status(pr_info)
        results['prs'].append(status)

        # Print status
        print(f"\nPR #{status['pr_number']} - ${status['bounty_value']}")
        print(f"  State: {status['state']}")
        print(f"  Mergeable: {status['mergeable']}")
        print(f"  Comments: {status['comment_count']}")
        print(f"  Reviews: {status['review_count']}")

        if status['needs_response']:
            print(f"  ⚠️  NEEDS RESPONSE")

        if status['action_required']:
            print(f"  📋 Actions: {', '.join(status['action_required'])}")

        if status['state'] == 'MERGED':
            print(f"  ✅ MERGED - Bounty claimable!")

    # Save state
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(results, indent=2))

    return results


def get_latest_comments(pr_number: int, repo: str, limit: int = 5):
    """Get latest comments on a PR."""
    pr_data = gh_api(pr_number, repo, 'comments')
    if not pr_data:
        return []

    comments = pr_data.get('comments', [])
    return comments[-limit:] if len(comments) > limit else comments


def respond_to_pr_comment(pr_number: int, repo: str, body: str):
    """Post a comment on a PR."""
    cmd = [
        'gh', 'pr', 'comment', str(pr_number),
        '--repo', repo,
        '--body', body
    ]
    env = os.environ.copy()
    env['GITHUB_TOKEN'] = GITHUB_TOKEN

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode == 0


def continuous_monitor(interval: int = 300):
    """Continuously monitor PRs."""
    print(f"Starting continuous PR monitor (checking every {interval}s)")
    print(f"Tracking {len(TRACKED_PRS)} PRs worth ${sum(pr['bounty_value'] for pr in TRACKED_PRS)}")

    while True:
        try:
            results = monitor_all_prs()

            # Check for actions needed
            needs_attention = [pr for pr in results['prs'] if pr.get('needs_response')]
            if needs_attention:
                print(f"\n⚠️  {len(needs_attention)} PRs need attention!")

        except Exception as e:
            print(f"Error monitoring PRs: {e}")

        time.sleep(interval)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        continuous_monitor()
    else:
        # One-time check
        monitor_all_prs()
        print(f"\nState saved to: {STATE_FILE}")
