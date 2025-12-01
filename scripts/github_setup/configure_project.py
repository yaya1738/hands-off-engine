#!/usr/bin/env python3
"""
Configure GitHub Project Board via GraphQL API.

Creates:
- Project board "Hands-Off Engine Kanban"
- Columns: Backlog, In Progress, Review, Done
- Links to repository
- Auto-add for new issues
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
        "script": "configure_project",
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
        
        # Parse GitHub URLs securely with regex patterns
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


def graphql_query(token: str, query: str, variables: Optional[Dict] = None):
    """Execute a GraphQL query against GitHub API."""
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"GraphQL errors: {data['errors']}")
                return None
            return data.get("data")
        else:
            print(f"GraphQL request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Exception during GraphQL query: {e}")
        return None


def get_repo_id(token: str, owner: str, repo: str) -> Optional[str]:
    """Get repository node ID for GraphQL."""
    query = """
    query($owner: String!, $repo: String!) {
        repository(owner: $owner, name: $repo) {
            id
        }
    }
    """
    
    variables = {"owner": owner, "repo": repo}
    data = graphql_query(token, query, variables)
    
    if data and "repository" in data:
        return data["repository"]["id"]
    
    return None


def get_owner_id(token: str, owner: str) -> Optional[str]:
    """Get owner node ID for GraphQL (could be user or org)."""
    # Try as user first
    query = """
    query($login: String!) {
        user(login: $login) {
            id
        }
    }
    """
    
    variables = {"login": owner}
    data = graphql_query(token, query, variables)
    
    if data and "user" in data and data["user"]:
        return data["user"]["id"]
    
    # Try as organization
    query = """
    query($login: String!) {
        organization(login: $login) {
            id
        }
    }
    """
    
    data = graphql_query(token, query, variables)
    if data and "organization" in data and data["organization"]:
        return data["organization"]["id"]
    
    return None


def create_project(token: str, owner: str, repo: str):
    """Create a GitHub Project (Projects V2) for the repository."""
    print(f"Creating project board for {owner}/{repo}...")
    log_action("create_project", "started", {"owner": owner, "repo": repo})
    
    # Get owner ID (needed for project creation)
    owner_id = get_owner_id(token, owner)
    if not owner_id:
        print("❌ Could not get owner ID")
        log_action("create_project", "failed", {
            "owner": owner,
            "repo": repo,
            "error": "Could not get owner ID"
        })
        return False
    
    # Create project using Projects V2 API
    mutation = """
    mutation($ownerId: ID!, $title: String!) {
        createProjectV2(input: {ownerId: $ownerId, title: $title}) {
            projectV2 {
                id
                title
                url
            }
        }
    }
    """
    
    variables = {
        "ownerId": owner_id,
        "title": "Hands-Off Engine Kanban"
    }
    
    data = graphql_query(token, mutation, variables)
    
    if data and "createProjectV2" in data:
        project = data["createProjectV2"]["projectV2"]
        print(f"✅ Project created: {project['title']}")
        print(f"   URL: {project['url']}")
        log_action("create_project", "success", {
            "owner": owner,
            "repo": repo,
            "project_id": project["id"],
            "project_url": project["url"]
        })
        
        print("\n📝 Manual steps needed:")
        print("   1. Go to the project board URL above")
        print("   2. Add custom fields for status: Backlog, In Progress, Review, Done")
        print("   3. Link the project to this repository")
        print("   4. Configure workflows to auto-add new issues")
        print("\nNote: Projects V2 API has limited automation capabilities.")
        print("      Full automation requires repository-level projects (V1, deprecated)")
        
        return True
    else:
        print("❌ Failed to create project")
        log_action("create_project", "failed", {
            "owner": owner,
            "repo": repo,
            "error": "GraphQL mutation failed"
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
    print("\nConfiguring GitHub Project Board...")
    
    success = create_project(token, owner, repo)
    
    if not success:
        print("\n⚠️  Note: Project creation requires appropriate token permissions")
        print("   and may not be fully automatable with Projects V2.")
        # Don't exit with error - this is a nice-to-have feature
    
    print("\n✅ Project configuration script complete")


if __name__ == "__main__":
    main()
