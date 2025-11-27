# Quick GitHub API Rate Limit Fix

## The Problem

GitHub API has two rate limits:
- **Unauthenticated**: 60 requests/hour (per IP)
- **Authenticated**: 5,000 requests/hour (per token)

The system was hitting the 60 request limit because GitHub API calls were not using authentication.

## Solution

Set the `GITHUB_TOKEN` environment variable to enable authenticated API access.

## Quick Setup (5 minutes)

### Option 1: Automated Setup

```bash
./scripts/setup_github_token.sh
```

This script will:
1. Guide you through creating a GitHub Personal Access Token
2. Save it securely to `~/.config/github/env`
3. Add it to your shell profile (bashrc/zshrc)
4. Test the configuration

### Option 2: Manual Setup

1. **Create a Personal Access Token**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - Name: "Hands-Off Engine"
   - Expiration: 90 days (or no expiration)
   - Scopes: Select `repo` (full control of private repos)
   - Click "Generate token"
   - Copy the token (starts with `ghp_` or `github_pat_`)

2. **Save the token**

   ```bash
   # Create config directory
   mkdir -p ~/.config/github
   chmod 700 ~/.config/github

   # Save token (replace YOUR_TOKEN with your actual token)
   echo 'export GITHUB_TOKEN="YOUR_TOKEN"' > ~/.config/github/env
   chmod 600 ~/.config/github/env

   # Add to shell profile
   echo '[ -f ~/.config/github/env ] && source ~/.config/github/env' >> ~/.bashrc
   ```

3. **Apply changes**

   ```bash
   source ~/.config/github/env
   ```

## Verify Setup

```bash
# Check rate limit status
python3 scripts/github_ratelimit_status.py
```

Expected output when authenticated:
```
==================================================
  GITHUB API RATE LIMIT STATUS
==================================================

Auth Status: ✅ Authenticated

Core API:
  Limit:     5,000 requests/hour
  Remaining: 4,998 requests
  Used:      2 requests
  Resets in: 58m 42s

✅ Rate limit is correct for authenticated access
```

## Using the GitHub Client

For code making GitHub API calls, use the authenticated client:

```python
from scripts.github_client import get_github_client

# Get authenticated client
client = get_github_client()

# Make API calls
repos = client.get("/user/repos")
rate_info = client.get_rate_limit()

print(f"Remaining requests: {rate_info.remaining}/{rate_info.limit}")
```

Features:
- Automatic authentication from `GITHUB_TOKEN` env var
- Rate limit awareness (waits when limit is low)
- Retry logic with exponential backoff
- Logging of API usage

## Healthcheck Integration

The system healthcheck (`scripts/healthcheck.sh`) now verifies GitHub authentication:

- ✅ Token is set and valid
- ⚠️ Token is missing (will warn)
- ⚠️ Token is invalid/expired (will alert)

## Troubleshooting

### Rate limit shows 60 instead of 5000

Your token may be invalid or expired. Reconfigure:
```bash
./scripts/setup_github_token.sh
```

### "Bad credentials" error

Token may have been revoked. Generate a new one at:
https://github.com/settings/tokens

### Different rate limit on Termux vs Server

Make sure the token is configured on both environments:
- Termux: Run setup script in Termux terminal
- Server: Run setup script on DigitalOcean droplet

## Related Files

- `scripts/setup_github_token.sh` - Automated token setup
- `scripts/github_ratelimit_status.py` - Check current rate limit
- `scripts/github_client.py` - Reusable authenticated client
- `scripts/healthcheck.sh` - System health check (includes GitHub auth)
- `ai/ai_intake_handler.py` - Uses GITHUB_TOKEN for posting comments
