#!/usr/bin/env python3
"""
Get GitHub Actions runner registration token.

Outputs a registration token that can be used to register a self-hosted runner.
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
    print("ERROR: requests library not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)


def log_action(action: str, status: str, details: Dict[str, Any] = None):
    """Log configuration action to audit trail."""
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "github_setup.jsonl"
    
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "script": "get_runner_token",
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
    github_repo = os.environ.get("GITHUB_REPOSITORY")
    if github_repo and "/" in github_repo:
        owner, repo = github_repo.split("/", 1)
        return owner, repo
    
    try:
        import subprocess
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True
        )
        remote_url = result.stdout.strip()
        if "github.com" in remote_url:
            parts = remote_url.replace(".git", "").split("/")
            repo = parts[-1]
            owner = parts[-2].split(":")[-1]
            return owner, repo
    except Exception as e:
        print(f"Warning: Could not parse git remote: {e}", file=sys.stderr)
    
    return None, None


def get_runner_registration_token(token: str, owner: str, repo: str) -> str:
    """Get a runner registration token from GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runners/registration-token"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    log_action("get_runner_token", "started", {"owner": owner, "repo": repo})
    
    try:
        response = requests.post(url, headers=headers)
        
        if response.status_code == 201:
            data = response.json()
            runner_token = data.get("token")
            expires_at = data.get("expires_at")
            
            print(f"✅ Runner registration token obtained", file=sys.stderr)
            print(f"   Expires at: {expires_at}", file=sys.stderr)
            
            log_action("get_runner_token", "success", {
                "owner": owner,
                "repo": repo,
                "expires_at": expires_at
            })
            
            # Output token to stdout (for capture by calling script)
            print(runner_token)
            return runner_token
            
        elif response.status_code == 403:
            error_msg = response.json().get("message", "Permission denied")
            print(f"❌ Permission denied: {error_msg}", file=sys.stderr)
            print("   This operation requires admin access to the repository.", file=sys.stderr)
            log_action("get_runner_token", "permission_denied", {
                "owner": owner,
                "repo": repo,
                "error": error_msg
            })
            sys.exit(1)
        else:
            error_msg = response.json().get("message", "Unknown error")
            print(f"❌ Failed to get runner token: {error_msg}", file=sys.stderr)
            print(f"   Status code: {response.status_code}", file=sys.stderr)
            log_action("get_runner_token", "failed", {
                "owner": owner,
                "repo": repo,
                "status_code": response.status_code,
                "error": error_msg
            })
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}", file=sys.stderr)
        log_action("get_runner_token", "error", {
            "owner": owner,
            "repo": repo,
            "error": str(e)
        })
        sys.exit(1)


def main():
    """Main entry point."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("ADMIN_TOKEN")
    if not token:
        print("❌ ERROR: GITHUB_TOKEN or ADMIN_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    owner, repo = get_github_info()
    if not owner or not repo:
        print("❌ ERROR: Could not determine repository owner/name", file=sys.stderr)
        sys.exit(1)
    
    get_runner_registration_token(token, owner, repo)


if __name__ == "__main__":
    main()
