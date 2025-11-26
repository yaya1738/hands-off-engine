# GitHub Task Examples

This directory contains example task definitions for the GitHub task processor.

## Usage

Process a task file using the GitHub task processor:

```bash
# From repo root
python -m scripts.github_task_processor examples/github_tasks/example_repo_info.json
```

## Task Types

### 1. github_repo_info

Get comprehensive information about a repository.

**Example:** `example_repo_info.json`

```json
{
  "task_id": "check_hands_off_engine",
  "task_type": "github_repo_info",
  "params": {
    "owner": "yaya1738",
    "repo": "hands-off-engine"
  }
}
```

**Returns:**
- Repository name, description, URL
- Stars, forks, watchers
- Open issues count
- Language, default branch
- Creation and update timestamps
- Rate limit metadata

### 2. github_list_prs

List pull requests for a repository.

**Example:** `example_list_prs.json`

```json
{
  "task_id": "list_open_prs",
  "task_type": "github_list_prs",
  "params": {
    "owner": "yaya1738",
    "repo": "hands-off-engine",
    "state": "open",
    "per_page": 10
  }
}
```

**Parameters:**
- `state`: "open", "closed", or "all" (default: "open")
- `per_page`: Results per page (default: 30, max: 100)
- `page`: Page number (default: 1)

**Returns:**
- List of PRs with number, title, state
- User information
- Creation/update timestamps
- Draft status, mergeable state
- Labels

### 3. github_get_pr

Get detailed information about a specific pull request.

```json
{
  "task_id": "get_pr_details",
  "task_type": "github_get_pr",
  "params": {
    "owner": "yaya1738",
    "repo": "hands-off-engine",
    "pr_number": 16
  }
}
```

**Returns:**
- All PR list information plus:
- PR body (description)
- Head and base branch details
- Commit count, additions, deletions
- Mergeable status
- Merge status and timestamp

### 4. github_list_issues

List issues for a repository (may include PRs).

```json
{
  "task_id": "list_bugs",
  "task_type": "github_list_issues",
  "params": {
    "owner": "yaya1738",
    "repo": "hands-off-engine",
    "state": "open",
    "labels": ["bug", "critical"]
  }
}
```

**Parameters:**
- `state`: "open", "closed", or "all"
- `labels`: Array of label names to filter by (optional)
- `per_page`: Results per page
- `page`: Page number

**Returns:**
- List of issues with metadata
- `is_pull_request` flag to distinguish PRs from issues

### 5. github_latest_release

Get the latest release for a repository.

```json
{
  "task_id": "check_latest_version",
  "task_type": "github_latest_release",
  "params": {
    "owner": "yaya1738",
    "repo": "hands-off-engine"
  }
}
```

**Returns:**
- Tag name, release name
- Release notes (body)
- Creation and publish timestamps
- Download URLs (tarball, zipball)
- Prerelease and draft status
- Author information

### 6. github_repo_stats

Get comprehensive repository statistics (combines multiple API calls).

**Example:** `example_repo_stats.json`

```json
{
  "task_id": "comprehensive_stats",
  "task_type": "github_repo_stats",
  "params": {
    "owner": "yaya1738",
    "repo": "hands-off-engine"
  }
}
```

**Returns:**
- Basic repository information
- Activity metrics (last push, updates, creation)
- Health metrics (open issues, archived status)
- Latest release information

### 7. github_search_code

Search for code across GitHub repositories.

```json
{
  "task_id": "find_todos",
  "task_type": "github_search_code",
  "params": {
    "query": "repo:yaya1738/hands-off-engine TODO",
    "per_page": 20
  }
}
```

**Parameters:**
- `query`: GitHub code search query (supports full search syntax)
- `per_page`: Results per page (default: 30, max: 100)
- `page`: Page number

**Query Examples:**
- `"repo:owner/repo filename:test.py"` - Search in specific files
- `"language:python TODO"` - Search across language
- `"org:myorg extension:js"` - Search in organization

**Returns:**
- List of matching files with path, name, SHA
- Repository information
- Direct URLs to code

## Integration with AI Runner

To integrate with the AI Runner system, you can add GitHub task processing to `ai_runner.py`:

```python
from scripts.github_task_processor import process_github_task

# In your task dispatcher
if task_type.startswith("github_"):
    result = process_github_task(task_data)
    # Write result to results directory
```

## Rate Limiting

All GitHub operations use the rate-limit-aware client that automatically:
- Detects rate limit exhaustion
- Waits until reset time before retrying
- Handles transient server errors with exponential backoff

Authenticated rate limits (with `GITHUB_TOKEN`):
- Core API: 5,000 requests/hour
- Search API: 30 requests/minute

See `docs/GITHUB_RATE_LIMIT_AND_AUTH.md` for authentication setup.

## Error Handling

Task results always include a `status` field:
- `"success"`: Task completed successfully, see `data` field
- `"error"`: Task failed, see `error` and `error_type` fields

Error types:
- `"rate_limit"`: GitHub rate limit exceeded
- `"validation"`: Invalid task parameters
- `"unknown"`: Unexpected error

Example error result:

```json
{
  "task_id": "failed_task",
  "task_type": "github_repo_info",
  "status": "error",
  "error": "GitHub rate limit exceeded: limit=5000, remaining=0",
  "error_type": "rate_limit"
}
```
