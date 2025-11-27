# Quick GitHub Rate Limit Fix

## The Problem

GitHub's API has rate limits:
- **Unauthenticated**: 60 requests/hour (easily exhausted)
- **Authenticated**: 5,000 requests/hour (plenty for automation)

When rate limited, you'll see errors like:
```
API rate limit exceeded for [IP]
```

## Quick Fix (30 seconds)

### 1. Create a GitHub Token

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Name: `hands-off-engine`
4. Select scopes: `repo` (for private repos)
5. Click **Generate token**
6. Copy the token (starts with `ghp_`)

### 2. Set Up Token

**Option A: Interactive setup**
```bash
cd /path/to/hands-off-engine
./scripts/setup_github_token.sh
```

**Option B: Direct export**
```bash
export GITHUB_TOKEN=ghp_your_token_here
echo 'export GITHUB_TOKEN=ghp_your_token_here' >> ~/.bashrc
```

### 3. Verify

```bash
python3 scripts/github_ratelimit_status.py
```

Expected output:
```
🟢 OK - Sufficient requests available
✅ Authenticated - 5000 requests/hour available
```

## Termux Setup

On Termux (Android), use the same steps:

```bash
# In Termux
pkg install python
cd ~/hands-off-engine
export GITHUB_TOKEN=ghp_your_token_here
echo 'export GITHUB_TOKEN=ghp_your_token_here' >> ~/.bashrc
python3 scripts/github_ratelimit_status.py
```

## Security Notes

- Never commit tokens to git (they're in `.gitignore`)
- Tokens are stored in `~/.github_token` with `chmod 600`
- You can revoke tokens anytime at github.com/settings/tokens

## Troubleshooting

### "Token validation failed"
- Make sure the token hasn't expired
- Check that you copied the full token

### Still rate limited after setup
- Run `source ~/.bashrc` to reload config
- Check token is exported: `echo $GITHUB_TOKEN`

### Permission denied
- Token might not have required scopes
- Create new token with `repo` scope

## Related Files

- `scripts/github_client.py` - Python client library
- `scripts/github_ratelimit_status.py` - Status checker
- `scripts/setup_github_token.sh` - Token setup script
