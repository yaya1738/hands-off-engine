# AI Intake Setup Guide

## Required Setup Steps

### Step 1: Configure OpenAI API Key Secret

**Location:** `https://github.com/yaya1738/hands-off-engine/settings/secrets/actions`

1. Navigate to: `Settings → Secrets and variables → Actions`
2. Look for a secret named **`OPENAI_API_KEY`**
   - If it exists: You're good to go (or update it if unsure)
   - If it doesn't exist: Click **"New repository secret"**
3. Create/Update the secret:
   - **Name:** `OPENAI_API_KEY`
   - **Value:** Your OpenAI API key
   - Click **"Add secret"** or **"Update secret"**

**Important Notes:**
- Secrets are **repo-level**, not branch-level
- One secret covers all branches in the repository
- It's safe to edit/overwrite an existing secret if you're uncertain about it
- The workflow references it as: `${{ secrets.OPENAI_API_KEY }}`

### Step 2: Merge Feature Branch to Main

**Branch:** `claude/add-standard-instructions-019TsC9NXytzdv4ZMciBSt4a`

1. Open the pull request for this branch on GitHub
2. Review the changes:
   - `ai/ai_intake_handler.py` - Handler script
   - `.github/workflows/ai-intake.yml` - GitHub Actions workflow
   - `ai/requirements.txt` - Dependencies
   - Documentation updates
3. Click **"Merge pull request"**
4. Confirm merge

**Why this matters:**
- GitHub Actions only runs workflows from the default branch (`main`)
- Until merged, the `/plan` trigger won't work on issues

### Step 3: Test the AI Intake Workflow

**Issue to use:** Issue #1 (or whichever you designate as "AI Intake")

1. Navigate to the AI Intake issue
2. Add a new comment with exactly:
   ```
   /plan
   ```
3. Verify it works:
   - Go to **Actions tab → "AI Intake" workflow** to see the run
   - Check the issue for a bot comment with "🤖 AI Intake – Plan" header

**Troubleshooting:**
- If workflow fails with "`OPENAI_API_KEY` not set":
  - Verify the secret exists (Step 1)
  - Check the workflow's `env:` block references it correctly
- If workflow doesn't trigger at all:
  - Verify the branch is merged to `main` (Step 2)
  - Verify you commented on the correct issue number

## How the Auto-Context Loading Works

### When Using AI Intake Workflow (GitHub Issues)
✅ **Automatic** - No manual context pasting required

The workflow automatically:
1. Triggers on `/plan` comment
2. Checks out the repository
3. Reads `AI_POLICY.md` from the repo
4. Reads `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md` from the repo
5. Sends both to OpenAI API as context
6. Posts the generated plan back as a comment

**You do NOT need to:**
- Copy/paste `AI_POLICY.md` anywhere
- Copy/paste the research report anywhere
- Manually provide context to the AI

### When Using ChatGPT Directly (Outside GitHub)
❌ **Manual** - Context must be provided

When chatting with ChatGPT in their web interface:
- ChatGPT cannot access your GitHub repository
- You must manually paste context OR upload files
- The auto-loading only works for the GitHub Actions workflow

## Workflow Configuration

**Default Settings:**
- AI Intake issue number: `1`
- Triggers on: `issue_comment.created` events
- OpenAI model: `gpt-4o-mini`
- Python version: `3.11`

**To change AI Intake issue number:**
Edit `.github/workflows/ai-intake.yml`:
```yaml
env:
  AI_INTAKE_ISSUE_NUMBER: "1"  # Change this number
```

## Verification Checklist

Before testing `/plan`:
- [ ] `OPENAI_API_KEY` secret exists in repo settings
- [ ] Branch `claude/add-standard-instructions-*` is merged to `main`
- [ ] Issue #1 exists (or designated AI Intake issue exists)
- [ ] Workflow file `.github/workflows/ai-intake.yml` is on `main` branch

After testing `/plan`:
- [ ] GitHub Action ran successfully (check Actions tab)
- [ ] Bot posted a plan comment on the issue
- [ ] Plan content references the research report and roadmap

## Next Steps

Once `/plan` is working, potential future commands to add:
- `/apply` - Generate and create a PR with proposed changes
- `/status` - Summarize current system state from `state/*.json`
- `/risk` - Analyze risk model outputs
- `/todo` - Extract actionable tasks from roadmap
