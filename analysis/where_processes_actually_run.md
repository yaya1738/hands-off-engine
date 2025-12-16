# WHERE PROCESSES ACTUALLY RUN
## Complete Execution Environment Map

**Date:** December 5, 2025
**Current Session:** SSH from phone → ho-cli-main (165.22.176.190)

---

## EXECUTION ENVIRONMENT BREAKDOWN

### 1. ON HO-CLI-MAIN DROPLET (165.22.176.190)

**What runs here RIGHT NOW:**

#### A. Active Processes (from ps aux scan)
```
Process                          CPU    RAM    What It Does
─────────────────────────────────────────────────────────────
python3 MONEY_PRINTER.py         307%   0.4%   Live trading execution
                                               (using 3+ CPU cores)

python3 autonomous/              <10%   0.3%   Backend loop orchestration
  backend_loop.py                              (runs every 5 minutes)

Claude Code CLI                  <5%    0.2%   This session (Node.js process)
                                               Running your commands

sshd                             <1%    0.1%   Your SSH connection from phone
```

#### B. Claude Code MCP Servers (run as child processes)
```
MCP Server          Port    What It Does
──────────────────────────────────────────────────
mcp-github          N/A     GitHub API operations
                            (create issues, PRs, search code)

mcp-playwright      N/A     Browser automation
                            (headless Chrome/Firefox)
```

#### C. System Services
```
Service             What It Does
────────────────────────────────────────────────
systemd             Linux init system
cron                Scheduled tasks (if configured)
sshd                SSH server (you're connected to this)
docker              Container runtime (if trading uses it)
```

#### D. File System Operations
```
Activity                        Where
──────────────────────────────────────────────────
Read/Write state files          /root/hands-off-engine/state/
Read/Write logs                 /root/hands-off-engine/logs/
Read code                       /root/hands-off-engine/
Write analysis files            /root/hands-off-engine/analysis/
Git operations                  /root/hands-off-engine/.git/
```

---

### 2. ON ANTHROPIC SERVERS (External)

**What runs here:**

```
Process                          What It Does
─────────────────────────────────────────────────────────────
Claude AI Inference             • Reads your messages
                                • Processes instructions
                                • Generates responses
                                • Decides which tools to call
                                • All the "thinking" happens here

Model: claude-sonnet-4-5-20250929
Location: Anthropic's infrastructure
Cost: Your API usage
```

**Data flow:**
```
You type → Anthropic servers process → Response sent back → CLI displays
          ↓
          Anthropic decides to use tool (e.g., Read, Write, Bash)
          ↓
Tool executes ON DROPLET → Result sent to Anthropic → Anthropic processes
```

---

### 3. ON GITHUB'S INFRASTRUCTURE (GitHub Actions)

**What runs here: Production Automation**

```
Workflow                          Triggers                        What It Does
──────────────────────────────────────────────────────────────────────────────────
agent-coordination-notify.yml     • Push to ai/coordination/      • Monitors agent messages
                                  • workflow_dispatch             • Creates GitHub issues
                                                                  • Triggers coordination events
                                                                  • Notifies other agents

auto-merge.yml                    • PR opened/synced              • Auto-merges trusted PRs
                                  • Checks completed              • Zero-touch repo management
                                  • workflow_dispatch             • Copilot/bot PRs → auto-merge
                                  • repository_dispatch

ai-intake.yml                     • (Various triggers)            • Handles AI intake processes

Runner Environment:               ubuntu-latest (GitHub-hosted)
Cost:                            Free (public repo) / Usage-based (private)
Recent Activity:                 5 runs in last 24 hours
Status:                          Some workflows failing (need attention)
```

**Key Point:** These workflows are PRODUCTION AUTOMATION running on GitHub's servers, triggered by production events (commits, PRs, coordination messages). They modify the production system (create issues, merge PRs, coordinate agents).

---

### 4. ON EXTERNAL API SERVICES

**What runs here:**

```
Service             What Happens There                     Called From
──────────────────────────────────────────────────────────────────────
Polymarket API      • Order placement                      Droplet
polymarket.com      • Market data fetching                 (MONEY_PRINTER.py)
                    • Position queries
                    • Trade execution

GitHub API          • Repo operations                      Droplet + GitHub Actions
api.github.com      • Issue/PR creation                    (mcp-github + workflows)
                    • Code searches
                    • Repository dispatch events

GitHub.com          • Git clone/pull/push                  Droplet
github.com          • Repo hosting                         (git commands)
                    • Workflow execution

Blockchain RPC      • Wallet queries                       Droplet
(Polygon)           • Transaction submission               (trading system)
                    • Balance checks
```

---

## DETAILED: WHAT'S ON THE DROPLET

