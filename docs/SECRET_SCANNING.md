# Secret Scanning Configuration

## Overview

GitHub's built-in secret scanning helps prevent exposure of sensitive credentials in the Hands-Off Engine repository.

## What is Scanned

GitHub automatically scans for over 200 types of secrets, including:

### Trading & Financial APIs
- Alpaca API keys
- Coinbase API tokens
- Kraken API credentials
- Generic API keys

### AI & ML Services
- OpenAI API keys
- Anthropic API keys
- Azure OpenAI credentials

### Communication Services
- Telegram bot tokens
- Slack tokens
- Discord webhooks

### Infrastructure
- AWS access keys
- DigitalOcean tokens
- GitHub personal access tokens
- SSH private keys

### Database & Services
- PostgreSQL connection strings
- MongoDB URIs
- Generic database passwords

## How It Works

1. **Push Protection** (if enabled):
   - Blocks commits containing secrets
   - Prevents accidental exposure before code is pushed

2. **Repository Scanning**:
   - Scans all commits in repository history
   - Creates alerts for detected secrets
   - Alerts appear in Security → Secret scanning

3. **Partner Patterns**:
   - Service providers (like OpenAI, Stripe) are notified
   - They can invalidate exposed credentials automatically

## Enabling Secret Scanning

### For Public Repositories
- Automatically enabled (free)
- No configuration needed

### For Private Repositories
- Requires GitHub Advanced Security
- Enable in: Settings → Code security and analysis → Secret scanning

### Push Protection
Enable to block secrets before they're pushed:
```
Settings → Code security and analysis → Push protection
```

## Custom Patterns for This Project

While GitHub's default patterns cover most cases, here are project-specific patterns to watch for:

### 1. Polymarket API Keys
Pattern: `polymarket_key_[a-zA-Z0-9]{32,}`
Location: `.env.polymarket`, `state/vault.json`

### 2. Custom Trading Credentials
Pattern: `ALPACA_API_KEY=[A-Z0-9]{20,}`
Location: `.env*` files, `vault.json`

### 3. Internal Tokens
Pattern: `HO_INTERNAL_TOKEN=[a-zA-Z0-9]{40,}`
Location: Configuration files

## Handling Detected Secrets

### If a Secret is Detected

1. **Acknowledge the alert:**
   - Go to Security → Secret scanning
   - Review the detected secret
   - Verify if it's a real secret or false positive

2. **If it's a real secret:**
   ```bash
   # 1. Immediately revoke the credential
   # (Go to the service provider and regenerate)
   
   # 2. Remove it from git history (if committed)
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch path/to/secret" \
     --prune-empty --tag-name-filter cat -- --all
   
   # 3. Force push (CAUTION: coordinate with team)
   git push --force --all
   
   # 4. Add new secret to .gitignore
   echo "path/to/secret" >> .gitignore
   
   # 5. Use GitHub Secrets or environment variables instead
   ```

3. **If it's a false positive:**
   - Close the alert as "False positive"
   - Document why it's not a real secret
   - Consider adding to `.gitignore` to prevent future alerts

### Prevention Best Practices

1. **Never commit secrets directly:**
   ```python
   # ❌ BAD
   API_KEY = "sk-abc123xyz789"
   
   # ✅ GOOD
   import os
   API_KEY = os.environ.get("API_KEY")
   ```

2. **Use environment variables:**
   ```bash
   # .env file (in .gitignore)
   OPENAI_API_KEY=sk-...
   TELEGRAM_BOT_TOKEN=123456:ABC...
   ```

3. **Use GitHub Secrets for CI/CD:**
   ```yaml
   # In workflow files
   env:
     API_KEY: ${{ secrets.API_KEY }}
   ```

4. **Use template files:**
   ```bash
   # Commit .env.template (no secrets)
   # Create .env locally (gitignored)
   cp .env.template .env
   # Then edit .env with real values
   ```

## Project-Specific Secret Storage

### Current Architecture

```
Repository (public)
├── .env.template           # ✅ Committed (no secrets)
├── .env.polymarket.template # ✅ Committed (no secrets)
└── .gitignore              # Excludes .env, vault.json

Local Development
├── .env                    # ❌ Not committed
├── .env.polymarket         # ❌ Not committed
└── state/vault.json        # ❌ Not committed

GitHub Secrets (for CI/CD)
├── OPENAI_API_KEY
├── TELEGRAM_BOT_TOKEN
└── POLYMARKET_API_KEY

GitHub Environments
├── staging/secrets         # Test credentials
└── production/secrets      # Real credentials
```

### Migration from Hard-coded to Environment Variables

If you find hard-coded secrets:

```python
# Before (hard-coded)
client = OpenAI(api_key="sk-abc123")

# After (environment variable)
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
```

## Integration with Development Standards

From `docs/DEVELOPMENT_STANDARDS.md`:

**When creating components that use secrets:**
- [ ] Never hard-code credentials
- [ ] Use environment variables or GitHub Secrets
- [ ] Add `.env.template` with placeholder values
- [ ] Update `.gitignore` to exclude real `.env` files
- [ ] Document required secrets in README
- [ ] Test with mock/sandbox credentials first

## Audit and Compliance

### Regular Reviews

Monthly secret scanning review checklist:
- [ ] Review all secret scanning alerts
- [ ] Verify no secrets in recent commits
- [ ] Audit GitHub Secrets usage
- [ ] Rotate credentials older than 90 days
- [ ] Review access to environment secrets

### Audit Log

Track secret-related events:
- Secret scanning alert created/resolved
- GitHub Secret created/updated/accessed
- Environment secret accessed
- Deployment to production environment

Access via: Settings → Audit log

## Responding to Security Incidents

### If a Secret is Leaked

1. **Immediate Actions (< 1 hour):**
   - Revoke/rotate the compromised credential
   - Assess impact (what could be accessed?)
   - Block suspicious activity if detected

2. **Investigation (< 24 hours):**
   - Review audit logs
   - Identify when/how secret was leaked
   - Check for unauthorized access
   - Document timeline

3. **Remediation (< 1 week):**
   - Remove secret from git history
   - Update documentation
   - Improve prevention (add checks)
   - Train team if needed

4. **Post-Mortem:**
   - Write incident report
   - Update security practices
   - Add prevention measures

### Notification Channels

For security incidents:
- Telegram: Critical alerts
- GitHub Issues: For tracking remediation
- Email: For compliance/audit trail

## Resources

- [GitHub Secret Scanning Docs](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning)
- [Push Protection](https://docs.github.com/en/code-security/secret-scanning/push-protection-for-users)
- [Partner Patterns](https://docs.github.com/en/code-security/secret-scanning/secret-scanning-patterns)
- [Custom Patterns](https://docs.github.com/en/code-security/secret-scanning/defining-custom-patterns-for-secret-scanning)

---

**Last Updated:** 2025-12-01  
**Owner:** Security Team  
**Related:** `docs/GITHUB_ENVIRONMENTS.md`, `docs/DEVELOPMENT_STANDARDS.md`
