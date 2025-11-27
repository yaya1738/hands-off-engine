# Quick GitHub Rate Limit Fix

## The Problem

GitHub API has two rate limits:
- **Anonymous**: 60 requests/hour (hits limit fast!)
- **Authenticated**: 5000 requests/hour (sufficient for most uses)

When you see rate limit errors or 403s, you're likely using the anonymous limit.

## Quick Fix (2 minutes)

### Step 1: Create a GitHub Token

1. Go to: https://github.com/settings/tokens/new
2. Set a name: `hands-off-engine`
3. Set expiration: 90 days (or your preference)
4. Select scope: `repo` (Full control of private repositories)
5. Click "Generate token"
6. Copy the token (starts with `ghp_`)

### Step 2: Configure the Token

**Option A: Automated Setup (Recommended)**
```bash
./scripts/setup_github_token.sh ghp_YOUR_TOKEN_HERE
```

**Option B: Manual Setup**
```bash
# Add to your shell config
echo 'export GITHUB_TOKEN="ghp_YOUR_TOKEN_HERE"' >> ~/.bashrc
source ~/.bashrc
```

### Step 3: Verify

```bash
python3 scripts/github_ratelimit_status.py
```

Expected output:
```
✓ GitHub API authenticated
Rate Limit: 5000/5000
Used: 0
Resets in: 60 minutes
```

## Using the GitHub Client

### In Python Scripts

```python
from scripts.github_client import GitHubClient, GitHubAuthError

try:
    client = GitHubClient()  # Uses GITHUB_TOKEN from environment
    
    # Check rate limit
    rate_info = client.get_rate_limit()
    print(f"Remaining: {rate_info.remaining}/{rate_info.limit}")
    
    # Check if authenticated
    if client.is_authenticated():
        print("Authentication working!")
        
except GitHubAuthError as e:
    print(f"Auth failed: {e}")
```

### Command Line

```bash
# Check rate limit
python3 scripts/github_client.py --rate-limit

# Check authentication
python3 scripts/github_client.py --check-auth

# Show authenticated user
python3 scripts/github_client.py --user
```

## Healthcheck Integration

The healthcheck script (`scripts/healthcheck.sh`) includes a GitHub auth check.
It will alert you if GitHub authentication is not configured.

## Troubleshooting

### "No GitHub token provided"

Set the environment variable:
```bash
export GITHUB_TOKEN="ghp_YOUR_TOKEN"
```

### "Authentication failed"

- Token may be expired → Create a new one
- Token may lack proper scopes → Regenerate with `repo` scope
- Token may be revoked → Check GitHub settings

### Rate Limit Still Low (60/hour)

- Token not exported in current shell
- Token environment variable name misspelled (must be `GITHUB_TOKEN`)
- Token is invalid

### Testing Your Token

```bash
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit
```

Look for `"limit": 5000` in the response.

## Files Reference

| File | Purpose |
|------|---------|
| `scripts/setup_github_token.sh` | Automated token setup |
| `scripts/github_ratelimit_status.py` | Check rate limit status |
| `scripts/github_client.py` | Reusable GitHub API client |
| `scripts/healthcheck.sh` | System health checks (includes GitHub auth) |

## Security Notes

- Never commit your token to git
- The token is stored in `~/.bashrc` which is not committed
- Rotate tokens periodically (every 90 days recommended)
- Use minimal required scopes (`repo` is sufficient)
