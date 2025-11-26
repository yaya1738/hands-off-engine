# GitHub Integration Guide

Complete guide for using GitHub operations in the Hands-Off Engine.

## Overview

The GitHub integration provides a comprehensive suite of tools for interacting with GitHub repositories, pull requests, issues, and code search. Built on a rate-limit-aware client, it automatically handles API limits and transient errors.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│  (AI Runner, Scripts, MBOL Task Processors)                  │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│              scripts/github_task_processor.py                │
│  (MBOL-style task definitions and processing)                │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│              scripts/github_operations.py                    │
│  (High-level operations: get_repo_info, list_prs, etc.)     │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│              scripts/github_client.py                        │
│  (Rate-limit-aware HTTP client with retry logic)            │
└────────────────────────────┬────────────────────────────────┘
                             │
                    GitHub REST API v3
```

## Components

### 1. GitHub Client (`scripts/github_client.py`)

Low-level HTTP client with rate limit awareness.

**Features:**
- Automatic rate limit detection and waiting
- Exponential backoff for 5xx errors
- Token-based authentication
- Returns both data and rate limit metadata

**Usage:**
```python
from scripts.github_client import github_get, GitHubRateLimitError

try:
    data, meta = github_get("/repos/owner/repo")
    print(f"Remaining requests: {meta['remaining']}")
except GitHubRateLimitError as e:
    print(f"Rate limited: {e}")
```

See: `docs/GITHUB_RATE_LIMIT_AND_AUTH.md` for authentication setup.

### 2. GitHub Operations (`scripts/github_operations.py`)

High-level functions for common GitHub tasks.

**Available Operations:**
- `get_repo_info(owner, repo)` - Repository information and statistics
- `list_pull_requests(owner, repo, state, per_page, page)` - List PRs
- `get_pull_request(owner, repo, pr_number)` - Detailed PR information
- `list_issues(owner, repo, state, labels, per_page, page)` - List issues
- `get_latest_release(owner, repo)` - Latest release information
- `get_repo_stats(owner, repo)` - Comprehensive repository statistics
- `search_code(query, per_page, page)` - Search code across repositories

**Usage:**
```python
from scripts.github_operations import get_repo_info, list_pull_requests

# Get repository info
repo = get_repo_info("anthropics", "anthropic-sdk-python")
print(f"Stars: {repo['stars']}, Language: {repo['language']}")

# List open PRs
prs, meta = list_pull_requests("anthropics", "anthropic-sdk-python", state="open")
for pr in prs:
    print(f"PR #{pr['number']}: {pr['title']}")
```

### 3. Task Processor (`scripts/github_task_processor.py`)

MBOL-style task processor for AI Runner integration.

**Supported Task Types:**
- `github_repo_info`
- `github_list_prs`
- `github_get_pr`
- `github_list_issues`
- `github_latest_release`
- `github_repo_stats`
- `github_search_code`

**Usage:**
```python
from scripts.github_task_processor import process_github_task

task = {
    "task_id": "check_repo",
    "task_type": "github_repo_info",
    "params": {
        "owner": "anthropics",
        "repo": "anthropic-sdk-python"
    }
}

result = process_github_task(task)
if result["status"] == "success":
    print(result["data"])
else:
    print(f"Error: {result['error']}")
```

## Quick Start

### 1. Set Up Authentication

Create a GitHub Personal Access Token and configure it:

```bash
# Termux
mkdir -p "$HOME/.config/github"
echo 'export GITHUB_TOKEN="ghp_your_token_here"' > "$HOME/.config/github/env"
echo 'source "$HOME/.config/github/env"' >> "$HOME/.bashrc"
source "$HOME/.bashrc"

# Droplet
mkdir -p /root/.config/github
echo 'export GITHUB_TOKEN="ghp_your_token_here"' > /root/.config/github/env
echo 'source /root/.config/github/env' >> /root/.bashrc
source /root/.bashrc
```

See: `docs/GITHUB_RATE_LIMIT_AND_AUTH.md` for detailed setup.

### 2. Check Rate Limit Status

```bash
python -m scripts.github_ratelimit_status
```

### 3. Run Example Tasks

```bash
# Get repository information
python -m scripts.github_task_processor examples/github_tasks/example_repo_info.json

