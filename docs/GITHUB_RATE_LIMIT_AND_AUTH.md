# GitHub Rate Limit and Authentication

This document explains how to configure GitHub API authentication for the Hands-Off Engine and how to use the rate-limit-aware GitHub client.

## Overview

The Hands-Off Engine includes a rate-limit-aware GitHub API client (`scripts/github_client.py`) that automatically handles:

- GitHub API authentication using Personal Access Tokens (PATs)
- Rate limit detection and smart retry logic
- Exponential backoff for transient 5xx errors
- Automatic parsing of rate limit headers

**Always use authenticated requests** to avoid the low unauthenticated rate limit (60 requests/hour vs 5000 requests/hour for authenticated users).

## Environment Variables

The GitHub client looks for authentication tokens in the following order:

1. `GITHUB_TOKEN` (preferred)
2. `GH_TOKEN` (fallback)

If neither is set, requests will be unauthenticated and subject to the low 60 requests/hour limit.

## Setting Up Authentication

### Termux (Phone)

1. Create a configuration directory and environment file:

```bash
mkdir -p "$HOME/.config/github"
nano "$HOME/.config/github/env"
```

2. Add your GitHub Personal Access Token:

```bash
export GITHUB_TOKEN="ghp_your_actual_token_here"
```

3. Source this file automatically by adding to your shell RC file:

```bash
echo 'source "$HOME/.config/github/env"' >> "$HOME/.bashrc"
source "$HOME/.bashrc"
```

### Droplet (Root SSH)

1. Create a configuration directory and environment file:

```bash
mkdir -p /root/.config/github
nano /root/.config/github/env
```

2. Add your GitHub Personal Access Token:

```bash
export GITHUB_TOKEN="ghp_your_actual_token_here"
```

3. Source this file automatically by adding to your shell RC file:

```bash
echo 'source /root/.config/github/env' >> /root/.bashrc
source /root/.bashrc
```

### Creating a GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" > "Generate new token (classic)"
3. Give it a descriptive name (e.g., "hands-off-engine-termux")
4. Set expiration as needed (or "No expiration" for long-lived tokens)
5. Select scopes based on your needs:
   - `repo` - for private repository access
   - `public_repo` - for public repository access only
   - `read:org` - for organization data
6. Click "Generate token" and copy the token immediately (you won't see it again)

## Checking Rate Limit Status

Use the included CLI utility to check your current rate limit status:

```bash
# From the repo root
python -m scripts.github_ratelimit_status
```

Example output:

```
GitHub rate limit status (UTC)
Now: 1732627200 (2024-11-26T12:00:00Z)

core     | limit= 5000 remaining= 4987 reset=1732630800 (2024-11-26T13:00:00Z)
search   | limit=   30 remaining=   30 reset=1732627260 (2024-11-26T12:01:00Z)
```

## Using the GitHub Client in Code

```python
from scripts.github_client import github_get, GitHubRateLimitError

try:
    # Fetch rate limit information
    data, meta = github_get("/rate_limit")
    print(f"Remaining: {meta['remaining']}/{meta['limit']}")

    # Fetch repository information
    repo_data, repo_meta = github_get("/repos/owner/repo")
    print(f"Stars: {repo_data['stargazers_count']}")

except GitHubRateLimitError as e:
    print(f"Rate limit exceeded: {e}")
```

The `github_get` function returns a tuple of:
- `data`: The parsed JSON response
- `meta`: A dictionary with rate limit headers (`limit`, `remaining`, `reset`)

## Security Warnings

**CRITICAL: Never commit tokens or environment files to Git.**

- Always keep tokens in local environment files only
- Never include tokens in code, scripts, or documentation
- Add environment files to `.gitignore` if they're not already excluded
- Use separate tokens for different environments (Termux, Droplet, CI/CD, etc.)
- Rotate tokens regularly and revoke them if compromised

The `.config/github/env` pattern ensures tokens stay out of the repository while being easy to source in shell sessions.

## Rate Limit Details

GitHub API rate limits (as of 2024):

| Type | Authenticated | Unauthenticated |
|------|---------------|-----------------|
| Core API | 5,000/hour | 60/hour |
| Search API | 30/minute | 10/minute |
| GraphQL API | 5,000 points/hour | Not available |

The `github_client` automatically:
- Waits until rate limit reset time when limit is exceeded
- Retries with exponential backoff on 5xx errors
- Raises `GitHubRateLimitError` if retries are exhausted

## Troubleshooting

### "Rate limit exceeded" errors

1. Check if your token is properly set:
   ```bash
   echo $GITHUB_TOKEN
   ```

2. Verify the token is valid and not expired on https://github.com/settings/tokens

3. Check current rate limit status:
   ```bash
   python -m scripts.github_ratelimit_status
   ```

### Import errors when running the CLI

Ensure you're running from the repo root and using the module syntax:

```bash
# Correct
python -m scripts.github_ratelimit_status

# Incorrect
python scripts/github_ratelimit_status.py
```

### Missing requests library

If you get `ModuleNotFoundError: No module named 'requests'`, install it:

```bash
pip install requests>=2.31.0
```

Or install from the project requirements:

```bash
pip install -r ai/requirements.txt
```

## Next Steps

Once the GitHub client is in place, consider:

1. Creating MBOL task types that use `github_get` for GitHub operations
2. Adding more specialized GitHub helpers (PR management, issue tracking, etc.)
3. Integrating with CI/CD workflows for automated rate limit monitoring
