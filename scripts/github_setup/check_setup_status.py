#!/usr/bin/env python3
"""
Check status of GitHub repository configuration.

Returns JSON with current state of:
- Branch protection
- Environments
- Security features
- Project boards
- Self-hosted runners
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
    print(json.dumps({"error": "requests library not installed"}))
    sys.exit(1)


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
    except Exception:
        pass
    
    return None, None


def check_branch_protection(token: str, owner: str, repo: str, branch: str = "main") -> Dict[str, Any]:
    """Check branch protection status."""
    url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}/protection"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return {
                "enabled": True,
                "status_checks": bool(data.get("required_status_checks")),
                "pr_reviews": bool(data.get("required_pull_request_reviews")),
                "no_force_push": not data.get("allow_force_pushes", {}).get("enabled", True),
                "no_deletions": not data.get("allow_deletions", {}).get("enabled", True)
            }
        elif response.status_code == 404:
            return {"enabled": False, "error": "Branch protection not configured"}
        else:
            return {"enabled": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"enabled": False, "error": str(e)}


def check_environments(token: str, owner: str, repo: str) -> Dict[str, Any]:
    """Check environments status."""
    url = f"https://api.github.com/repos/{owner}/{repo}/environments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            envs = {env["name"]: True for env in data.get("environments", [])}
            return {
                "staging": envs.get("staging", False),
                "production": envs.get("production", False),
                "total": len(envs)
            }
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def check_security_features(token: str, owner: str, repo: str) -> Dict[str, Any]:
    """Check security features status."""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            security = data.get("security_and_analysis", {})
            
            return {
                "secret_scanning": security.get("secret_scanning", {}).get("status") == "enabled",
                "secret_scanning_push_protection": security.get("secret_scanning_push_protection", {}).get("status") == "enabled",
                "dependabot_alerts": bool(data.get("has_vulnerability_alerts")),
            }
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def check_runners(token: str, owner: str, repo: str) -> Dict[str, Any]:
    """Check self-hosted runners status."""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runners"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            runners = data.get("runners", [])
            
            return {
                "total": len(runners),
                "online": sum(1 for r in runners if r.get("status") == "online"),
                "offline": sum(1 for r in runners if r.get("status") == "offline"),
                "runners": [
                    {
                        "name": r.get("name"),
                        "status": r.get("status"),
                        "labels": [l["name"] for l in r.get("labels", [])]
                    }
                    for r in runners
                ]
            }
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def main():
    """Main entry point."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("ADMIN_TOKEN")
    if not token:
        result = {
            "error": "GITHUB_TOKEN or ADMIN_TOKEN environment variable not set",
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)
    
    owner, repo = get_github_info()
    if not owner or not repo:
        result = {
            "error": "Could not determine repository owner/name",
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)
    
    # Check all configuration items
    status = {
        "repository": f"{owner}/{repo}",
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "branch_protection": check_branch_protection(token, owner, repo),
        "environments": check_environments(token, owner, repo),
        "security": check_security_features(token, owner, repo),
        "runners": check_runners(token, owner, repo)
    }
    
    # Output JSON
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
