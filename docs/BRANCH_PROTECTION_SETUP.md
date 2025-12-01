# Branch Protection Setup Guide

## Overview

This document describes the recommended branch protection rules for the `main` branch. These rules ensure code quality and safety while enabling autonomous operation where appropriate.

**Note:** Branch protection rules must be configured manually in the GitHub repository settings. This document serves as the canonical reference for the desired configuration.

---

## Accessing Branch Protection Settings

1. Go to repository Settings
2. Navigate to Branches (under "Code and automation")
3. Click "Add rule" or edit existing rule for `main`

---

## Recommended Branch Protection Rules for `main`

### Basic Settings

- **Branch name pattern:** `main`
- **Require a pull request before merging:** ✅ Enabled
  - **Require approvals:** 0 (allows auto-merge from trusted bots)
  - **Dismiss stale pull request approvals when new commits are pushed:** ✅ Enabled
  - **Require review from Code Owners:** ⚠️ Optional (see notes below)

### Status Checks

- **Require status checks to pass before merging:** ✅ Enabled
  - **Require branches to be up to date before merging:** ✅ Enabled
  - **Status checks that are required:**
    - `test` (from CI workflow)
    - Any other critical checks as they are added

### Additional Settings

- **Require conversation resolution before merging:** ⚠️ Optional
- **Require signed commits:** ❌ Disabled (bot commits are not signed)
- **Require linear history:** ❌ Disabled (allows merge commits)
- **Include administrators:** ✅ Enabled (protection applies to all)

### Push Restrictions

- **Restrict who can push to matching branches:** ❌ Disabled
  - Reason: Auto-merge workflow needs to push merge commits
  
### Force Push

- **Allow force pushes:** ❌ Disabled
- **Allow deletions:** ❌ Disabled

---

## Code Owners and Auto-Merge

The `.github/CODEOWNERS` file designates ownership for specific files and directories. However, for auto-merge to work:

1. **CODEOWNERS review can be optional** - The auto-merge workflow checks if PRs are from trusted sources
2. **Trusted sources are defined in** `.github/workflows/auto-merge.yml`
3. **Critical files listed in CODEOWNERS** should trigger human review even if auto-merge is enabled

### Balancing Auto-Merge with Code Owners

**Option A: CODEOWNERS required (more secure)**
- Enable "Require review from Code Owners"
- Auto-merge will only work after owner approves
- Good for: Critical infrastructure changes

**Option B: CODEOWNERS optional (more autonomous)**
- Disable "Require review from Code Owners"  
- Auto-merge relies on trusted bot list in workflow
- Auto-merge workflow already checks critical files
- Good for: Day-to-day autonomous operation

**Recommendation:** Option B for maximum autonomy, with critical files flagged in auto-merge workflow logic.

---

## Status Checks Configuration

As new CI workflows are added, required status checks should be updated:

### Currently Available Checks

1. **CI Tests** (`.github/workflows/ci.yml`)
   - Job name: `test`
   - Runs: Tests, linting, type checking
   - Should be required: ✅ Yes

2. **Pre-commit Checks** (`.github/workflows/pre-commit.yml`)
   - Job name: `pre-commit`
   - Runs: Formatting, secrets scanning
   - Should be required: ⚠️ Optional (currently warnings-only)

### Future Checks to Add

- CodeQL analysis (when enabled)
- Security scans
- Build verification
- Integration tests

---

## Merge Strategies

**Allowed merge methods:**
- ✅ **Squash merging** (recommended, used by auto-merge)
- ✅ Merge commits (for manual merges)
- ⚠️ Rebase merging (optional)

**Auto-merge workflow uses:** Squash merging with `--delete-branch`

---

## Deployment Branch Protection

For production deployments using the deploy workflow:

1. **Create deployment environments** in Settings > Environments
2. **`production` environment should require:**
   - Deployment from `main` branch only
   - Required reviewers (owner approval)
   - Environment secrets properly configured

---

## Testing Branch Protection

After configuring branch protection:

1. Create a test branch and PR
2. Verify required checks run and must pass
3. Test that auto-merge workflow can merge (if using trusted bot)
4. Verify force push is blocked
5. Verify direct push to main is blocked

---

## Troubleshooting Auto-Merge

If auto-merge is not working:

1. **Check branch protection settings**
   - "Require a pull request before merging" should be enabled
   - Required approvals should be 0 (or bot should approve)
   - Status checks should pass

2. **Check auto-merge workflow**
   - PR author is in `TRUSTED_AUTHORS` env var
   - All status checks have completed successfully
   - PR is not a draft

3. **Check GitHub permissions**
   - Auto-merge workflow has `contents: write` and `pull-requests: write`
   - GitHub token has sufficient permissions

---

## Updating Branch Protection

When adding new critical workflows or checks:

1. Update this document with the new requirement
2. Add the status check name to branch protection settings
3. Update the auto-merge workflow if needed
4. Test with a sample PR

---

## Emergency Access

In case branch protection needs to be temporarily bypassed:

1. **Prefer:** Create an emergency PR that passes all checks
2. **If critical:** Owner can temporarily disable protection
   - Make the urgent change
   - Re-enable protection immediately
   - Document the bypass in an issue

**Never leave branch protection disabled.**

---

## Summary Checklist

When setting up branch protection for `main`:

- [ ] Require pull requests (0 approvals for auto-merge)
- [ ] Require status checks (`test` job from CI)
- [ ] Require branches up to date
- [ ] Disable force push and deletions
- [ ] Apply rules to administrators
- [ ] Configure CODEOWNERS (optional enforcement)
- [ ] Test auto-merge with sample PR
- [ ] Document any deviations from this guide

---

**Last Updated:** 2025-12-01  
**Maintained By:** Repository owner (@yaya1738)  
**Related Files:**
- `.github/workflows/auto-merge.yml`
- `.github/CODEOWNERS`
- `.github/workflows/ci.yml`
