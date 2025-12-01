# GitHub Environments for Trading Mode Protection

This document explains how to use GitHub Environments to protect LIVE trading deployments while allowing automated DRYRUN operations.

## Overview

The Hands-Off Engine operates in two modes:
- **DRYRUN** (staging): Simulated trading, safe for automation
- **LIVE** (production): Real money trading, requires human approval

GitHub Environments provide deployment protection rules to ensure LIVE trading changes require explicit approval.

## Environment Configuration

### 1. Staging Environment (DRYRUN Mode)

**Purpose:** Testing and automated dry-run trading  
**Protection:** None (fully automated)  
**Usage:** All PR merges, automated deployments

**Configuration Steps:**
1. Go to Settings → Environments → New environment
2. Name: `staging`
3. Protection rules: None needed (auto-deploy is safe)
4. Environment secrets (if different from production):
   - `TRADING_MODE=DRYRUN`
   - API keys for test/sandbox accounts

### 2. Production Environment (LIVE Mode)

**Purpose:** Real money trading operations  
**Protection:** Manual approval required  
**Usage:** Explicit deployment to LIVE trading

**Configuration Steps:**
1. Go to Settings → Environments → New environment
2. Name: `production`
3. Protection rules:
   - ✅ Required reviewers: Add trusted users (e.g., @yaya1738)
   - ✅ Wait timer: Optional (e.g., 5 minutes to allow review)
   - ⚠️ DO NOT enable auto-merge for production deployments
4. Environment secrets:
   - `TRADING_MODE=LIVE`
   - Real API keys and credentials (encrypted by GitHub)
   - `POLYMARKET_API_KEY`
   - `ALPACA_API_KEY`
   - `OPENAI_API_KEY`
   - `TELEGRAM_BOT_TOKEN`

## Using Environments in Workflows

### Example: Deployment Workflow

```yaml
name: Deploy Trading System

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        type: choice
        options:
          - staging
          - production

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment }}
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Deploy to environment
        run: |
          echo "Deploying to ${{ github.event.inputs.environment }}"
          # Deployment logic here
        env:
          TRADING_MODE: ${{ secrets.TRADING_MODE }}
          API_KEY: ${{ secrets.POLYMARKET_API_KEY }}
```

### Example: Auto-merge Skip for Production Files

The auto-merge workflow should skip certain critical files that affect LIVE trading:

```yaml
# In .github/workflows/auto-merge.yml (already implemented)
# Critical files that require human approval:
# - .env* files
# - **/secrets/**
# - executor/ho_executor.py (live trade execution)
# - state/risk_profile.json (risk parameters)
```

## Manual Approval Process

When deploying to production:

1. **Trigger deployment:**
   ```bash
   # Via GitHub UI: Actions → Deploy Trading System → Run workflow
   # Select "production" environment
   ```

2. **Review required:**
   - GitHub will pause the deployment
   - Tagged reviewers get notification
   - Review changes in the deployment
   - Approve or reject

3. **Approval:**
   - Reviewer clicks "Review pending deployments"
   - Checks changes are safe for LIVE mode
   - Approves deployment
   - Workflow continues

## Security Considerations

### Environment Secrets Best Practices

1. **Never commit secrets to code**
   - Use GitHub environment secrets
   - Reference via `${{ secrets.SECRET_NAME }}`

2. **Separate credentials per environment**
   - Staging uses sandbox/test API keys
   - Production uses real API keys
   - Never share keys between environments

3. **Audit access**
   - Regularly review who has access to production environment
   - Remove access for inactive users
   - Use GitHub audit log to track secret access

### Protection Against Accidents

The environment system prevents:
- ✅ Accidental LIVE trading from automated PRs
- ✅ Unauthorized changes to production configuration
- ✅ API key exposure in logs (secrets are masked)
- ✅ Deployment without human verification

## Integration with Auto-Merge

The auto-merge workflow (`.github/workflows/auto-merge.yml`) already implements critical file protection:

```yaml
env:
  TRUSTED_AUTHORS: "copilot,github-actions[bot],dependabot[bot]"
```

**Critical files requiring human approval:**
- `.env*` files (environment configuration)
- `**/secrets/**` (credential storage)
- `.github/workflows/auto-merge.yml` (the auto-merge workflow itself)
- `executor/ho_executor.py` (live trade execution)
- `state/risk_profile.json` (risk parameters)

These files should be protected by:
1. Branch protection rules
2. CODEOWNERS file (optional)
3. Manual review requirement in auto-merge workflow

## Environment Variables vs. Secrets

| Type | Storage | Usage | Example |
|------|---------|-------|---------|
| Environment Variable | Workflow file | Public configuration | `PYTHON_VERSION: "3.11"` |
| Environment Secret | Settings → Environments | Sensitive data | `${{ secrets.API_KEY }}` |
| Repository Secret | Settings → Secrets | Shared across environments | `${{ secrets.GITHUB_TOKEN }}` |

## Monitoring and Alerts

### Deployment Notifications

Configure Telegram notifications for production deployments:

```yaml
- name: Notify deployment
  if: environment == 'production'
  run: |
    python telegram/notify.py "🚀 LIVE deployment initiated"
```

### Audit Trail

All production deployments are logged:
- GitHub Actions logs (retained per repo settings)
- Deployment history in Environments tab
- Audit log for secret access

## Migration Path

To implement environments in existing repository:

1. ✅ Create `staging` and `production` environments (manual in GitHub UI)
2. ✅ Add environment secrets (manual in GitHub UI)
3. ✅ Update deployment workflows to use environments (create if needed)
4. ✅ Test staging deployment
5. ⚠️ Test production deployment approval flow
6. ✅ Document for team in this file

## Future Enhancements

Potential improvements:
- [ ] Auto-create environments via GitHub API
- [ ] Terraform/IaC for environment configuration
- [ ] Integration tests that run in staging before production
- [ ] Automated rollback on production failures
- [ ] Gradual rollout (canary deployments)

## References

- [GitHub Environments Documentation](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [Environment Protection Rules](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment#environment-protection-rules)
- [Repository Secrets vs Environment Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

---

**Last Updated:** 2025-12-01  
**Owner:** Hands-Off Engine Team  
**Related:** `docs/DEVELOPMENT_STANDARDS.md`, `docs/RISK_MODEL_V1.md`
