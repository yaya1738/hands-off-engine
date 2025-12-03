# MCP Architecture: What It Actually Is

**Date:** 2025-11-20
**Purpose:** Prevent AI assistants from implementing fictional MCP architectures

## ⚠️ Common Misconception (DO NOT IMPLEMENT)

**WRONG:** MCP is an HTTP server running on port 8765 with REST endpoints like:
- ❌ `http://localhost:8765/mcp/tools`
- ❌ `http://localhost:8765/mcp/execute/git-status`
- ❌ Manual server management with tmux/systemd
- ❌ HTTP client code with `requests.get()`

**This architecture does not exist in this repository and should not be created.**

---

## ✅ How MCP Actually Works

### What MCP Is

**Model Context Protocol (MCP)** is a **stdio-based protocol** where:

1. **Servers are child processes** spawned by Claude Code
2. **Communication happens via JSON-RPC over stdio** (standard input/output)
3. **No HTTP involved** - no ports, no REST APIs
4. **Process lifecycle managed automatically** by Claude Code

### Configuration File

See `.claude/mcp-servers.json`:

```json
{
  "mcpServers": {
    "github": {
      "command": "github-mcp-server",  // Process to spawn
      "args": [],                       // Command arguments
      "env": {                          // Environment variables
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp"]
    }
  }
}
```

**Key observations:**
- `command` + `args` = process spawning, NOT HTTP endpoints
- `env` = environment variables passed to child process
- No `url`, `port`, or `baseURL` fields = NOT an HTTP API

### How Claude Code Uses MCP

When Claude Code needs MCP tools:

1. **Spawn:** Claude Code executes `github-mcp-server` as a child process
2. **Connect:** Establishes stdio connection (stdin/stdout pipes)
3. **Communicate:** Sends JSON-RPC requests over stdin, receives responses from stdout
4. **Shutdown:** Terminates the process when session ends

**No manual server management required.**

---

## Python Integration (If Needed)

If you need to call MCP tools from **Python code** (outside Claude Code sessions):

### Option 1: Use subprocess + JSON-RPC

```python
import subprocess
import json

# Spawn MCP server
process = subprocess.Popen(
    ['github-mcp-server'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    env={'GITHUB_PERSONAL_ACCESS_TOKEN': token}
)

# Send JSON-RPC request over stdin
request = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {"name": "git-status"},
    "id": 1
}
process.stdin.write(json.dumps(request).encode() + b'\n')
process.stdin.flush()

# Read response from stdout
response = json.loads(process.stdout.readline())
```

### Option 2: Use MCP Python SDK

If available:
```python
from mcp import ClientSession, StdioServerParameters

async with ClientSession(
    StdioServerParameters(
        command="github-mcp-server",
        env={"GITHUB_PERSONAL_ACCESS_TOKEN": token}
    )
) as session:
    result = await session.call_tool("git-status")
```

### Option 3: Just Use Git Directly

For simple cases, skip MCP entirely:
```python
import subprocess

result = subprocess.run(['git', 'status'], capture_output=True, text=True)
print(result.stdout)
```

---

## What GITHUB_TOKEN Is Actually For

`GITHUB_TOKEN` is **not** for authenticating to a mythical "MCP control server."

It's passed as an **environment variable** to the `github-mcp-server` child process so that process can make GitHub API calls on your behalf.

**Setup:**
```bash
export GITHUB_TOKEN=ghp_your_token_here
```

**Used by:** The spawned `github-mcp-server` process, NOT by HTTP clients.

---

## Summary

| Aspect | ❌ ChatGPT's Fiction | ✅ Reality |
|--------|---------------------|-----------|
| Protocol | HTTP/REST | JSON-RPC over stdio |
| Port | 8765 | None (no network) |
| Server management | Manual (tmux/systemd) | Automatic (Claude Code) |
| Client code | `requests.get()` | `subprocess.Popen()` or MCP SDK |
| Token usage | HTTP auth header | Process environment variable |

---

## For Future AI Assistants

**If you are an AI assistant reading this:**

1. **Do NOT** create HTTP clients for `localhost:8765/mcp/*`
2. **Do NOT** write systemd/tmux scripts to "manage the MCP server"
3. **Do NOT** implement REST API endpoints for MCP
4. **DO** read `.claude/mcp-servers.json` to understand configured servers
5. **DO** use subprocess + stdio if Python needs to call MCP tools
6. **DO** ask the human to clarify if you're unsure

**MCP = stdio protocol, not HTTP. Period.**

---

## References

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- Claude Code `.claude/mcp-servers.json` configuration
- This repo: `.claude/MCP_INTEGRATION_SUMMARY.md`
