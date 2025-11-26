# Configuration System

This directory contains the centralized configuration management system for the Hands-Off Engine.

## Quick Start

```python
from config import get_config

# Get config manager
config = get_config()

# Load all configs
config.load_all()

# Get a value
max_position_size = config.get('risk', 'position_sizing', 'max_position_size')
```

## Directory Structure

```
config/
├── __init__.py           # Package exports
├── manager.py            # ConfigManager implementation
├── system.json           # Core system settings
├── risk.json             # Risk parameters from RISK_MODEL_V1
├── trading.json          # Trading settings
├── notifications.json    # Alert settings
├── agents.json           # AI agent settings
└── schemas/              # JSON schemas for validation
    ├── system_schema.json
    ├── risk_schema.json
    ├── trading_schema.json
    ├── notifications_schema.json
    └── agents_schema.json
```

## Configuration Files

### system.json
Core system settings including:
- Default mode (DRYRUN/LIVE)
- Log levels and directories
- Node configurations (Termux, Droplet, GitHub)

### risk.json
Risk management parameters from RISK_MODEL_V1:
- Position sizing limits
- Entry thresholds (min edge, min confidence)
- Daily limits and circuit breakers
- Safety layer configuration

### trading.json
Trading and execution settings:
- Execution mode and timeouts
- Market configuration
- Decision-making parameters
- Position management

### notifications.json
Alert and notification settings:
- Channel configuration (Telegram, GitHub, Email)
- Alert type settings
- Formatting options

### agents.json
AI agent settings:
- Backend configuration (OpenAI, Claude)
- AI Intake settings
- Orchestration configuration
- Safety settings

## Environment Variable Overrides

Override any config value using environment variables:

```bash
# Format: HO_<CONFIG>__<SECTION>__<KEY>=value
export HO_RISK__POSITION_SIZING__MAX_POSITION_SIZE=200.0
export HO_RISK__ENTRY_THRESHOLDS__MIN_CONFIDENCE=0.80
```

See `.env.example` in the repository root for all available overrides.

## CLI Tool

Use the config CLI for management:

```bash
# List all configs
python scripts/config_cli.py list

# View specific config
python scripts/config_cli.py view risk

# Validate configs
python scripts/config_cli.py validate

# Get specific value
python scripts/config_cli.py get risk position_sizing max_position_size

# Show environment overrides
python scripts/config_cli.py diff
```

## Integration Examples

### Executor
```python
from executor.ho_executor_plan import Executor

# Executor automatically loads config
executor = Executor()
# MAX_POSITION_SIZE and MIN_CONFIDENCE_THRESHOLD come from config
```

### Decider
```python
from decider.ho_decider import Decider

# Decider loads bankroll and risk params from config
decider = Decider()
# Can override with custom bankroll
decider = Decider(bankroll=5000.0)
```

## Schema Validation

All configs are validated against JSON schemas on load. Schemas enforce:
- Required fields
- Data types
- Value ranges
- Structure

To disable validation (not recommended):
```python
config.load_config('risk', validate=False)
```

## Hot-Reload

The config manager supports hot-reloading:

```python
# Check for changes
changes = config.check_for_changes()

# Auto-reload changed configs
reloaded = config.auto_reload()

# Manual reload
config.reload('risk')  # specific
config.reload()        # all
```

## Testing

Run the test suite:
```bash
python tests/unit/test_config_manager.py
```

## Security

- Never commit secrets to config files
- Use environment variables for API keys
- See `.env.example` for required environment variables
- Enable LIVE mode only after thorough testing

## Documentation

For complete documentation, see:
- [docs/CONFIGURATION.md](../docs/CONFIGURATION.md) - Full documentation
- [docs/RISK_MODEL_V1.md](../docs/RISK_MODEL_V1.md) - Risk model parameters
- [.env.example](../.env.example) - Environment variables

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2025-11-26 | 1.0 | Initial configuration management system |
