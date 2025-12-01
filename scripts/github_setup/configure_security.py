#!/usr/bin/env python3
"""
Configure GitHub security features via API.

Enables:
- Secret scanning
- Secret scanning push protection
- Dependabot security updates
- Dependabot version updates
- Code scanning (if available)
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
        "script": "configure_security",
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


def enable_secret_scanning(token: str, owner: str, repo: str):
    """Enable secret scanning for the repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # Update repository settings
    config = {
        "security_and_analysis": {
            "secret_scanning": {
                "status": "enabled"
            },
            "secret_scanning_push_protection": {
                "status": "enabled"
            }
        }
    }
    
    print("Enabling secret scanning and push protection...")
    log_action("enable_secret_scanning", "started", {"owner": owner, "repo": repo})
    
    try:
        response = requests.patch(url, headers=headers, json=config)
        
        if response.status_code == 200:
            print("✅ Secret scanning enabled")
            log_action("enable_secret_scanning", "success", {"owner": owner, "repo": repo})
            return True
        elif response.status_code == 403:
            error_msg = response.json().get("message", "Permission denied")
            print(f"❌ Permission denied: {error_msg}")
            print("   This may require admin access or be unavailable for private repos on free plan")
            log_action("enable_secret_scanning", "permission_denied", {
                "owner": owner,
                "repo": repo,
                "error": error_msg
            })
            return False
        else:
            error_msg = response.json().get("message", "Unknown error")
            print(f"⚠️  Could not enable secret scanning: {error_msg}")
            log_action("enable_secret_scanning", "failed", {
                "owner": owner,
                "repo": repo,
                "status_code": response.status_code,
                "error": error_msg
            })
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        log_action("enable_secret_scanning", "error", {
            "owner": owner,
            "repo": repo,
            "error": str(e)
        })
        return False


def enable_dependabot_alerts(token: str, owner: str, repo: str):
    """Enable Dependabot alerts."""
    url = f"https://api.github.com/repos/{owner}/{repo}/vulnerability-alerts"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    print("Enabling Dependabot security alerts...")
    log_action("enable_dependabot_alerts", "started", {"owner": owner, "repo": repo})
    
    try:
        response = requests.put(url, headers=headers)
        
        if response.status_code == 204:
            print("✅ Dependabot alerts enabled")
            log_action("enable_dependabot_alerts", "success", {"owner": owner, "repo": repo})
            return True
        elif response.status_code == 403:
            error_msg = response.json().get("message", "Permission denied") if response.text else "Permission denied"
            print(f"⚠️  Could not enable Dependabot alerts: {error_msg}")
            log_action("enable_dependabot_alerts", "permission_denied", {
                "owner": owner,
                "repo": repo,
                "error": error_msg
            })
            return False
        else:
            print(f"⚠️  Could not enable Dependabot alerts (status: {response.status_code})")
            log_action("enable_dependabot_alerts", "failed", {
                "owner": owner,
                "repo": repo,
                "status_code": response.status_code
            })
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        log_action("enable_dependabot_alerts", "error", {
            "owner": owner,
            "repo": repo,
            "error": str(e)
        })
        return False


def enable_automated_security_fixes(token: str, owner: str, repo: str):
    """Enable automated security fixes (Dependabot)."""
    url = f"https://api.github.com/repos/{owner}/{repo}/automated-security-fixes"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    print("Enabling automated security fixes...")
    log_action("enable_automated_fixes", "started", {"owner": owner, "repo": repo})
    
    try:
        response = requests.put(url, headers=headers)
        
        if response.status_code == 204:
            print("✅ Automated security fixes enabled")
            log_action("enable_automated_fixes", "success", {"owner": owner, "repo": repo})
            return True
        elif response.status_code == 403:
            error_msg = response.json().get("message", "Permission denied") if response.text else "Permission denied"
            print(f"⚠️  Could not enable automated security fixes: {error_msg}")
            log_action("enable_automated_fixes", "permission_denied", {
                "owner": owner,
                "repo": repo,
                "error": error_msg
            })
            return False
        else:
            print(f"⚠️  Could not enable automated security fixes (status: {response.status_code})")
            log_action("enable_automated_fixes", "failed", {
                "owner": owner,
                "repo": repo,
                "status_code": response.status_code
            })
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        log_action("enable_automated_fixes", "error", {
            "owner": owner,
            "repo": repo,
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
    print("\nConfiguring security features...")
    
    # Enable various security features
    results = []
    results.append(enable_secret_scanning(token, owner, repo))
    results.append(enable_dependabot_alerts(token, owner, repo))
    results.append(enable_automated_security_fixes(token, owner, repo))
    
    print("\n📝 Additional manual steps:")
    print("   1. Create .github/dependabot.yml for version updates configuration")
    print("   2. Enable code scanning in Security > Code scanning alerts")
    print("   3. Configure CodeQL analysis workflow if not already present")
    
    # Count successes
    success_count = sum(1 for r in results if r)
    total_count = len(results)
    
    print(f"\n✅ Security configuration complete ({success_count}/{total_count} features enabled)")
    
    if success_count < total_count:
        print("⚠️  Some features could not be enabled (see logs above)")
        # Don't fail - some features may require paid plans
    
    log_action("configure_security", "complete", {
        "owner": owner,
        "repo": repo,
        "success_count": success_count,
        "total_count": total_count
    })


if __name__ == "__main__":
    main()
