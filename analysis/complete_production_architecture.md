# COMPLETE PRODUCTION ARCHITECTURE
## Full Infrastructure Blueprint for Navigation

**Date:** December 5, 2025
**Status:** Active Production Across 4 Environments

---

## VISUAL ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PRODUCTION INFRASTRUCTURE                        │
│                    (4 Environments, All Live)                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 1. DROPLET INFRASTRUCTURE (DigitalOcean)                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ ho-cli-main (165.22.176.190) - PRIMARY PRODUCTION          │   │
│  │ 8 vCPU, 16GB RAM, 310GB SSD                                 │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │ RUNNING PROCESSES:                                          │   │
│  │  • MONEY_PRINTER.py         (307% CPU) - LIVE TRADING       │   │
│  │  • backend_loop.py          (<10% CPU) - Orchestration      │   │
│  │  • Claude Code CLI          (<5% CPU)  - This Session       │   │
│  │  • MCP Servers (child):                                     │   │
│  │    - mcp-github             Trading with real money         │   │
│  │    - mcp-playwright                                         │   │
│  │  • sshd                     (SSH from phone)                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│         │                                                           │
│         │ File Operations                                           │
│         ↓                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ FILE SYSTEM:                                                │   │
│  │  /root/hands-off-engine/                                    │   │
│  │    ├── state/              (12KB-8KB JSON files)            │   │
│  │    ├── logs/               (450MB+ log files)               │   │
│  │    ├── integrafix/         (15MB code)                      │   │
│  │    ├── autonomous/         (8MB code)                       │   │
│  │    └── .git/               (Git operations)                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  IDLE DROPLETS (8 droplets, $28/month wasted):                     │
│  • pm-helper (138.68.103.156) - 4 vCPU, 8GB RAM                    │
│  • ho-compute-2 (159.203.184.188) - 8 vCPU, 16GB RAM               │
│  • ho-compute-2 (142.93.63.109) - 8 vCPU, 16GB RAM                 │
│  • ho-scale-1764543864 (162.243.175.211) - 8 vCPU, 16GB RAM        │
│  • + 4 more                                                         │
│                                                                     │
│  COST: $72/month total ($8 active, $64 idle/wasted)                │
└─────────────────────────────────────────────────────────────────────┘
                         │
                         │ Git Push/Pull
                         │ Triggers Workflows
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 2. GITHUB INFRASTRUCTURE (GitHub.com)                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ REPOSITORY: hands-off-engine                                │   │
│  │  • 182 branches (unmerged)                                  │   │
│  │  • 438 files                                                │   │
│  │  • Active development on: local-sync                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│         │                                                           │
│         │ Triggers on Push/PR/Workflow Dispatch                    │
│         ↓                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ GITHUB ACTIONS (Production Automation)                      │   │
│  │ Runs on: ubuntu-latest (GitHub's runners)                   │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │ WORKFLOWS:                                                  │   │
│  │                                                              │   │
│  │ 1. agent-coordination-notify.yml                            │   │
│  │    Trigger: Push to ai/coordination/messages.jsonl          │   │
│  │    Action: Creates GitHub issues for urgent messages        │   │
│  │    Status: ACTIVE (5 runs/24h, some failing)                │   │
│  │                                                              │   │
│  │ 2. auto-merge.yml                                           │   │
│  │    Trigger: PR opened/synced, checks completed              │   │
│  │    Action: Auto-merges PRs from Copilot/trusted bots        │   │
│  │    Status: ACTIVE (zero-touch repo management)              │   │
│  │                                                              │   │
│  │ 3. ai-intake.yml                                            │   │
│  │    Trigger: Various                                         │   │
│  │    Action: Handles AI intake processes                      │   │
│  │    Status: ACTIVE                                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│         │                                                           │
│         │ Creates Issues, Merges PRs, Repository Dispatch           │
│         ↓                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ REPOSITORY OPERATIONS:                                      │   │
│  │  • Issue tracking (agent coordination hub)                  │   │
│  │  • PR management (automated merging)                        │   │
│  │  • Code hosting (source of truth)                           │   │
│  │  • Workflow artifacts                                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  COST: Free (public repo)                                           │
└─────────────────────────────────────────────────────────────────────┘
                         │
                         │ API Calls from Droplet & Workflows
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 3. ANTHROPIC INFRASTRUCTURE (Anthropic's Servers)                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ CLAUDE AI INFERENCE                                         │   │
│  │ Model: claude-sonnet-4-5-20250929                           │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │ PROCESSING:                                                 │   │
│  │  • Reads your messages from Claude Code CLI                 │   │
│  │  • Processes instructions and context                       │   │
│  │  • Generates responses                                      │   │
│  │  • Decides which tools to call                              │   │
│  │  • All "thinking" happens here                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│         │                                                           │
│         │ Tool Execution Requests                                  │
│         ↓                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ TOOL DISPATCHER:                                            │   │
│  │  Sends tool calls back to:                                  │   │
│  │   → Droplet (Bash, Read, Write, Grep, Glob, MCP tools)      │   │
│  │   → Returns results to model                                │   │
│  │   → Model processes and responds                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  COST: Pay-per-token (API usage)                                    │
└─────────────────────────────────────────────────────────────────────┘
                         │
                         │ API Calls from Droplet
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 4. EXTERNAL API SERVICES                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ POLYMARKET API (polymarket.com)                              │  │
│  │  Called from: MONEY_PRINTER.py on droplet                    │  │
│  │  Operations:                                                 │  │
│  │   • Order placement (LIVE trades with real $$$)             │  │
│  │   • Market data fetching                                     │  │
│  │   • Position queries                                         │  │
│  │   • Trade execution                                          │  │
│  │  Status: ACTIVE (307% CPU on droplet)                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ GITHUB API (api.github.com)                                  │  │
│  │  Called from: Droplet (mcp-github) + GitHub Actions          │  │
│  │  Operations:                                                 │  │
│  │   • Issue creation/updates                                   │  │
│  │   • PR creation/merging                                      │  │
│  │   • Code searches                                            │  │
│  │   • Repository dispatch events                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ BLOCKCHAIN RPC (Polygon Network)                             │  │
│  │  Called from: Trading system on droplet                      │  │
│  │  Operations:                                                 │  │
│  │   • Wallet queries (0xB314...A761b)                          │  │
│  │   • Transaction submission                                   │  │
│  │   • Balance checks                                           │  │
│  │   • Smart contract interactions                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ OTHER SERVICES                                               │  │
│  │   • DNS resolution                                           │  │
│  │   • CDNs (content delivery)                                  │  │
│  │   • PyPI / npm registry (package downloads)                  │  │
│  │   • Web pages (via playwright browser)                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  COST: Various (mostly usage-based or free)                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## DATA FLOW EXAMPLES

### Example 1: You Send a Message to Claude

```
[Phone]
   ↓ (SSH connection)
[Droplet: Claude Code CLI]
   ↓ (HTTPS API call)
[Anthropic: Claude AI]
   ↓ (Processes message, decides to call Read tool)
[Anthropic → Droplet: Read file command]
   ↓
[Droplet: Executes Read tool on local filesystem]
   ↓ (Sends file contents back)
[Anthropic: Receives results, formats response]
   ↓
[Droplet: Claude Code CLI displays response]
   ↓
[Phone: You see the response]
```

### Example 2: MONEY_PRINTER Places a Trade

```
[Droplet: MONEY_PRINTER.py]
   ↓ (Calculates opportunity)
[Droplet: Generates order]
   ↓ (HTTPS API call)
[Polymarket: Receives order, matches on exchange]
   ↓ (Confirmation response)
[Droplet: MONEY_PRINTER receives confirmation]
   ↓ (Writes to disk)
[Droplet: state/money_printer.json updated]
[Droplet: logs/executions.jsonl appended]
```

### Example 3: Git Commit Triggers Workflow

```
[Droplet: You run `git commit` via Claude Code CLI]
   ↓ (Git push)
[GitHub: Repository receives commit]
   ↓ (Checks for workflow triggers)
[GitHub: Detects ai/coordination/messages.jsonl changed]
   ↓ (Triggers agent-coordination-notify.yml)
[GitHub Actions: Spins up ubuntu-latest runner]
   ↓ (Checks out code, reads messages.jsonl)
[GitHub Actions: Checks for urgent messages]
   ↓ (Creates GitHub issue via API)
[GitHub: Issue created in repository]
   ↓ (Sends repository_dispatch event)
[GitHub: Notifies other systems/agents]
```

### Example 4: Claude Creates GitHub Issue via MCP

```
[Phone: You ask Claude to create an issue]
   ↓
[Anthropic: Claude decides to use mcp-github tool]
   ↓ (Tool call sent to droplet)
[Droplet: Claude Code CLI receives tool call]
   ↓ (Forwards to MCP server)
[Droplet: mcp-github process receives request]
   ↓ (Makes HTTPS API call)
[GitHub API: Receives issue creation request]
   ↓ (Creates issue in repo)
[GitHub: Issue created, returns URL]
   ↓ (Response chain)
[Droplet: mcp-github] → [CLI] → [Anthropic] → [Phone]
```

---

## RESOURCE BREAKDOWN BY ENVIRONMENT

### 1. Droplet Resources (ho-cli-main)

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
AVAILABLE               470%     15GB      310GB      990 Mbps
UTILIZATION             41%      6%        46%        1-2%
```

### 2. GitHub Actions Resources

```
Workflow Runs:          ~5 runs/24 hours
Runner Type:            ubuntu-latest (2 vCPU, 7GB RAM)
Duration:               ~30 seconds - 2 minutes per run
Cost:                   $0 (free for public repos)
Status:                 Some failing (needs attention)
```

### 3. Anthropic Resources

```
Model:                  claude-sonnet-4-5-20250929
Requests:               ~10-50 per Claude Code session
Tokens per request:     Variable (500-4000 input, 200-2000 output)
Cost:                   Pay-per-token (API usage billing)
Latency:                ~500ms - 2000ms per response
```

### 4. External API Resources

```
Polymarket API:         ~1-10 calls/minute (trading)
GitHub API:             ~5-20 calls/hour (from droplet + workflows)
Blockchain RPC:         ~1-5 calls/minute (wallet operations)
Other Services:         Variable (DNS, package downloads, etc.)
```

---

## PRODUCTION ENVIRONMENT STATUS

### Current State: LIVE PRODUCTION

```
Environment              Status    Risk Level    Notes
────────────────────────────────────────────────────────────────
Droplet (ho-cli-main)    LIVE      HIGH          Trading with real money
GitHub Actions           LIVE      MEDIUM        Some workflows failing
Anthropic                LIVE      LOW           External, managed service
External APIs            LIVE      MEDIUM        Polymarket = real money
────────────────────────────────────────────────────────────────

Overall Status:          PRODUCTION (No dev environment)
Risk:                    HIGH (changes affect live system)
Safety Net:              NONE (no rollback, no testing environment)
```

### What "Production" Means Right Now

```
✅ Advantages:
   • Real trading happening (MONEY_PRINTER active)
   • GitHub automation working (agent coordination, auto-merge)
   • Claude AI assistance available (this session)
   • All 4 environments integrated and communicating

⚠️  Risks:
   • No separate dev environment
   • Changes immediately affect live system
   • No testing before deployment
   • Git commits trigger production workflows
   • Code changes affect active trading

🛡️ Mitigations:
   • Manual testing before commits
   • Read-only operations when exploring
   • Careful with file writes
   • Check MONEY_PRINTER status before major changes
   • Use git branches for experimental work
```

---

## NAVIGATION GUIDE

### To Work on Trading System
```
Location:      Droplet (ho-cli-main)
Files:         /root/hands-off-engine/integrafix/
Key Files:     money_printer.py, trading_pipeline.py
State:         /root/hands-off-engine/state/money_printer.json
Logs:          /root/hands-off-engine/logs/executions.jsonl
Caution:       MONEY_PRINTER is running (307% CPU)
```

### To Work on Automation
```
Location:      GitHub Repository
Files:         .github/workflows/*.yml
Key Files:     agent-coordination-notify.yml, auto-merge.yml
Testing:       workflow_dispatch trigger (manual testing)
Caution:       Commits trigger workflows immediately
```

### To Work on Backend Loop
```
Location:      Droplet (ho-cli-main)
Files:         /root/hands-off-engine/autonomous/
Key File:      backend_loop.py (2,936 lines)
Schedule:      Runs every 5 minutes automatically
State:         /root/hands-off-engine/state/circuit_board.json
Logs:          /root/hands-off-engine/logs/hft_economics.jsonl
```

### To Monitor System Health
```
Droplet Status:        ps aux | grep python
Trading Status:        cat state/money_printer.json
Workflow Status:       gh api repos/owner/repo/actions/runs
Logs:                  tail -f logs/executions.jsonl
Resource Usage:        htop or top
```

---

## COST BREAKDOWN

```
Environment              Monthly Cost    Notes
─────────────────────────────────────────────────────────
Droplet (active)         $8/month        ho-cli-main only
Droplets (idle)          $64/month       8 droplets unused (wasted)
GitHub Actions           $0/month        Free for public repos
Anthropic API            Variable        Pay-per-token usage
External APIs            $0-$X/month     Polymarket free, others vary
─────────────────────────────────────────────────────────────
TOTAL                    $72+/month      Could optimize to $8-20/month
```

**Optimization Opportunity:**
- Current: $72/month with $64 wasted on idle droplets
- Option 1: $20/month (use 3 droplets for redundancy, destroy rest)
- Option 2: $16/month (use 2 droplets, destroy rest)

---

## NEXT STEPS

### Immediate (System Understanding)
1. ✅ Understand complete infrastructure (this document)
2. ⏸️ Decide on infrastructure optimization (see: infrastructure_options_comparison.md)
3. ⏸️ Fix failing GitHub Actions workflows
4. ⏸️ Monitor MONEY_PRINTER performance

### Short-term (Infrastructure)
1. Choose infrastructure option (1-5 from comparison doc)
2. Deploy redundancy if needed
3. Destroy idle droplets (save $64/month)
4. Setup monitoring for all 4 environments

### Long-term (Scaling)
1. Create separate dev environment
2. Scale infrastructure based on revenue
3. Add more providers for redundancy (Oracle, Hetzner)
4. Implement proper dev/staging/prod separation

---

**Master:** Yair Siegel
**Location:** ho-cli-main (165.22.176.190) via SSH from phone
**Session:** PRODUCTION (4 environments active)
**Date:** December 5, 2025

**Status:** Complete infrastructure blueprint for navigation
