# Agent Session Manager

A CLI tool for discovering, creating, and managing agent sessions in the Hands-Off Engine.

## Quick Start

```bash
# List available templates
python -m ai_nexus.session_manager templates

# Get session suggestions based on pending tasks and kernels
python -m ai_nexus.session_manager suggest

# Create a new session
python -m ai_nexus.session_manager create --goal "Analyze risk model" --template risk_analysis

# List existing sessions
python -m ai_nexus.session_manager list

# Get info about a specific session
python -m ai_nexus.session_manager info <conversation_id>
```

## Commands

### `list`
Lists all existing sessions with their status, goal, participants, and bound kernels.

```bash
python -m ai_nexus.session_manager list
python -m ai_nexus.session_manager list --archived  # Include archived sessions
```

### `create`
Creates a new agent session with the specified configuration.

```bash
python -m ai_nexus.session_manager create --goal "Your session goal"
python -m ai_nexus.session_manager create --goal "..." --template risk_analysis
python -m ai_nexus.session_manager create --goal "..." --agents chatgpt,claude_cli --rounds 3
python -m ai_nexus.session_manager create --goal "..." --continuous --max-steps 10
python -m ai_nexus.session_manager create --goal "..." --kernels risk_model_v2,system_health
```

Options:
- `--goal`: Session goal/purpose (required)
- `--agents`: Comma-separated list of agents (default: chatgpt,claude_cli)
- `--rounds`: Number of rounds for burst mode (default: 1)
- `--kernels`: Comma-separated list of kernel IDs to bind
- `--continuous`: Use continuous mode instead of burst mode
- `--max-steps`: Max steps for continuous mode (default: 20)
- `--max-duration`: Max duration in seconds (default: 900)
- `--id`: Custom conversation ID
- `--template`: Template name to use as base configuration

### `suggest`
Suggests new sessions based on:
- Pending tasks in `ai/coordination/status.json`
- Open questions in memory kernels
- System health and optimization opportunities

```bash
python -m ai_nexus.session_manager suggest
```

### `templates`
Lists all available built-in templates.

```bash
python -m ai_nexus.session_manager templates
```

### `info`
Gets detailed information about a specific session.

```bash
python -m ai_nexus.session_manager info 20251127_risk_analysis
```

## Built-in Templates

| Template | Description | Mode | Default Kernels |
|----------|-------------|------|-----------------|
| `risk_analysis` | Analyze and improve risk management | burst | risk_model_v2 |
| `alpha_optimization` | Optimize alpha signals | burst | alpha_polymarket_core |
| `system_architecture` | Discuss architecture changes | burst | system_health |
| `ai_coordination` | Coordinate between AI agents | burst | ai_coordination |
| `general_discussion` | General multi-agent discussion | burst | - |
| `deep_research` | Extended research sessions | continuous | - |

## Session Modes

### Burst Mode
Fixed number of rounds, then stop. Each round consists of each agent speaking once.

### Continuous Mode
Runs until max steps or max duration is reached. Useful for extended research and deep-dive sessions.

## Running a Created Session

After creating a session, the tool outputs a command to run it:

```bash
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id "20251127_risk_analysis" \
    --session-goal "Analyze risk model" \
    --agents chatgpt,claude_cli \
    --rounds 2 \
    --bind-kernels risk_model_v2
```

## Integration with Spark Plug Architecture

The session manager integrates with the Spark Plug architecture:
- Creates `CpuInstance` objects for each session
- Binds sessions to memory kernels for context
- Stores session data in `ai/intercom/<conversation_id>/`

See: [SPARK_PLUG_ARCHITECTURE_v0.1.md](SPARK_PLUG_ARCHITECTURE_v0.1.md)
