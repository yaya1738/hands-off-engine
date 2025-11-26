"""
GitHub task processor for AI Runner integration.

Processes GitHub-related tasks using the github_operations module.
Supports MBOL-style task definitions for common GitHub operations.

Task Types Supported:
- github_repo_info: Get repository information
- github_list_prs: List pull requests
- github_get_pr: Get specific PR details
- github_list_issues: List issues
- github_latest_release: Get latest release info
- github_repo_stats: Get comprehensive repository statistics
- github_search_code: Search code across repositories

Task JSON Schema:
{
    "task_id": "unique-task-id",
    "task_type": "github_repo_info",
    "params": {
        "owner": "repository-owner",
        "repo": "repository-name",
        ...additional params based on task type
    }
}
"""

import json
from typing import Any, Dict
from scripts import github_operations as gh_ops
from scripts.github_client import GitHubRateLimitError


def process_github_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a GitHub task and return results.

    Args:
        task_data: Task definition dictionary with task_type and params

    Returns:
        Result dictionary with:
        - status: "success" or "error"
        - data: Task results (if successful)
        - error: Error message (if failed)
        - task_id: Original task ID
        - task_type: Original task type

    Raises:
        ValueError: If task_type is not supported or params are invalid
    """
    task_id = task_data.get("task_id", "unknown")
    task_type = task_data.get("task_type")
    params = task_data.get("params", {})

    result = {
        "task_id": task_id,
        "task_type": task_type,
        "status": "error",
    }

    try:
        if task_type == "github_repo_info":
            owner = params.get("owner")
            repo = params.get("repo")
            if not owner or not repo:
                raise ValueError("Missing required params: owner, repo")

            data = gh_ops.get_repo_info(owner, repo)
            result["status"] = "success"
            result["data"] = data

        elif task_type == "github_list_prs":
            owner = params.get("owner")
            repo = params.get("repo")
            if not owner or not repo:
                raise ValueError("Missing required params: owner, repo")

            state = params.get("state", "open")
            per_page = params.get("per_page", 30)
            page = params.get("page", 1)

            prs, meta = gh_ops.list_pull_requests(owner, repo, state, per_page, page)
            result["status"] = "success"
            result["data"] = {
                "pull_requests": prs,
                "count": len(prs),
                "rate_limit": meta,
            }

        elif task_type == "github_get_pr":
            owner = params.get("owner")
            repo = params.get("repo")
            pr_number = params.get("pr_number")
            if not owner or not repo or pr_number is None:
                raise ValueError("Missing required params: owner, repo, pr_number")

            data = gh_ops.get_pull_request(owner, repo, int(pr_number))
            result["status"] = "success"
            result["data"] = data

        elif task_type == "github_list_issues":
            owner = params.get("owner")
            repo = params.get("repo")
            if not owner or not repo:
                raise ValueError("Missing required params: owner, repo")

            state = params.get("state", "open")
            labels = params.get("labels")
            per_page = params.get("per_page", 30)
            page = params.get("page", 1)

            issues, meta = gh_ops.list_issues(owner, repo, state, labels, per_page, page)
            result["status"] = "success"
            result["data"] = {
                "issues": issues,
                "count": len(issues),
                "rate_limit": meta,
            }

        elif task_type == "github_latest_release":
            owner = params.get("owner")
            repo = params.get("repo")
            if not owner or not repo:
                raise ValueError("Missing required params: owner, repo")

            data = gh_ops.get_latest_release(owner, repo)
            result["status"] = "success"
            result["data"] = data if data else {"message": "No releases found"}

        elif task_type == "github_repo_stats":
            owner = params.get("owner")
            repo = params.get("repo")
            if not owner or not repo:
                raise ValueError("Missing required params: owner, repo")

            data = gh_ops.get_repo_stats(owner, repo)
            result["status"] = "success"
            result["data"] = data

        elif task_type == "github_search_code":
            query = params.get("query")
            if not query:
                raise ValueError("Missing required param: query")

            per_page = params.get("per_page", 30)
            page = params.get("page", 1)

            results, meta = gh_ops.search_code(query, per_page, page)
            result["status"] = "success"
            result["data"] = {
                "results": results,
                "count": len(results),
                "rate_limit": meta,
            }

        else:
            raise ValueError(f"Unsupported task type: {task_type}")

    except GitHubRateLimitError as e:
        result["status"] = "error"
        result["error"] = f"GitHub rate limit exceeded: {str(e)}"
        result["error_type"] = "rate_limit"

    except ValueError as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["error_type"] = "validation"

    except Exception as e:
        result["status"] = "error"
        result["error"] = f"Unexpected error: {str(e)}"
        result["error_type"] = "unknown"

    return result


def process_github_task_file(task_file_path: str) -> Dict[str, Any]:
    """
    Load a GitHub task from a JSON file and process it.

    Args:
        task_file_path: Path to task JSON file

    Returns:
        Result dictionary from process_github_task

    Raises:
        FileNotFoundError: If task file doesn't exist
        json.JSONDecodeError: If task file is not valid JSON
    """
    with open(task_file_path, "r") as f:
        task_data = json.load(f)

    return process_github_task(task_data)


def format_result_summary(result: Dict[str, Any]) -> str:
    """
    Format task result into a human-readable summary.

    Args:
        result: Result dictionary from process_github_task

    Returns:
        Formatted string summary
    """
    lines = []
    lines.append(f"Task: {result['task_id']}")
    lines.append(f"Type: {result['task_type']}")
    lines.append(f"Status: {result['status']}")

    if result["status"] == "success":
        data = result.get("data", {})

        if result["task_type"] == "github_repo_info":
            lines.append(f"  Repository: {data.get('full_name')}")
            lines.append(f"  Stars: {data.get('stars')}")
            lines.append(f"  Language: {data.get('language')}")
            lines.append(f"  Open Issues: {data.get('open_issues')}")

        elif result["task_type"] == "github_list_prs":
            lines.append(f"  Found {data.get('count')} pull requests")
            for pr in data.get("pull_requests", [])[:5]:
                lines.append(f"    - #{pr['number']}: {pr['title']} ({pr['state']})")

        elif result["task_type"] == "github_get_pr":
            lines.append(f"  PR #{data.get('number')}: {data.get('title')}")
            lines.append(f"  State: {data.get('state')}")
            lines.append(f"  Mergeable: {data.get('mergeable')}")
            lines.append(f"  Changes: +{data.get('additions')} -{data.get('deletions')}")

        elif result["task_type"] == "github_list_issues":
            lines.append(f"  Found {data.get('count')} issues")
            for issue in data.get("issues", [])[:5]:
                issue_type = "PR" if issue["is_pull_request"] else "Issue"
                lines.append(f"    - #{issue['number']} [{issue_type}]: {issue['title']}")

        elif result["task_type"] == "github_latest_release":
            if "tag_name" in data:
                lines.append(f"  Version: {data.get('tag_name')}")
                lines.append(f"  Name: {data.get('name')}")
                lines.append(f"  Published: {data.get('published_at')}")
            else:
                lines.append("  No releases found")

        elif result["task_type"] == "github_repo_stats":
            repo = data.get("repository", {})
            health = data.get("health", {})
            release = data.get("latest_release")
            lines.append(f"  Repository: {repo.get('full_name')}")
            lines.append(f"  Stars: {repo.get('stars')} | Forks: {repo.get('forks')}")
            lines.append(f"  Open Issues: {health.get('open_issues')}")
            if release:
                lines.append(f"  Latest Release: {release.get('tag_name')}")

        elif result["task_type"] == "github_search_code":
            lines.append(f"  Found {data.get('count')} code results")
            for item in data.get("results", [])[:5]:
                lines.append(f"    - {item['repository']['full_name']}: {item['path']}")

    else:
        lines.append(f"  Error: {result.get('error')}")
        lines.append(f"  Error Type: {result.get('error_type')}")

    return "\n".join(lines)


# Example usage and task definitions
EXAMPLE_TASKS = {
    "repo_info": {
        "task_id": "check_repo_001",
        "task_type": "github_repo_info",
        "params": {
            "owner": "anthropics",
            "repo": "anthropic-sdk-python"
        }
    },
    "list_prs": {
        "task_id": "list_prs_001",
        "task_type": "github_list_prs",
        "params": {
            "owner": "anthropics",
            "repo": "anthropic-sdk-python",
            "state": "open",
            "per_page": 10
        }
    },
    "get_pr": {
        "task_id": "get_pr_001",
        "task_type": "github_get_pr",
        "params": {
            "owner": "anthropics",
            "repo": "anthropic-sdk-python",
            "pr_number": 123
        }
    },
    "list_issues": {
        "task_id": "list_issues_001",
        "task_type": "github_list_issues",
        "params": {
            "owner": "anthropics",
            "repo": "anthropic-sdk-python",
            "state": "open",
            "labels": ["bug", "enhancement"]
        }
    },
    "latest_release": {
        "task_id": "latest_release_001",
        "task_type": "github_latest_release",
        "params": {
            "owner": "anthropics",
            "repo": "anthropic-sdk-python"
        }
    },
    "repo_stats": {
        "task_id": "repo_stats_001",
        "task_type": "github_repo_stats",
        "params": {
            "owner": "anthropics",
            "repo": "anthropic-sdk-python"
        }
    },
    "search_code": {
        "task_id": "search_code_001",
        "task_type": "github_search_code",
        "params": {
            "query": "repo:anthropics/anthropic-sdk-python TODO",
            "per_page": 20
        }
    }
}


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m scripts.github_task_processor <task_file.json>")
        print("\nSupported task types:")
        for task_type in EXAMPLE_TASKS.keys():
            print(f"  - {task_type}")
        sys.exit(1)

    task_file = sys.argv[1]
    result = process_github_task_file(task_file)

    print(format_result_summary(result))
    print("\nFull result JSON:")
    print(json.dumps(result, indent=2))
