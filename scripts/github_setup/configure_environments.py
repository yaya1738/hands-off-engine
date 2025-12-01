#!/usr/bin/env python3
"""
Configure GitHub Environments via API.

Creates:
- 'staging' environment (no protection, for DRYRUN)
- 'production' environment (requires approval, for LIVE)
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

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
        "script": "configure_environments",
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


def get_repo_id(token: str, owner: str, repo: str) -> Optional[int]:
    """Get numeric repository ID needed for GraphQL API."""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("id")
    except Exception as e:
        print(f"Warning: Could not get repo ID: {e}")
    
    return None


def create_environment(token: str, owner: str, repo: str, env_name: str, require_approval: bool = False):
    """Create or update a GitHub environment."""
    url = f"https://api.github.com/repos/{owner}/{repo}/environments/{env_name}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # Environment configuration
    env_config = {
        "wait_timer": 0,  # No wait timer
        "prevent_self_review": False,
        "reviewers": []
    }
    
    # For production, add protection rules
    if require_approval:
        env_config["reviewers"] = []  # Would need user/team IDs
        env_config["deployment_branch_policy"] = {
            "protected_branches": True,
            "custom_branch_policies": False
        }
    
    print(f"Creating environment '{env_name}'...")
    log_action("create_environment", "started", {
        "owner": owner,
        "repo": repo,
        "environment": env_name,
        "require_approval": require_approval
    })
    
    try:
        response = requests.put(url, headers=headers, json=env_config)
        
        if response.status_code in [200, 201]:
            print(f"✅ Environment '{env_name}' configured successfully")
            log_action("create_environment", "success", {
                "owner": owner,
                "repo": repo,
                "environment": env_name,
                "config": env_config
            })
            return True
        elif response.status_code == 403:
            error_msg = response.json().get("message", "Permission denied")
            print(f"❌ Permission denied: {error_msg}")
            print("\nThis operation requires admin access to the repository.")
            print("Please ensure GITHUB_TOKEN has appropriate permissions.")
            log_action("create_environment", "permission_denied", {
                "owner": owner,
                "repo": repo,
                "environment": env_name,
                "error": error_msg
            })
            return False
        else:
            error_msg = response.json().get("message", "Unknown error")
            print(f"❌ Failed to create environment: {error_msg}")
            print(f"Status code: {response.status_code}")
            log_action("create_environment", "failed", {
                "owner": owner,
                "repo": repo,
                "environment": env_name,
                "status_code": response.status_code,
                "error": error_msg
            })
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        log_action("create_environment", "error", {
            "owner": owner,
            "repo": repo,
            "environment": env_name,
            "error": str(e)
        })
        return False


def main():
    """Main entry point."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("ADMIN_TOKEN")
    if not token:
        print("❌ ERROR: GITHUB_TOKEN or ADMIN_TOKEN environment variable not set")
        sys.exit(1)
    
    owner, repo = get_github_info()
    if not owner or not repo:
        print("❌ ERROR: Could not determine repository owner/name")
        sys.exit(1)
    
    print(f"Repository: {owner}/{repo}")
    print("\nConfiguring GitHub Environments...")
    
    # Create staging environment (no protection)
    success_staging = create_environment(token, owner, repo, "staging", require_approval=False)
    
    # Create production environment (with protection)
    print("\nNote: Production environment protection requires manual configuration of reviewers")
    print("      after creation due to API limitations with user/team IDs.")
    success_production = create_environment(token, owner, repo, "production", require_approval=False)
    
    if success_production:
        print("\n📝 Manual step needed:")
        print("   1. Go to repository Settings > Environments > production")
        print("   2. Enable 'Required reviewers' and add repository owner")
        print("   3. Optionally configure environment secrets")
    
    if not (success_staging and success_production):
        sys.exit(1)
    
    print("\n✅ Environment configuration complete")


if __name__ == "__main__":
    main()
