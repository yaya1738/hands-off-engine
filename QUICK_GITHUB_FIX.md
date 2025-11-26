# EMERGENCY FIX: GitHub Rate Limit (60/hour → 5000/hour)

## Problem
You're hitting the unauthenticated rate limit because GITHUB_TOKEN is not set.

**Current:** 60 requests/hour (unauthenticated)
**Need:** 5,000 requests/hour (authenticated)

---

## IMMEDIATE FIX (Choose One)

### Option 1: Automated Setup (Recommended)
```bash
# Run the setup script
bash scripts/setup_github_token.sh
```

This will:
- Prompt for your GitHub token
- Save it securely to `~/.config/github/env`
- Update your shell RC file
- Test the configuration

### Option 2: Manual Setup (Fast)

**Step 1:** Get your GitHub token from https://github.com/settings/tokens
(Or create new: click "Generate new token (classic)" → select scopes → copy token)

**Step 2:** Set it immediately:
```bash
# FOR THIS SESSION ONLY (immediate fix)
export GITHUB_TOKEN="ghp_your_actual_token_here"

# Verify it works
python -m scripts.github_ratelimit_status
```

You should now see:
```
core     | limit= 5000 remaining= 5000 ...
```

**Step 3:** Make it permanent:
```bash
# Create config directory
mkdir -p ~/.config/github

# Save token
echo 'export GITHUB_TOKEN="ghp_your_actual_token_here"' > ~/.config/github/env
chmod 600 ~/.config/github/env

# Add to shell RC
echo 'source ~/.config/github/env' >> ~/.bashrc

# Reload shell
source ~/.bashrc
```

---

## For Termux (Phone)
```bash
# Set token
mkdir -p "$HOME/.config/github"
echo 'export GITHUB_TOKEN="ghp_your_token"' > "$HOME/.config/github/env"
chmod 600 "$HOME/.config/github/env"

# Add to bashrc
echo 'source "$HOME/.config/github/env"' >> "$HOME/.bashrc"

# Reload
source "$HOME/.bashrc"

# Verify
python -m scripts.github_ratelimit_status
```

---

## For Droplet (Root SSH)
```bash
# Set token
mkdir -p /root/.config/github
echo 'export GITHUB_TOKEN="ghp_your_token"' > /root/.config/github/env
chmod 600 /root/.config/github/env

# Add to bashrc
echo 'source /root/.config/github/env' >> /root/.bashrc

# Reload
source /root/.bashrc

# Verify
python -m scripts.github_ratelimit_status
```

---

## Verify It's Working

After setting the token, check:
```bash
# Should show your token (first 20 chars)
echo $GITHUB_TOKEN | head -c 20

# Should show 5000 limit, not 60
python -m scripts.github_ratelimit_status
```

**Expected output:**
```
core     | limit= 5000 remaining= 5000 reset=...
```

If you still see `limit= 60`, the token is not set correctly.

---

## Creating a Token

If you don't have a token yet:

1. Go to: https://github.com/settings/tokens
2. Click: **"Generate new token"** → **"Generate new token (classic)"**
3. Name it: `hands-off-engine-[environment]`
4. Set expiration: Choose based on your needs
5. Select scopes:
   - ✓ `repo` (for private repos)
   - ✓ `public_repo` (for public repos)
   - ✓ `read:org` (if checking org repos)
6. Click: **"Generate token"**
7. **COPY THE TOKEN IMMEDIATELY** (you won't see it again)

---

## Troubleshooting

### Still seeing 60 limit after setting token?

**Check 1:** Token is actually set
```bash
echo $GITHUB_TOKEN
# Should show: ghp_xxxxx... (not empty)
```

**Check 2:** Token is valid
```bash
curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/user
# Should NOT return "Bad credentials"
```

**Check 3:** Python can see it
```bash
python -c "import os; print('Token set:', bool(os.getenv('GITHUB_TOKEN')))"
# Should show: Token set: True
```

### Token expired or invalid?

Create a new token at https://github.com/settings/tokens and update:
```bash
# Edit the config file
nano ~/.config/github/env

# Update the token
export GITHUB_TOKEN="ghp_new_token_here"

# Reload
source ~/.config/github/env
```

---

## Current Status Check
```bash
python -m scripts.github_ratelimit_status
```

---

## Security Notes

⚠️ **NEVER commit tokens to git**
- Tokens stay in `~/.config/github/env` (local only)
- This file is NOT in the repository
- Use separate tokens for different environments

🔒 **Protect your token file**
```bash
chmod 600 ~/.config/github/env
```

---

## Once Fixed

After authentication is working:
1. All GitHub operations will use the 5000/hour limit
2. Copilot and other integrations will work smoothly
3. No more rate limit blockers
4. Monitor usage: `python -m scripts.github_ratelimit_status`