# List open pull requests
python -m scripts.github_task_processor examples/github_tasks/example_list_prs.json

# Get comprehensive stats
python -m scripts.github_task_processor examples/github_tasks/example_repo_stats.json
```

## Common Use Cases

### Monitor Repository Activity

```python
from scripts.github_operations import get_repo_stats

stats = get_repo_stats("yaya1738", "hands-off-engine")

print(f"Repository: {stats['repository']['name']}")
print(f"Stars: {stats['repository']['stars']}")
print(f"Last pushed: {stats['activity']['last_pushed']}")
print(f"Open issues: {stats['health']['open_issues']}")

if stats['latest_release']:
    print(f"Latest version: {stats['latest_release']['tag_name']}")
```

### Check for Open Pull Requests

```python
from scripts.github_operations import list_pull_requests

prs, meta = list_pull_requests("yaya1738", "hands-off-engine", state="open")

print(f"Found {len(prs)} open PRs (Rate limit: {meta['remaining']}/{meta['limit']})")

for pr in prs:
    labels = ", ".join(pr['labels']) if pr['labels'] else "none"
    print(f"  #{pr['number']}: {pr['title']}")
    print(f"    State: {pr['mergeable_state']}, Labels: {labels}")
    print(f"    Updated: {pr['updated_at']}")
```

### Search for TODOs in Code

```python
from scripts.github_operations import search_code

query = "repo:yaya1738/hands-off-engine TODO"
results, meta = search_code(query, per_page=20)

print(f"Found {len(results)} TODOs")
for item in results:
    print(f"  {item['path']}: {item['html_url']}")
```

### Monitor Multiple Repositories

```python
from scripts.github_operations import get_repo_info

repos = [
    ("yaya1738", "hands-off-engine"),
    ("anthropics", "anthropic-sdk-python"),
    ("openai", "openai-python"),
]

for owner, repo in repos:
    info = get_repo_info(owner, repo)
    print(f"{info['full_name']}: {info['stars']} ⭐ | {info['open_issues']} issues")
```

## Integration with AI Runner

To integrate GitHub tasks with the AI Runner system:

### Option 1: Add to Task Dispatcher

Edit `ai_runner.py` to handle GitHub task types:

```python
from scripts.github_task_processor import process_github_task

def process_task(task_file):
    with open(task_file) as f:
        task_data = json.load(f)

    task_type = task_data.get("task_type")

    # Handle GitHub tasks
    if task_type.startswith("github_"):
        result = process_github_task(task_data)
        return result

    # Handle other task types...
    elif task_type == "sparkplug_autokernel_refresh":
        # existing logic
        pass
```

### Option 2: Dedicated GitHub Task Watcher

Create a dedicated watcher for GitHub tasks:

```python
# scripts/github_task_watcher.py
import os
import json
import time
from pathlib import Path
from scripts.github_task_processor import process_github_task, format_result_summary

GITHUB_TASKS_DIR = Path("/path/to/github/tasks")
RESULTS_DIR = Path("/path/to/results")

def watch_github_tasks():
    """Watch for new GitHub task files and process them."""
    while True:
        for task_file in GITHUB_TASKS_DIR.glob("*.json"):
            try:
                result = process_github_task_file(str(task_file))

                # Write result
                result_file = RESULTS_DIR / f"{task_file.stem}_result.json"
                with open(result_file, "w") as f:
                    json.dump(result, f, indent=2)

                # Log summary
                print(format_result_summary(result))

                # Move processed task
                task_file.rename(GITHUB_TASKS_DIR / "processed" / task_file.name)

            except Exception as e:
                print(f"Error processing {task_file}: {e}")

        time.sleep(10)

if __name__ == "__main__":
    watch_github_tasks()
```

## Rate Limiting Best Practices

### 1. Monitor Your Rate Limit

```python
from scripts.github_client import github_get

data, meta = github_get("/rate_limit")
core = data["resources"]["core"]

remaining = int(core["remaining"])
limit = int(core["limit"])
usage_percent = ((limit - remaining) / limit) * 100

