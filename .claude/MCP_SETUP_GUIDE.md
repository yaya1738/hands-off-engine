# MCP Servers Setup Guide

This guide explains how to set up and use the GitHub and Playwright MCP servers with Claude Code.

## Overview

Two Model Context Protocol (MCP) servers have been configured for the Hands-Off Engine:

1. **GitHub MCP Server** - Git operations and repository management
2. **Playwright MCP Server** - Web browser automation and testing

## Installation Status

✅ Both servers are already installed globally:
- `github-mcp-server` (v1.8.7)
- `@playwright/mcp` (v0.0.47)

## GitHub MCP Server Setup

### Features
- 30 MCP operations for Git management
- 33 CLI aliases for common Git tasks
- Support for all standard Git workflows

### Configuration

The GitHub MCP server requires a GitHub Personal Access Token:

```bash
# Option 1: Export as environment variable
export GITHUB_TOKEN=your_github_token_here

# Option 2: Create .claude/.env file (do not commit)
echo "GITHUB_TOKEN=your_github_token_here" > .claude/.env
```

### Getting a GitHub Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" (classic)
3. Select scopes: `repo`, `workflow`, `admin:org_hook`
4. Copy the token (you won't see it again)
5. Store it securely (use .env file, not in code)

### Available Commands

**File Operations:**
- `git-init` - Initialize a new Git repository
- `git-add` - Add specific files to staging
- `git-add-all` - Add all files to staging
- `git-remove` - Remove file from staging
- `git-remove-all` - Remove all files from staging

**Information:**
- `git-status` - Show repository status
- `git-log` - Show commit history
- `git-diff` - Show differences

**Commit & Sync:**
- `git-commit` - Commit staged changes
- `git-push` - Push to remote repository
- `git-pull` - Pull from remote repository

**Branch Management:**
- `git-branch` - List branches or create new one
- `git-checkout` - Switch to branch

**Stash Operations:** (and more advanced workflows)

## Playwright MCP Server Setup

### Features
- Browser automation and control
- Page navigation and interaction
- Screenshot capture
- HTML content extraction
- JavaScript evaluation in browser context

### Configuration

No additional configuration needed! The Playwright MCP server uses the globally installed package.

### Available Tools

- `navigate` - Navigate to a URL
- `click` - Click on elements
- `fill` - Fill text inputs
- `screenshot` - Capture page screenshot
- `get_page_html` - Get page HTML content
- `evaluate` - Execute JavaScript in browser
- `wait` - Wait for conditions
- `new_page` - Open new browser page
- `close_page` - Close browser page

## Starting the MCP Servers

### Method 1: Automatic (Recommended for Claude Code)

Claude Code automatically starts configured MCP servers when needed. Ensure the `mcp-servers.json` file is properly configured.

### Method 2: Manual Testing

Test that servers can start:

```bash
# Test GitHub MCP server
github-mcp-server --help

# Test Playwright MCP server
npx @playwright/mcp --help
```

### Method 3: Direct Execution

Start servers directly in separate terminals:

```bash
# Terminal 1: GitHub MCP server
export GITHUB_TOKEN=your_token
github-mcp-server

# Terminal 2: Playwright MCP server
npx @playwright/mcp
```

## Integration with Claude Code

The MCP servers are configured in `.claude/mcp-servers.json` for automatic discovery and integration.

Claude Code will:
1. Detect available MCP servers from the configuration
2. Start them on demand when tools are requested
3. Route requests to appropriate servers
4. Handle server lifecycle and cleanup

## Troubleshooting

### GitHub MCP Server Issues

**Error: "GITHUB_TOKEN not set"**
- Solution: Export GITHUB_TOKEN environment variable
- Command: `export GITHUB_TOKEN=your_token`

**Error: "Command not found: github-mcp-server"**
- Solution: Reinstall the package
- Command: `npm install -g github-mcp-server`

### Playwright MCP Server Issues

**Error: "Playwright not installed"**
- Solution: Ensure @playwright/mcp is installed
- Command: `npm install -g @playwright/mcp`

**Browser installation**
- First run may take longer as Playwright downloads browsers
- This is normal and happens only once

## Best Practices

1. **Never commit tokens** - Use environment variables or .env files
2. **Use scoped tokens** - GitHub tokens should have minimal required permissions
3. **Rotate tokens regularly** - Follow GitHub security best practices
4. **Monitor server logs** - Check for errors or performance issues

## Advanced Configuration

For production use in CI/CD pipelines:

```bash
# Use GitHub Actions secrets
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

# Or use Termux environment setup
# Store in ~/.bashrc or Termux startup scripts
```

## Integration with Hands-Off Engine

These MCP servers enable:

1. **Automated GitHub operations** - Issue creation, PR management, workflow triggers
2. **Web-based data collection** - Scraping market data, fetching pages
3. **Market surveillance** - Monitoring odds changes, detecting anomalies
4. **Automation** - Scheduled tasks, event-driven workflows

Example use cases:

- Fetch latest Polymarket data from web pages
- Automatically create GitHub issues for trading opportunities
- Monitor GitHub workflows for trading signal updates
- Test web interfaces for market platforms

## Next Steps

1. [x] Install MCP servers
2. [x] Create configuration file
3. [ ] Set up GITHUB_TOKEN if using GitHub operations
4. [ ] Test servers in Claude Code
5. [ ] Integrate with Alpha pipeline
6. [ ] Create automated workflows

See `.claude/mcp-servers.json` for configuration details.

---

**Last Updated:** 2025-11-20
**Status:** Ready for use