### Currently Running Python Processes

**1. MONEY_PRINTER.py (307% CPU)**
```python
Location: /root/hands-off-engine/MONEY_PRINTER.py
What: Live trading execution
CPU: 307% (using 3+ cores)
RAM: ~60MB

What it's doing RIGHT NOW:
├── Connecting to Polymarket API
├── Fetching market data
├── Calculating positions
├── Placing orders
├── Monitoring execution
└── Writing to state/money_printer.json
```

**2. backend_loop.py (Periodic)**
```python
Location: /root/hands-off-engine/autonomous/backend_loop.py
What: Orchestrates 10+ subsystems
CPU: <10% (spikes every 5 min)
RAM: ~40MB

Runs every 5 minutes:
├── Check trading status
├── Update AI intelligence
├── Sync wallet state
├── Health diagnostics
├── Process job hunting tasks
├── M2M communication
├── Update coordination state
└── Save system state
```

### Claude Code CLI Process

```
Process: node (Claude Code CLI)
Location: Wherever Claude Code is installed
CPU: <5%
RAM: ~200MB

What it does:
├── Accepts your typed commands
├── Sends to Anthropic API
├── Receives tool calls from Claude
├── Executes tools locally:
│   ├── Bash commands → run on droplet
│   ├── Read/Write → file operations on droplet
│   ├── Grep/Glob → search on droplet
│   └── MCP tools → call MCP servers on droplet
├── Sends results back to Anthropic
└── Displays Claude's response to you
```

### MCP Server Processes

```
1. MCP GitHub Server
   Process: node (mcp-github)
   CPU: <1% (when used)
   RAM: ~50MB

   What it does:
   ├── Receives tool calls from Claude Code CLI
   ├── Makes GitHub API requests
   ├── Returns results to CLI
   └── Runs on droplet, calls api.github.com

2. MCP Playwright Server
   Process: node (mcp-playwright)
   CPU: <5% (when used)
   RAM: ~100MB

   What it does:
   ├── Launches headless browser (Chrome/Firefox)
   ├── Navigates web pages
   ├── Takes screenshots
   ├── Returns results
   └── Browser runs ON DROPLET, fetches from web
```

---

## RESOURCE USAGE BREAKDOWN

### Current Active Usage (from scan)

```
Component               CPU      RAM       Storage    Network
──────────────────────────────────────────────────────────────
MONEY_PRINTER           307%     60MB      ~1MB/sec   5-10 Mbps
backend_loop            <10%     40MB      ~100KB/5m  1-2 Mbps
Claude Code CLI         <5%      200MB     Minimal    Variable
MCP Servers             <5%      150MB     Minimal    Variable
System (OS, SSH, etc)   10%      500MB     N/A        <1 Mbps
──────────────────────────────────────────────────────────────
TOTAL USED              ~330%    950MB     ~1MB/sec   5-15 Mbps
AVAILABLE (8 vCPU)      470%     15GB      310GB      990 Mbps
```

### Storage Activity

```
File/Directory                   Size      Access Pattern
────────────────────────────────────────────────────────────
state/money_printer.json         12KB      Write: every order
state/wallet_state.json          8KB       Write: every 5 min
logs/hft_economics.jsonl         450MB     Append: continuous
logs/abcfc_cycles.jsonl          89MB      Append: every cycle
logs/executions.jsonl            125MB     Append: every trade
integrafix/                      15MB      Read: frequent
autonomous/                      8MB       Read: every 5 min
executor/                        12MB      Read: frequent
```

---

## DATA FLOW EXAMPLES

### Example 1: You Ask Claude to Read a File

```
[Phone] → [Anthropic Servers] → [Droplet]
   ↓           ↓                     ↓
You type    Claude processes    Read tool executes
            and decides to          ↓
            call Read tool      Opens file on droplet
                ↑                   ↓
            Result sent back    Reads contents
                ↑                   ↓
            [Anthropic]  ←──────  Sends back
                ↓
            Claude formats response
                ↓
            [Phone] displays it
```

### Example 2: MONEY_PRINTER Places Trade

```
[Droplet: MONEY_PRINTER.py]
    ↓
Calculates opportunity
    ↓
Generates order
    ↓
[Droplet: Network] → [Polymarket API]
    ↓
polymarket.com receives order
    ↓
Matches order on exchange
    ↓
[Polymarket API] → [Droplet]
    ↓
MONEY_PRINTER receives confirmation
    ↓
Writes to state/money_printer.json (on droplet)
    ↓
Writes to logs/executions.jsonl (on droplet)
```

### Example 3: You Ask Claude to Create GitHub PR

