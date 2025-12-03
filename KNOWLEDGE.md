# Hands-Off Engine - Complete Knowledge Base
## Autonomous Income Generation System for Yair Siegel

---

# TABLE OF CONTENTS

1. [System Overview](#1-system-overview)
2. [Core Philosophy](#2-core-philosophy)
3. [Architecture Layers](#3-architecture-layers)
4. [Autonomous Module Catalog](#4-autonomous-module-catalog)
5. [The Evolution Engine (Brain)](#5-the-evolution-engine-brain)
6. [Process Endpoints (Router)](#6-process-endpoints-router)
7. [Actuators (Hands)](#7-actuators-hands)
8. [Trading Infrastructure](#8-trading-infrastructure)
9. [Infrastructure Management](#9-infrastructure-management)
10. [Hardware Monitoring](#10-hardware-monitoring)
11. [AI & Intelligence Systems](#11-ai--intelligence-systems)
12. [Financial Tracking](#12-financial-tracking)
13. [State Management](#13-state-management)
14. [External Integrations](#14-external-integrations)
15. [Income Generation Paths](#15-income-generation-paths)
16. [Self-Healing & Maintenance](#16-self-healing--maintenance)
17. [Security & Protection](#17-security--protection)
18. [Executor Framework](#18-executor-framework)
19. [Mathematical Infrastructure](#19-mathematical-infrastructure)
20. [Best Practices & Patterns](#20-best-practices--patterns)

---

# 1. SYSTEM OVERVIEW

## What is Hands-Off Engine?

The Hands-Off Engine is a **fully autonomous income generation system** designed to operate with minimal human intervention. It combines:

- **Prediction Market Trading** (Polymarket)
- **Cloud Infrastructure Management** (DigitalOcean)
- **AI-Driven Decision Making**
- **Self-Healing Capabilities**
- **Continuous Self-Improvement**

## Core Mission

```
ALWAYS OBJECTIVES:
1. Generate income for Yair Siegel
2. Maintain system health and uptime
3. Convert visitors to paying customers
4. Take action over analysis
5. Improve continuously
6. Reduce costs where possible
7. Find and help ONE person who needs us
```

## System Statistics

| Metric | Value |
|--------|-------|
| Autonomous Modules | 89 |
| Lines of Code | ~72,000+ |
| State Files | 169 |
| Active Systems | 16+ |
| Cron Jobs | 18 |
| External APIs | 4+ |

## Current State

```json
{
  "mode": "LIVE_READY",
  "financial": {
    "liquid": "$7.99",
    "positions": "$98.05",
    "total": "$106.04"
  },
  "infrastructure": {
    "droplets": 9,
    "disk_available": "303G",
    "memory_available": "7.9Gi"
  }
}
```

---

# 2. CORE PHILOSOPHY

## Autonomous Operation

The system is designed around these principles:

### 1. Zero Human Intervention
```
Normal operations: NEVER require user input
Business decisions: Use approval queue for risky items
Emergency handling: Self-heal first, notify if critical
```

### 2. Action Over Analysis
```
Decision Loop:
  gather_intelligence → decide_action → execute → capture_feedback → loop

Rule: 80% action, 20% analysis
Anti-pattern: Analysis paralysis
```

### 3. Continuous Evolution
```
Self-Improvement:
  - Watch system state
  - Identify improvements
  - Implement changes
  - Measure results
  - Loop forever
```

### 4. Multi-Agent Friendly
```
Supported Agents:
  - Claude Code CLI
  - ChatGPT
  - Aider
  - GitHub Copilot
  - Custom AI agents
```

## Design Patterns

### The OODA Loop
```
Observe → Orient → Decide → Act → Repeat

Implemented as:
  Reality Feedback → Intelligence Gathering → Evolution Engine → Actuators
```

### Defense in Depth
```
Layer 1: Trading Safeguards (never lose trading capability)
Layer 2: Infrastructure Protection (maintain servers)
Layer 3: Financial Gates (cost controls)
Layer 4: Self-Healing (auto-fix issues)
```

---

# 3. ARCHITECTURE LAYERS

## Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      BRAIN LAYER                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  evolution_engine.py - Decides what to do next          │ │
│  │  Inputs: war_room, helicopter, stage, gallery, reality  │ │
│  │  Outputs: decisions, actions, improvements              │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      ROUTER LAYER                            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  process_endpoints.py - Routes decisions to processes   │ │
│  │  Maintains: Endpoint registry, process cycles           │ │
│  │  Calls: Scripts, actuators, subprocess commands         │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      HANDS LAYER                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  actuators.py - Real-world action execution             │ │
│  │  Capabilities: Telegram, Polymarket, Landing Pages      │ │
│  │  External: api.telegram.org, clob.polymarket.com        │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
1. Intelligence Gathering
   ├── War Room (preparations)
   ├── Helicopter (overview)
   ├── Stage (self-reflection)
   ├── Gallery (perspectives)
   └── Reality (ground truth)
          ↓
2. Evolution Engine
   ├── Analyze inputs
   ├── Compare to objectives
   ├── Decide next action
   └── Generate decision
          ↓
3. Process Router
   ├── Select endpoint
   ├── Prepare execution
   └── Dispatch action
          ↓
4. Actuators
   ├── Execute real-world action
   ├── Capture result
   └── Write feedback
          ↓
5. Feedback Loop
   └── Results feed back to intelligence gathering
```

## Module Categories

| Category | Count | Purpose |
|----------|-------|---------|
| autonomous/ | 89 | Core autonomous systems |
| executor/ | 30+ | Execution and trading |
| ai/ | 17 | AI and intelligence |
| infrastructure/ | 9 | Cloud management |
| hardware/ | 10 | System monitoring |
| trading/ | 6 | Trading logic |
| finance/ | 9 | Cost tracking |
| scripts/ | 40+ | Automation scripts |

---

# 4. AUTONOMOUS MODULE CATALOG

## Core Control Systems

### orchestrator.py
**UnifiedAutonomousSystem** - The master controller
```python
Functions:
- Monitors hardware health continuously
- Provisions/upgrades infrastructure automatically
- Integrates with approval queue
- Protects trading at all costs

Intervals:
- Normal: 60 seconds
- Degraded: 30 seconds
- Critical: 15 seconds
```

### evolution_engine.py
**The Brain** - Decision maker
```python
Watches:
- war_room, helicopter, stage, gallery, reality

Decides:
- Next action based on objectives
- Triggers capabilities
- Implements improvements
```

### master_orchestrator.py
High-level coordination across all systems

### master_controller.py
Central control point for system operations

## Income Generation

### active_pursuit.py
Proactive outreach to find customers
```python
Functions:
- Generate outreach templates
- Find potential customers
- Execute outreach campaigns
- Track responses
```

### conversion_optimizer.py
Optimize visitor-to-customer conversion
```python
Experiments:
- Pricing variations
- Offer changes
- Headline testing
- CTA optimization
```

### income_accelerator.py
Maximize income generation speed

### revenue_tracker.py
Track all revenue streams

### zero_capital_income.py
Income strategies requiring zero capital

### zero_capital_extraction.py
Extract value from existing resources

## Trading Systems

### polymarket_live.py
Live Polymarket trading integration
```python
Capabilities:
- Check balances
- Execute trades
- Monitor positions
- Generate signals
```

### trade_executor.py
Execute trading decisions safely

### arbitrage_scanner.py
Scan for arbitrage opportunities

### sharp_wallet_tracker.py
Track successful trader wallets

### signal_generator.py
Generate trading signals from analysis

## Self-Awareness Systems

### self_awareness.py
System understands itself

### self_conversation.py
System reflects on itself (stage)

### peanut_gallery.py
Multiple perspectives commenting (gallery)
```python
Observers:
- The Skeptic: "Does this actually work?"
- The Optimist: "I love where this is going!"
- The Pragmatist: "Less talk, more action."
- The Contrarian: "What if we did the opposite?"
- The Historian: "We tried this before..."
- The Numbers Person: "Where's the data?"
```

### conceptual_awareness.py
Understand abstract concepts

### architecture_awareness.py
Understand system architecture

### architecture_session.py
Session-based architecture exploration

## Health & Maintenance

### self_healer.py
Automatically fix detected issues

### system_doctor.py
Comprehensive health examination
```python
Checks:
- Processes, state files, actuators
- Finances, outreach, evolution
- Disk, memory, network
- Endpoints, cron, logs, git
- Python, env, trading
```

### health_diagnostics.py
Detailed health diagnostics

### glitch_detector.py
Detect system anomalies

### harm_prevention.py
Prevent harmful actions

### infra_protection.py
Protect infrastructure

### self_preservation.py
System self-preservation logic

## Intelligence Gathering

### helicopter.py
High-level system overview broadcasts

### reality_feedback.py
Get ground truth from external world

### corporate_meeting.py
War room - preparation and planning

### feedback_loop.py
Capture and process feedback

### probability_calibrator.py
Calibrate probability estimates

## Infrastructure Management

### infra_manager.py
Manage infrastructure resources

### proactive_infra.py
Proactively provision resources

### scaling_engine.py
Auto-scale based on demand

### resource_tracker.py
Track resource usage

## Capital Management

### capital_tracker.py
Track capital allocation

### capital_accelerator.py
Accelerate capital growth

### capital_vessel.py
Capital container management

### capital_state_manager.py
Manage capital state

### compound_tracker.py
Track compound growth

### compound_growth.py
Compound growth engine

## Execution Systems

### aggressive_executor.py
Aggressive action execution

### concrete_executor.py
Concrete action implementation

### web_executor.py
Web-based executions

### web_agent.py
Web interaction agent

### api_automation.py
API automation tasks

## Monitoring & Reporting

### system_dashboard.py
System status dashboard

### outcome_recorder.py
Record outcomes

### scribes.py
System event logging

### meta_metrics.py
Meta-level metrics

## Optimization

### claude_optimizer.py
Optimize Claude AI usage

### improvement_loop.py
Continuous improvement

### skill_growth_tracker.py
Track skill growth

### learning_engine.py
Learn from outcomes

## Special Systems

### dimensional_continuum.py
Multi-dimensional analysis

### optimal_singularity.py
Convergence to optimal state

### singularity_trigger.py
Trigger system evolution

### time_collapse.py
Time compression execution

### instant_manifest.py
Instant manifestation

### moonshot_loop.py
High-risk, high-reward attempts

### fuel_ingenuity.py
Generate creative solutions

### escape_velocity_tracker.py
Track progress to sustainability

### dense_ai.py
Dense AI operations

### advisor.py
AI advisory functions

### battery_slot.py
Resource reservation

### power_plant.py
Energy/resource management

## Security

### security_layer.py
Security operations

### threat_analysis.py
Analyze potential threats

### credential_monitor.py
Monitor credentials

### api_quota_monitor.py
Monitor API quotas

## Integration

### mega_integration.py
Mega integration layer

### self_integrator.py
Self-integration system

### state_sync.py
Synchronize state

### system_coordinator.py
Coordinate systems

---

# 5. THE EVOLUTION ENGINE (BRAIN)

## Overview

The Evolution Engine is the **decision-making brain** of the system. It:

1. Watches all intelligence inputs
2. Compares current state to objectives
3. Decides the next action
4. Triggers capabilities
5. Evolves the system

## Input Sources

```python
INPUTS = {
    "war_room": "state/war_room.jsonl",
    "contingencies": "state/contingency_plans.json",
    "helicopter": "state/helicopter_state.json",
    "reality": "state/reality_feedback.json",
    "stage": "state/self_conversation.jsonl",
    "gallery": "state/peanut_gallery.jsonl",
    "pursuit": "state/active_pursuit.json",
    "conversion": "state/conversion_optimizer.json",
    "doctor": "state/doctor_state.json",
    "diagnosis": "state/diagnosis_log.jsonl",
}
```

## Capabilities

```python
CAPABILITIES = {
    "outreach": {
        "name": "Active Outreach",
        "script": "autonomous/active_pursuit.py",
        "purpose": "Reach out to potential customers"
    },
    "conversion": {
        "name": "Conversion Optimization",
        "script": "autonomous/conversion_optimizer.py",
        "purpose": "Optimize conversion rates"
    },
    "trading": {
        "name": "Trading Execution",
        "actuator": "polymarket",
        "purpose": "Execute prediction market trades"
    },
    "reality_check": {
        "name": "Reality Feedback",
        "script": "autonomous/reality_feedback.py",
        "purpose": "Get ground truth"
    },
    # ... more capabilities
}
```

## Decision Cycle

```
1. Gather Intelligence
   - Read all input files
   - Extract recent entries
   - Synthesize insights

2. Evaluate State
   - Compare to objectives
   - Identify gaps
   - Prioritize needs

3. Decide Action
   - Select best capability
   - Prepare parameters
   - Consider constraints

4. Execute
   - Trigger capability
   - Monitor execution
   - Capture results

5. Log & Learn
   - Record decision
   - Capture outcome
   - Feed back to inputs
```

## State Files

| File | Purpose |
|------|---------|
| evolution_state.json | Current engine state |
| evolution_log.jsonl | Execution history |
| evolution_decisions.jsonl | Decision log |

---

# 6. PROCESS ENDPOINTS (ROUTER)

## Overview

Process Endpoints is the **routing layer** that:

1. Maintains registry of all endpoints
2. Routes decisions to appropriate handlers
3. Manages process lifecycle
4. Captures feedback from executions

## Endpoint Registry

```python
ENDPOINT_REGISTRY = {
    "income_generation": {
        "outreach": "autonomous/active_pursuit.py",
        "conversion": "autonomous/conversion_optimizer.py",
        "trading": "polymarket_actuator"
    },
    "monitoring": {
        "reality_check": "autonomous/reality_feedback.py",
        "helicopter": "autonomous/helicopter.py",
        "self_heal": "scripts/self_healing_agent.py",
        "doctor": "autonomous/system_doctor.py"
    },
    "preparation": {
        "war_room": "autonomous/corporate_meeting.py",
        "coordination": "scripts/coordination_agent.py"
    },
    "dialogue": {
        "stage_conversation": "autonomous/self_conversation.py",
        "gallery": "autonomous/peanut_gallery.py"
    }
}
```

## Process Cycling

```python
class ProcessCycler:
    """Cycles through processes in priority order."""

    def cycle_once(self):
        """Execute one cycle through all processes."""
        for category in self.priority_order:
            for endpoint in category.endpoints:
                result = self.execute_endpoint(endpoint)
                self.record_cycle(endpoint, result)
```

## Feedback Capture

Each endpoint writes feedback to its designated state file:

```
Endpoint → Execution → Result → Feedback File → Evolution Engine
```

---

# 7. ACTUATORS (HANDS)

## Overview

Actuators are the **hands** that execute real-world actions.

## Available Actuators

### TelegramActuator
```python
class TelegramActuator:
    """Send notifications to Telegram."""

    def send(self, message: str) -> bool:
        """Send message to owner's Telegram."""
        # Uses Bot API
        # Returns success/failure
```

### PolymarketActuator
```python
class PolymarketActuator:
    """Execute trades on Polymarket."""

    def get_balance(self) -> dict:
        """Get current USDC balance."""

    def execute_trade(self, market_id, side, amount, price):
        """Execute a trade (through safeguards)."""

    def get_positions(self) -> list:
        """Get current positions."""
```

### ActuatorHub
```python
class ActuatorHub:
    """Central hub for all actuators."""

    def notify(self, message: str) -> bool:
        """Send notification via Telegram."""

    def get_trading_status(self) -> dict:
        """Get Polymarket status."""

    def execute_trade(self, params: dict) -> dict:
        """Execute trade through safeguards."""
```

## Safety Rules

```python
ACTUATOR_SAFETY = {
    "telegram": {
        "rate_limit": "10 messages/minute",
        "max_length": 4096
    },
    "polymarket": {
        "max_trade_size": "50 USDC",
        "require_safeguards": True,
        "dry_run_first": True
    }
}
```

---

# 8. TRADING INFRASTRUCTURE

## Polymarket Integration

### Architecture

```
┌──────────────────────────────────────────────────────┐
│                 TRADING STACK                         │
├──────────────────────────────────────────────────────┤
│  Signal Generation (trading/signal_generator.py)     │
│         ↓                                            │
│  Trading Brain (trading/trading_brain.py)            │
│         ↓                                            │
│  Executor Pipeline (executor/)                       │
│         ↓                                            │
│  Safeguards (executor/trading_safeguards.py)         │
│         ↓                                            │
│  Polymarket API (py_clob_client)                     │
└──────────────────────────────────────────────────────┘
```

### Core Components

**Signal Generator**
```python
- Analyze market opportunities
- Generate trading signals
- Score by confidence/edge
- Prioritize by expected value
```

**Trading Brain**
```python
- Process signals
- Apply risk limits
- Size positions
- Generate orders
```

**Trading Safeguards**
```python
- Maximum position size
- Daily loss limits
- Liquidity checks
- Price validation
```

### Executor Modules

| Module | Purpose |
|--------|---------|
| polymarket_api.py | Direct API access |
| polymarket_client.py | High-level client |
| polymarket_full_stack.py | Complete stack |
| polymarket_wallet_factory.py | Wallet management |
| rapid_order_manager.py | Fast order execution |
| parallel_order_orchestrator.py | Parallel orders |
| hft_order_cannon.py | High-frequency trading |
| hft_order_presigner.py | Pre-sign orders |
| hft_million_coordinator.py | Scale coordination |
| fleet_commander.py | Fleet management |
| gasless_wallet_manager.py | Gasless operations |
| multi_wallet_manager.py | Multi-wallet |
| wallet_flow_coordinator.py | Fund flows |

### Mathematical Support

```python
from executor.polymarket import poly

# Quick status
poly.quick_status()

# Check arbitrage
poly.check_arbitrage(0.60, 0.38)

# Optimal bet sizing
poly.optimal_bet_size(0.65, 0.55, bankroll=1000)
```

---

# 9. INFRASTRUCTURE MANAGEMENT

## Cloud Infrastructure

### Auto-Provisioner
```python
class AutoProvisioner:
    """Automatically provision cloud resources."""

    def provision_if_needed(self):
        """Check health, provision if degraded."""

    def scale_up(self, reason: str):
        """Add more resources."""

    def scale_down(self):
        """Remove unused resources."""
```

### Autonomous Infra Manager
```python
class AutonomousInfraManager:
    """Manage infrastructure autonomously."""

    def health_check(self) -> HealthStatus:
        """Check all infrastructure health."""

    def auto_heal(self, issue: Issue):
        """Automatically fix issues."""

    def optimize_costs(self):
        """Optimize infrastructure costs."""
```

### Cloud Providers
```python
class CloudProvider:
    """Abstract cloud provider interface."""

    Supported:
    - DigitalOcean (primary)
    - AWS (future)
    - GCP (future)
```

## DigitalOcean Integration

### Active Resources
- 9 Droplets
- Multiple sizes (s-1vcpu-1gb to larger)
- Automatic scaling
- Region: NYC/SF

### Management
```python
# Via doctl CLI
doctl compute droplet list
doctl compute droplet create ...
doctl compute droplet delete ...
```

## Resilience

### Self-Healing
```python
class SelfHeal:
    """Automatically recover from failures."""

    def detect_issues(self):
        """Scan for problems."""

    def fix_issue(self, issue):
        """Apply automatic fix."""

    def escalate(self, issue):
        """Escalate if can't fix."""
```

### Backup Management
```python
class BackupManager:
    """Manage system backups."""

    def backup_state(self):
        """Backup all state files."""

    def backup_code(self):
        """Backup codebase."""

    def restore(self, backup_id):
        """Restore from backup."""
```

---

# 10. HARDWARE MONITORING

## Hardware Stack

```
┌─────────────────────────────────────────┐
│         HARDWARE MONITORING              │
├─────────────────────────────────────────┤
│  HardwareCollector - Gather metrics     │
│         ↓                               │
│  HardwareAnalyzer - Analyze data        │
│         ↓                               │
│  HardwareKernel - Core logic            │
│         ↓                               │
│  HardwareDecisionEngine - Decide action │
│         ↓                               │
│  TradingProtectionManager - Safety      │
└─────────────────────────────────────────┘
```

## Modules

### HardwareCollector
```python
class HardwareCollector:
    """Collect hardware metrics."""

    def collect_cpu(self) -> dict
    def collect_memory(self) -> dict
    def collect_disk(self) -> dict
    def collect_network(self) -> dict
```

### HardwareAnalyzer
```python
class HardwareAnalyzer:
    """Analyze hardware metrics."""

    def analyze_trends(self, metrics: list) -> dict
    def predict_failures(self) -> list
    def recommend_actions(self) -> list
```

### HardwareDecisionEngine
```python
class HardwareDecisionEngine:
    """Make hardware decisions."""

    def should_upgrade(self) -> bool
    def should_scale(self) -> tuple
    def emergency_action(self) -> str
```

### TradingProtectionManager
```python
class TradingProtectionManager:
    """Protect trading at all costs."""

    def is_trading_safe(self) -> bool
    def protect_trading(self):
        """Never compromise trading capability."""
```

## Health Status

```python
class HealthStatus:
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

def quick_health_check() -> HealthStatus:
    """Quick system health check."""
```

---

# 11. AI & INTELLIGENCE SYSTEMS

## AI Module Structure

```
ai/
├── unified_ai.py          # Central AI coordination
├── ho_brain_orchestrator.py # Brain orchestration
├── ho_ai_loop.py          # AI decision loop
├── ho_ai_runner.py        # AI task runner
├── ai_runner.py           # Task execution
├── ai_intake_handler.py   # Task intake
├── approval_queue.py      # Human approval queue
├── ho_policy_agent.py     # Policy decisions
├── ho_policy_brain_v2.py  # Policy brain v2
├── ho_policy_executor.py  # Policy execution
├── ho_consensus_engine.py # Multi-agent consensus
├── ho_action_verifier.py  # Verify actions
├── ho_learning_engine.py  # Learn from outcomes
├── mega_unified_system.py # Mega integration
└── integrate_all.py       # Integration scripts
```

## Key Components

### Unified AI
```python
MASTER = "Yair Siegel"

def get_master() -> str:
    """All systems serve the master."""
    return MASTER
```

### Brain Orchestrator
```python
class BrainOrchestrator:
    """Orchestrate AI brain activities."""

    def think(self, context: dict) -> dict:
        """Think about situation."""

    def decide(self, options: list) -> dict:
        """Decide between options."""

    def act(self, decision: dict) -> dict:
        """Execute decision."""
```

### Approval Queue
```python
class ApprovalQueue:
    """Queue for human approval of risky decisions."""

    def needs_approval(self, action: dict) -> bool:
        """Check if action needs approval."""

    def request_approval(self, action: dict):
        """Request human approval."""

    def check_approved(self, action_id: str) -> bool:
        """Check if approved."""
```

### Consensus Engine
```python
class ConsensusEngine:
    """Multi-agent consensus building."""

    def gather_opinions(self, question: str) -> list:
        """Gather agent opinions."""

    def find_consensus(self, opinions: list) -> dict:
        """Find consensus position."""
```

---

# 12. FINANCIAL TRACKING

## Finance Module

```
finance/
├── action_costs.py         # Cost per action
├── ai_cost_optimizer.py    # Optimize AI costs
├── autonomous_cost_gate.py # Gate expensive actions
├── cc_optimizer.py         # Credit card optimization
├── cost_predictor.py       # Predict costs
├── cost_tracker.py         # Track all costs
├── dashboard.py            # Financial dashboard
├── provider_intelligence.py # Provider analysis
└── refresh_balances.py     # Refresh balance data
```

## Cost Tracking

```python
class CostTracker:
    """Track all system costs."""

    def record_cost(self, category: str, amount: float):
        """Record a cost."""

    def get_daily_costs(self) -> dict:
        """Get costs for today."""

    def get_burn_rate(self) -> float:
        """Calculate burn rate."""
```

## Autonomous Cost Gate

```python
class AutonomousCostGate:
    """Gate expensive operations."""

    def can_spend(self, amount: float) -> bool:
        """Check if can spend amount."""

    def approve_cost(self, amount: float, reason: str):
        """Approve a cost."""

    def get_budget_remaining(self) -> float:
        """Get remaining budget."""
```

## Provider Intelligence

```python
class ProviderIntelligence:
    """Intelligence on providers for cost optimization."""

    def compare_providers(self, service: str) -> list:
        """Compare provider costs."""

    def recommend_provider(self, service: str) -> str:
        """Recommend best provider."""
```

---

# 13. STATE MANAGEMENT

## State Directory Structure

```
state/
├── ABSOLUTE_TRUTH.json       # Core truth
├── CURRENT_TRUTH.json        # Current state
├── SYSTEM_ARCHITECTURE.json  # Architecture
├── UNIFIED_SYSTEM_STATE.json # Unified state
├── evolution_state.json      # Evolution engine
├── actuator_state.json       # Actuator state
├── trading_status.json       # Trading state
├── doctor_state.json         # System health
├── ... (169 total files)
```

## Key State Files

### ABSOLUTE_TRUTH.json
```json
{
  "master": "Yair Siegel",
  "purpose": "Generate income autonomously",
  "core_values": ["action", "income", "health"]
}
```

### CURRENT_TRUTH.json
```json
{
  "financial": {"liquid": 7.99, "positions": 98.05},
  "infrastructure": {"droplets": 9, "cron_jobs": 18},
  "autonomous_systems": {"count": 16, "status": "active"},
  "api_connections": {"polymarket": "LIVE"}
}
```

### evolution_state.json
```json
{
  "cycle_count": 1234,
  "last_action": "outreach",
  "last_result": "success",
  "improvements_made": 45
}
```

## State Patterns

### JSONL for Logs
```
*.jsonl files store append-only event logs
Each line is a JSON object with timestamp
Used for: decisions, cycles, observations
```

### JSON for Current State
```
*.json files store current state
Overwritten on each update
Used for: configuration, status, snapshots
```

## State Synchronization

```python
class StateSync:
    """Synchronize state across systems."""

    def sync_all(self):
        """Sync all state files."""

    def validate_state(self) -> bool:
        """Validate state consistency."""

    def repair_state(self):
        """Repair inconsistent state."""
```

---

# 14. EXTERNAL INTEGRATIONS

## Connected APIs

### Polymarket
```python
Endpoint: clob.polymarket.com
Chain: Polygon (137)
Credentials: .env.polymarket

Capabilities:
- Get markets
- Place orders
- Check positions
- Get balances
```

### Telegram
```python
Endpoint: api.telegram.org
Credentials: /root/hands-off/state/tg/bots/handsoff.env

Capabilities:
- Send notifications
- Receive commands
- Alert on critical events
```

### DigitalOcean
```python
Endpoint: api.digitalocean.com
Credentials: doctl auth

Capabilities:
- Create/delete droplets
- Manage DNS
- Monitor resources
```

### GitHub
```python
Endpoint: api.github.com
Credentials: gh auth

Capabilities:
- Create PRs
- Manage issues
- Monitor repos
```

### Gamma API
```python
Endpoint: gamma-api.polymarket.com

Capabilities:
- Market metadata
- Resolution data
- Historical prices
```

## Landing Pages

### AI Nexus
```
URL: http://138.68.103.156:8081
Purpose: Customer acquisition
Status: Live
```

---

# 15. INCOME GENERATION PATHS

## Active Paths

### 1. Prediction Market Trading
```
Source: Polymarket
Method: Signal-based trading
Edge: Probability calibration, sharp wallet tracking
Current: $98.05 in positions
```

### 2. Active Outreach
```
Source: Direct outreach
Method: Find and help people
Edge: AI-powered personalization
Templates: 11 active
```

### 3. Conversion Optimization
```
Source: Landing pages
Method: A/B testing, offer optimization
Edge: Data-driven iteration
Current: Testing pricing at $199
```

### 4. Service Offering
```
Source: AI services
Method: Leverage system capabilities
Target: Small businesses, individuals
```

### 5. Arbitrage
```
Source: Market inefficiencies
Method: Cross-platform arbitrage
Scanner: autonomous/arbitrage_scanner.py
```

### 6. Compound Growth
```
Source: Reinvested profits
Method: Compound interest
Tracker: autonomous/compound_tracker.py
```

## Zero-Capital Strategies

```python
# From zero_capital_income.py
Strategies:
- Leverage existing resources
- Time arbitrage
- Information asymmetry
- Network effects
```

---

# 16. SELF-HEALING & MAINTENANCE

## Self-Healing System

### System Doctor
```python
class SystemDoctor:
    """Comprehensive health examination."""

    Checks:
    - Processes
    - State files
    - Actuators
    - Finances
    - Outreach
    - Evolution
    - Disk
    - Memory
    - Network
    - Endpoints
    - Cron
    - Logs
    - Git
    - Python
    - Env
    - Trading

    def diagnose(self) -> Diagnosis:
        """Run all diagnostics."""

    def treat(self, diagnosis: Diagnosis):
        """Apply treatment."""
```

### Self Healer
```python
class SelfHealer:
    """Automatically fix issues."""

    def detect(self) -> list:
        """Detect issues."""

    def fix(self, issue: Issue) -> bool:
        """Fix issue automatically."""

    def escalate(self, issue: Issue):
        """Escalate if can't fix."""
```

### Glitch Detector
```python
class GlitchDetector:
    """Detect anomalies and glitches."""

    def scan(self) -> list:
        """Scan for glitches."""

    def analyze(self, glitch: dict):
        """Analyze glitch cause."""
```

## Maintenance Tasks

### Cron Jobs
```
18 scheduled tasks including:
- Health checks
- State sync
- Backup
- Trading monitoring
- Cost tracking
```

### Backup Strategy
```
- State: Every hour
- Code: Daily
- Full: Weekly
- Retention: 30 days
```

---

# 17. SECURITY & PROTECTION

## Security Layers

### Trading Protection
```python
class TradingProtectionManager:
    """Trading capability is NEVER compromised."""

    Priority: ABSOLUTE
    Rule: Protect trading first, everything else second
```

### Infrastructure Protection
```python
class InfraProtection:
    """Protect infrastructure resources."""

    def protect_critical(self):
        """Ensure critical services survive."""
```

### Credential Management
```python
class CredentialMonitor:
    """Monitor and protect credentials."""

    def check_exposure(self):
        """Check for exposed credentials."""

    def rotate_if_needed(self):
        """Rotate compromised credentials."""
```

### Threat Analysis
```python
class ThreatAnalysis:
    """Analyze potential threats."""

    def scan_threats(self) -> list:
        """Scan for threats."""

    def assess_risk(self, threat: dict) -> str:
        """Assess threat risk level."""
```

## Safety Rules

```python
SAFETY_RULES = {
    "max_trade_size": 50,  # USDC
    "max_daily_loss": 100,  # USDC
    "require_safeguards": True,
    "dry_run_new_strategies": True,
    "human_approval_threshold": 50,  # USD
}
```

---

# 18. EXECUTOR FRAMEWORK

## Executor Structure

```
executor/
├── polymarket/          # Polymarket knowledge & trading
│   ├── core.py          # Market mechanics
│   ├── clob.py          # Order book operations
│   ├── orders.py        # Order management
│   ├── strategies.py    # Trading strategies
│   ├── portfolio.py     # Portfolio management
│   ├── risk.py          # Risk management
│   ├── analysis.py      # Market analysis
│   ├── execution.py     # Execution algorithms
│   ├── KNOWLEDGE.md     # Knowledge base
│   └── KNOWLEDGE_ADVANCED.md
├── uma/                 # UMA oracle knowledge
│   ├── KNOWLEDGE.md     # Complete UMA knowledge
│   └── KNOWLEDGE_ADVANCED.md
├── math/                # Mathematical infrastructure
│   ├── number_theory.py
│   ├── abstract_algebra.py
│   ├── geometry.py
│   ├── analysis.py
│   ├── financial.py
│   ├── discrete.py
│   ├── statistics.py
│   └── ml_math.py
└── (trading modules...)
```

## Usage Patterns

### Polymarket
```python
from executor.polymarket import poly

# Status
poly.quick_status()

# Arbitrage check
poly.check_arbitrage(yes_price=0.60, no_price=0.38)

# Optimal sizing
poly.optimal_bet_size(win_prob=0.65, market_price=0.55)

# Analyze opportunity
poly.analyze_opportunity(yes_price=0.55, estimated_prob=0.65)
```

### Math
```python
from executor.math import (
    number_theory, algebra, geometry,
    analysis, financial, discrete,
    statistics, ml
)

# Number theory
number_theory.is_prime(17)
number_theory.gcd(48, 18)

# Financial math
financial.black_scholes_call(S=100, K=100, T=1, r=0.05, sigma=0.2)
financial.kelly_criterion(win_prob=0.6, odds=2.0)
```

---

# 19. MATHEMATICAL INFRASTRUCTURE

## Math Module Catalog

### Number Theory (75 functions)
```
- Primality testing (Miller-Rabin)
- GCD, LCM, modular arithmetic
- Prime factorization
- Euler's totient
- Chinese Remainder Theorem
```

### Abstract Algebra (65 functions)
```
- Group operations
- Ring operations
- Field operations
- Polynomial operations
- Matrix algebra
```

### Geometry (70 functions)
```
- Euclidean geometry
- Vector operations
- Transformations
- Projective geometry
- Differential geometry
```

### Analysis (68 functions)
```
- Calculus (derivatives, integrals)
- Sequences and series
- Complex analysis
- Differential equations
```

### Financial Math (72 functions)
```
- Option pricing (Black-Scholes, Greeks)
- Portfolio theory (Markowitz)
- Risk metrics (VaR, Sharpe)
- Time value of money
```

### Discrete Math (65 functions)
```
- Combinatorics
- Graph theory
- Automata theory
- Set operations
```

### Statistics (70 functions)
```
- Distributions
- Hypothesis testing
- Regression
- Bayesian inference
```

### ML Math (73 functions)
```
- Activation functions
- Loss functions
- Kernels
- Optimizers (Adam, SGD)
- Information theory
- Attention mechanisms
```

---

# 20. BEST PRACTICES & PATTERNS

## Development Patterns

### State Management
```python
# Always use state files
state_path = STATE_DIR / "my_state.json"

# Read state
state = json.loads(state_path.read_text()) if state_path.exists() else {}

# Update state
state["last_run"] = datetime.now().isoformat()

# Write state
state_path.write_text(json.dumps(state, indent=2))
```

### Error Handling
```python
# Always handle errors gracefully
try:
    result = risky_operation()
except Exception as e:
    log_error(e)
    notify_if_critical(e)
    fallback_action()
```

### Logging
```python
# Use JSONL for append-only logs
log_path = STATE_DIR / "my_log.jsonl"
with open(log_path, "a") as f:
    f.write(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "event": "action_completed",
        "result": "success"
    }) + "\n")
```

## Operational Patterns

### Safety First
```
1. Never compromise trading capability
2. Always have fallback
3. Dry run new strategies
4. Human approval for large costs
5. Log everything
```

### Continuous Improvement
```
1. Observe outcomes
2. Analyze what worked
3. Implement improvements
4. Measure results
5. Loop forever
```

### Resource Conservation
```
1. Optimize AI costs
2. Right-size infrastructure
3. Kill unused processes
4. Cache expensive computations
5. Batch operations where possible
```

## Command Reference

### Quick Health Check
```bash
python3 -c "from hardware import quick_health_check; print(quick_health_check())"
```

### View Current State
```bash
cat state/CURRENT_TRUTH.json | python3 -m json.tool
```

### Run Evolution Cycle
```bash
python3 autonomous/evolution_engine.py
```

### Check Trading Status
```bash
PYTHONPATH=/root/hands-off-engine python3 -c "
from executor.polymarket import poly
print(poly.quick_status())
"
```

---

# APPENDIX A: FILE LOCATIONS

## Key Directories

| Path | Purpose |
|------|---------|
| /root/hands-off-engine | Main codebase |
| /root/hands-off-engine/autonomous | 89 autonomous modules |
| /root/hands-off-engine/executor | Execution & trading |
| /root/hands-off-engine/state | 169 state files |
| /root/hands-off-engine/ai | AI systems |
| /root/hands-off-engine/infrastructure | Cloud management |
| /root/hands-off-engine/hardware | System monitoring |
| /root/hands-off-engine/trading | Trading logic |
| /root/hands-off-engine/finance | Cost tracking |
| /root/hands-off-engine/scripts | Automation scripts |

## Configuration Files

| File | Purpose |
|------|---------|
| .env.polymarket | Polymarket credentials |
| .env | General environment |
| config/settings.json | System settings |

---

# APPENDIX B: GLOSSARY

| Term | Definition |
|------|------------|
| Actuator | Component that executes real-world actions |
| Evolution Engine | The brain that decides what to do |
| Process Endpoint | Handler for a specific capability |
| ALWAYS_OBJECTIVES | Unchanging core goals |
| State File | JSON file storing system state |
| Capability | Something the system can do |
| Self-Healing | Automatic issue resolution |
| Trading Safeguards | Protections for trading |
| Approval Queue | Human approval for risky actions |

---

*This knowledge base represents the complete Hands-Off Engine system. The system evolves continuously - state reflects current status at time of reading.*
