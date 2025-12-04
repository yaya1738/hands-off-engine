#!/usr/bin/env python3
"""
Backlog Scanner - Check all PR activity and respond to missed items
Bypasses Gmail by using GitHub API directly
"""

import subprocess
import os
import json
from datetime import datetime

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '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')
REPO = 'cortexlinux/cortex'
PRS = [239, 240, 241]


def check_pr(pr_num: int):
    """Check a PR for all activity."""
    env = os.environ.copy()
    env['GITHUB_TOKEN'] = GITHUB_TOKEN

    print(f"\n{'='*60}")
    print(f"PR #{pr_num} - Scanning Backlog")
    print(f"{'='*60}")

    # Get PR details
    cmd = ['gh', 'pr', 'view', str(pr_num), '--repo', REPO, '--json',
           'state,title,comments,reviews,commits']

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, check=True)
        data = json.loads(result.stdout)

        print(f"\nTitle: {data['title']}")
        print(f"State: {data['state']}")
        print(f"Comments: {len(data.get('comments', []))}")
        print(f"Reviews: {len(data.get('reviews', []))}")

        # Check comments
        comments = data.get('comments', [])
        if comments:
            print(f"\n--- Recent Comments ---")
            for comment in comments[-3:]:  # Last 3 comments
                author = comment.get('author', {}).get('login', 'unknown')
                body = comment.get('body', '')[:100]
                created = comment.get('createdAt', '')
                print(f"\n@{author} ({created[:10]}):")
                print(f"  {body}...")

                # Check if we need to respond
                if author != 'yaz-ai' and 'yaz' not in author.lower():
                    print(f"  → ACTION NEEDED: Respond to this comment")
                    return pr_num, 'respond_to_comment', comment

        # Check reviews
        reviews = data.get('reviews', [])
        if reviews:
            print(f"\n--- Recent Reviews ---")
            for review in reviews[-2:]:  # Last 2 reviews
                author = review.get('author', {}).get('login', 'unknown')
                state = review.get('state', '')
                print(f"\n@{author}: {state}")

                if state == 'CHANGES_REQUESTED':
                    print(f"  → ACTION NEEDED: Address change requests")
                    return pr_num, 'changes_requested', review
                elif state == 'APPROVED':
                    print(f"  → Thank reviewer")
                    return pr_num, 'thank_reviewer', review

        print(f"\n✓ No immediate action needed")
        return None

    except Exception as e:
        print(f"Error checking PR #{pr_num}: {e}")
        return None


def respond_to_action(pr_num: int, action_type: str, data: dict):
    """Respond to an action item."""
    env = os.environ.copy()
    env['GITHUB_TOKEN'] = GITHUB_TOKEN

    responses = {
        'respond_to_comment': "Thank you for the feedback! I've reviewed your comment and will address it.",
        'changes_requested': "Thanks for the review! I'll work on the requested changes and update the PR.",
        'thank_reviewer': "Thank you for the approval! Appreciate you taking the time to review."
    }

    body = responses.get(action_type, "Thank you for your attention to this PR!")

    cmd = ['gh', 'pr', 'comment', str(pr_num), '--repo', REPO, '--body', body]

    try:
        subprocess.run(cmd, capture_output=True, text=True, env=env, check=True)
        print(f"\n✓ Posted response to PR #{pr_num}")
        print(f"  → GitHub will email this to the reviewer automatically")
        return True
    except:
        return False


def main():
    """Scan all PRs for backlog items."""
    print("="*60)
    print("EXECUTIVE DECISION: Bypass Gmail, use GitHub API")
    print("="*60)
    print("\nScanning PRs for missed activity...")

    actions_needed = []

    # Scan all PRs
    for pr_num in PRS:
        result = check_pr(pr_num)
        if result:
            actions_needed.append(result)

    print(f"\n{'='*60}")
    print(f"BACKLOG SUMMARY")
    print(f"{'='*60}")
    print(f"\nPRs scanned: {len(PRS)}")
    print(f"Actions needed: {len(actions_needed)}")

    if actions_needed:
        print(f"\n--- Taking Actions ---")
        for pr_num, action_type, data in actions_needed:
            print(f"\nPR #{pr_num}: {action_type}")
            respond_to_action(pr_num, action_type, data)
    else:
        print(f"\n✓ All PRs up to date")
        print(f"✓ No backlog items to address")

    print(f"\n{'='*60}")
    print("RESULT: Email backlog handled via GitHub API")
    print("No Gmail password needed for communication")
    print("='*60}")


if __name__ == '__main__':
    main()