print(f"Rate limit usage: {usage_percent:.1f}% ({remaining}/{limit} remaining)")

if remaining < 100:
    print("⚠️  Warning: Low rate limit remaining!")
```

### 2. Batch Operations

When fetching data for multiple repositories, add delays:

```python
import time
from scripts.github_operations import get_repo_info

repos = [...]  # List of (owner, repo) tuples

for i, (owner, repo) in enumerate(repos):
    info = get_repo_info(owner, repo)
    # Process info...

    # Add delay every 10 repos
    if (i + 1) % 10 == 0:
        time.sleep(1)
```

### 3. Cache Results

For data that doesn't change frequently, cache results:

```python
import json
import time
from pathlib import Path

CACHE_DIR = Path("/tmp/github_cache")
CACHE_DURATION = 3600  # 1 hour

def cached_get_repo_info(owner, repo):
    cache_file = CACHE_DIR / f"{owner}_{repo}.json"

    # Check cache
    if cache_file.exists():
        cache_age = time.time() - cache_file.stat().st_mtime
        if cache_age < CACHE_DURATION:
            with open(cache_file) as f:
                return json.load(f)

    # Fetch fresh data
    info = get_repo_info(owner, repo)

    # Update cache
    CACHE_DIR.mkdir(exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump(info, f)

    return info
```

## Error Handling

All operations may raise `GitHubRateLimitError` or standard HTTP errors:

```python
from scripts.github_client import GitHubRateLimitError
from scripts.github_operations import get_repo_info
import requests

try:
    repo = get_repo_info("owner", "repo")

except GitHubRateLimitError as e:
    # Rate limit exceeded - wait or skip
    print(f"Rate limited: {e}")
    # Option 1: Wait and retry
    time.sleep(60)
    repo = get_repo_info("owner", "repo")

except requests.HTTPError as e:
    # HTTP error (404, 403, etc.)
    if e.response.status_code == 404:
        print("Repository not found")
    elif e.response.status_code == 403:
        print("Access forbidden - check token permissions")
    else:
        print(f"HTTP error: {e}")

except Exception as e:
    # Unexpected error
    print(f"Unexpected error: {e}")
```

## Testing

Run the test suite:

```bash
# Test GitHub client
pytest tests/unit/test_github_client.py -v

# Test GitHub operations
pytest tests/unit/test_github_operations.py -v

# Run all tests
pytest tests/unit/ -v
```

All tests use mocked HTTP responses - no network calls are made.

## Security Considerations

1. **Never commit tokens** - Always use environment variables
2. **Use fine-grained tokens** when possible with minimal required scopes
3. **Rotate tokens regularly** - Set expiration dates on tokens
4. **Separate tokens per environment** - Different tokens for Termux, Droplet, CI/CD
5. **Monitor token usage** - Check GitHub's token usage dashboard regularly

## Troubleshooting

### Import Errors

```bash
# Ensure you're running from repo root
cd /path/to/hands-off-engine
python -m scripts.github_ratelimit_status
```

### Rate Limit Issues

```bash
# Check current rate limit
python -m scripts.github_ratelimit_status

# If limited, wait or use a different token
# Rate limits reset every hour
```

### Authentication Issues

```bash
# Verify token is set
echo $GITHUB_TOKEN

# Test token validity
curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/user
```

### Module Not Found

```bash
# Install dependencies
pip install requests>=2.31.0

# Or install from requirements
pip install -r ai/requirements.txt
```

## Next Steps

1. **Create MBOL GitHub agents** - Build agents that use GitHub operations for monitoring and automation
2. **Integrate with CI/CD** - Use GitHub operations in deployment pipelines
3. **Build dashboards** - Create real-time dashboards showing repository health
4. **Automate PR reviews** - Build systems to automatically check PR status and notify teams
5. **Monitor releases** - Track new releases across multiple repositories

## References

- [GitHub REST API Documentation](https://docs.github.com/en/rest)
- [GitHub API Rate Limiting](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting)
- [Creating Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- Project docs:
  - `docs/GITHUB_RATE_LIMIT_AND_AUTH.md` - Authentication setup
  - `examples/github_tasks/README.md` - Task examples and usage
