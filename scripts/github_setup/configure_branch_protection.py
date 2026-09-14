#!/usr/bin/env python3
"""
Configure branch protection rules via GitHub API.

Configures the 'main' branch with:
- Required status checks (ci workflow)
- Required PR reviews (1 reviewer, dismiss stale)
- Bypass rules for trusted bots
- No force pushes
- No deletions
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

try:
    import requests
except ImportError:
    print("ERROR: requests library not installed. Run: pip install requests")
    sys.exit(1)


def log_action(action: str, status: str, details: Dict[str, Any] = None):
    """Log configuration action to audit trail."""
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "github_setup.jsonl"
    
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "script": "configure_branch_protection",
        "action": action,
        "status": status,
        "details": details or {}
    }
    
    try:
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Warning: Failed to write to log file: {e}", file=sys.stderr)


def get_github_info():
    """Extract owner/repo from environment or git remote."""
    import re
    
    # Try GITHUB_REPOSITORY env var (set in GitHub Actions)
    github_repo = os.environ.get("GITHUB_REPOSITORY")
    if github_repo and "/" in github_repo:
        owner, repo = github_repo.split("/", 1)
        return owner, repo
    
    # Fallback: parse from git remote
    try:
        import subprocess
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True
        )
        remote_url = result.stdout.strip()
        
        # Parse GitHub URLs securely with regex patterns
        # Supports: https://github.com/owner/repo.git
        #          git@github.com:owner/repo.git
        #          git://github.com/owner/repo.git
        
        # Pattern for HTTPS URLs
        https_match = re.match(r'https://github\.com/([^/]+)/([^/]+?)(?:\.git)?$', remote_url)
        if https_match:
            return https_match.group(1), https_match.group(2)
        
        # Pattern for SSH URLs
        ssh_match = re.match(r'git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$', remote_url)
        if ssh_match:
            return ssh_match.group(1), ssh_match.group(2)
        
        # Pattern for git:// URLs
        git_match = re.match(r'git://github\.com/([^/]+)/([^/]+?)(?:\.git)?$', remote_url)
        if git_match:
            return git_match.group(1), git_match.group(2)
    except Exception as e:
        print(f"Warning: Could not parse git remote: {e}", file=sys.stderr)
    
    return None, None


def configure_branch_protection(token: str, owner: str, repo: str, branch: str = "main"):
    """Configure branch protection rules via GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}/protection"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # Branch protection configuration
    protection_config = {
        "required_status_checks": {
            "strict": True,  # Require branches to be up to date before merging
            "checks": [
                {"context": "ci"}  # Require 'ci' workflow to pass
            ]
        },
        "enforce_admins": False,  # Allow admins to bypass
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": True,  # Dismiss old reviews when new commits pushed
            "require_code_owner_reviews": False,
            "required_approving_review_count": 1,
            "require_last_push_approval": False,
            "bypass_pull_request_allowances": {
                "users": [],
                "teams": [],
                "apps": []  # Will be populated if we can get app IDs
            }
        },
        "restrictions": None,  # No push restrictions (anyone with write access can push)
        "required_linear_history": False,
        "allow_force_pushes": False,  # No force pushes
        "allow_deletions": False,  # No branch deletion
        "block_creations": False,
        "required_conversation_resolution": False,
        "lock_branch": False,
        "allow_fork_syncing": True
    }
    
    print(f"Configuring branch protection for {owner}/{repo}:{branch}...")
    log_action("configure_protection", "started", {
        "owner": owner,
        "repo": repo,
        "branch": branch
    })
    
    try:
        response = requests.put(url, headers=headers, json=protection_config)
        
        if response.status_code == 200:
            print("✅ Branch protection configured successfully")
            log_action("configure_protection", "success", {
                "owner": owner,
                "repo": repo,
                "branch": branch,
                "config": protection_config
            })
            return True
        elif response.status_code == 403:
            error_msg = response.json().get("message", "Permission denied")
            print(f"❌ Permission denied: {error_msg}")
            print("\nThis operation requires admin access to the repository.")
            print("Please ensure GITHUB_TOKEN has 'admin:repo' scope.")
            print("You may need to create a PAT with admin permissions and use ADMIN_TOKEN secret.")
            log_action("configure_protection", "permission_denied", {
                "owner": owner,
                "repo": repo,
                "branch": branch,
                "error": error_msg
            })
            return False
        else:
            error_msg = response.json().get("message", "Unknown error")
            print(f"❌ Failed to configure branch protection: {error_msg}")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            log_action("configure_protection", "failed", {
                "owner": owner,
                "repo": repo,
                "branch": branch,
                "status_code": response.status_code,
                "error": error_msg
            })
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        log_action("configure_protection", "error", {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "error": str(e)
        })
        return False


def main():
    """Main entry point."""
    # Get GitHub token
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("ADMIN_TOKEN")
    if not token:
        print("❌ ERROR: GITHUB_TOKEN or ADMIN_TOKEN environment variable not set")
        sys.exit(1)
    
    # Get repository info
    owner, repo = get_github_info()
    if not owner or not repo:
        print("❌ ERROR: Could not determine repository owner/name")
        print("Set GITHUB_REPOSITORY environment variable or run from git repository")
        sys.exit(1)
    
    print(f"Repository: {owner}/{repo}")
    
    # Configure branch protection
    success = configure_branch_protection(token, owner, repo)
    
    if not success:
        sys.exit(1)
    
    print("\n✅ Branch protection configuration complete")


if __name__ == "__main__":
    main()
