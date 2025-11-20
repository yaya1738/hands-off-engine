# MCP context assessment

## Reality check: how MCP works here (not HTTP)

* The repo **already defines MCP servers** in `.claude/mcp-servers.json`: `github-mcp-server` and `@playwright/mcp` are invoked as child processes.
* Communication is **stdio JSON-RPC** only. There is **no** port listener, `localhost:8765`, `/mcp/tools`, or any REST API to curl.
* `GITHUB_TOKEN` is passed as an environment variable to the GitHub MCP process; it is **not** a credential for an HTTP control plane.

## Operational expectations for contributors

* Let **Claude Code** manage the lifecycle: it reads `.claude/mcp-servers.json`, spawns the binaries when needed, and shuts them down at session end. Do **not** add tmux/supervisor/curl health checks.
* To use MCP tools successfully, ensure the binaries are available locally (`github-mcp-server`, `npx @playwright/mcp`) and set `GITHUB_TOKEN` before launching Claude Code.
* If you build “MCP-aware” features in this codebase, treat MCP as **Claude-side tools** available during a Claude Code session—not as a networked service the Hands-Off engine can call directly.

## Guardrails against past hallucinations

* Avoid introducing HTTP calls (e.g., `requests.get("http://localhost:8765/mcp/tools")`) or references to `/mcp/*` endpoints; they do not exist here.
* Documentation, tests, and future planners should explicitly assume stdio MCP and avoid implying a long-running control server.