```
[Phone] → [Anthropic] → [Droplet: Claude Code CLI]
                            ↓
                        Calls mcp-github tool
                            ↓
                        [Droplet: MCP GitHub Server]
                            ↓
                        Makes API request to api.github.com
                            ↓
                        [GitHub API] creates PR
                            ↓
                        Returns PR URL
                            ↓
                        [MCP Server] → [CLI] → [Anthropic] → [Phone]
```

---

## WHAT'S NOT ON THE DROPLET

```
Activity                        Where It Actually Is
──────────────────────────────────────────────────────────
Claude's "thinking"             Anthropic servers
Model inference                 Anthropic servers
GitHub repo hosting             GitHub.com
GitHub Actions workflows        GitHub's runner infrastructure
Polymarket order matching       Polymarket exchange servers
Blockchain state                Polygon network nodes
DNS resolution                  Internet DNS servers
Package downloads (pip/npm)     PyPI / npm registry
```

---

## PRODUCTION vs DEVELOPMENT

### This Session (RIGHT NOW)

```
Location: ho-cli-main (prod droplet) + GitHub (prod repo)
Mode: PRODUCTION ACROSS 4 ENVIRONMENTS
Risk: HIGH

What this means:
├── All changes affect LIVE system
├── MONEY_PRINTER is trading with REAL money
├── Git commits trigger production workflows
├── GitHub Actions modify production repo
├── No safety net / rollback
├── No separate dev environment
└── Development happening IN production across multiple platforms

Active Production Environments:
1. Droplet (ho-cli-main) - Trading + orchestration
2. GitHub Actions - Automation workflows
3. Anthropic - AI inference
4. External APIs - Polymarket, blockchain, etc.
```

### True Dev Environment (Doesn't Exist Yet)

```
What a dev environment would be:
├── Separate droplet or local machine
├── dry_run: true in config
├── Mock APIs instead of real Polymarket
├── Separate GitHub repo or branch protection
├── Test workflows that don't affect production
├── No real money
├── Safe to break things
└── Changes tested before going to prod

Status: NOT IMPLEMENTED
You're developing directly in prod across 4 platforms
```

---

## SUMMARY: COMPLETE PRODUCTION INFRASTRUCTURE

### 1. ON HO-CLI-MAIN DROPLET

**Always Running:**
1. **MONEY_PRINTER.py** - Live trading (307% CPU)
2. **backend_loop.py** - Every 5 min orchestration
3. **sshd** - Your SSH connection
4. **System services** - Linux OS

**When You Use Claude Code:**
5. **Claude Code CLI** - Node.js process
6. **MCP Servers** - GitHub, Playwright tools
7. **All tool executions** - Bash, Read, Write, Grep, etc.

**All File Operations:**
8. **Reading/writing code files**
9. **Reading/writing state files**
10. **Appending to logs**
11. **Git operations** (commits trigger GitHub Actions)

### 2. ON GITHUB'S INFRASTRUCTURE

**GitHub Actions Workflows (Production Automation):**
1. **agent-coordination-notify** - Monitors agent messages, creates issues
2. **auto-merge** - Auto-merges PRs from trusted sources
3. **ai-intake** - Handles AI intake processes

**Repository Operations:**
4. **Issue tracking** - Agent coordination hub
5. **PR management** - Automated merging
6. **Code hosting** - Source of truth

### 3. ON ANTHROPIC SERVERS

**Claude AI Processing:**
1. **Model inference** - All thinking happens here
2. **Tool decision making** - Which tools to call
3. **Response generation** - Your conversational AI

### 4. ON EXTERNAL APIS

**Live Production Services:**
1. **Polymarket API** - Order placement, trading
2. **GitHub API** - Repo operations (from droplet + workflows)
3. **Blockchain RPC** - Wallet operations, transactions
4. **DNS, CDNs, etc.** - Internet infrastructure

---

## RESOURCE UTILIZATION

### Current (Development + Trading)

```
CPU: ~330% of 800% available (41% utilization)
RAM: ~950MB of 16GB available (6% utilization)
Storage: 142GB used of 310GB (46% utilization)
Network: 5-15 Mbps of 1000 Mbps (1-2% utilization)
```

**Conclusion:** Droplet is UNDER-utilized for current workload

### Production (When Fully Operational)

```
From production_infrastructure_requirements.md:
CPU: Would need 100-200 cores (1M orders/sec)
RAM: Would need 50-100 GB (63-wallet fleet)
Storage: Would need 10-20 TB (with log rotation)
Network: Would need 20-40 Gbps (order traffic)
```

**Conclusion:** Current droplet insufficient for full production scale

---

**Master:** Yair Siegel
**Location:** ho-cli-main (165.22.176.190)
**Session:** PRODUCTION (development in prod)
**Date:** December 5, 2025
