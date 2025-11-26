# Configuration Management System

## Overview

The Hands-Off Engine configuration management system provides centralized, validated, and flexible configuration handling with support for environment variable overrides and hot-reloading.

## Architecture

### Components

1. **Config Manager** (`config/manager.py`)
   - Centralized configuration loading and access
   - Environment variable override support
   - JSON schema validation
   - Hot-reload capability
   - Singleton pattern for global access

2. **Configuration Files** (`config/*.json`)
   - `system.json` - Core system settings
   - `risk.json` - Risk parameters from RISK_MODEL_V1
   - `trading.json` - Trading settings and execution parameters
   - `notifications.json` - Alert and notification settings
   - `agents.json` - AI agent settings and orchestration

3. **JSON Schemas** (`config/schemas/*_schema.json`)
   - Validation schemas for each config type
   - Enforce required fields and data types
   - Provide helpful validation errors

4. **Config CLI** (`scripts/config_cli.py`)
   - View, validate, and inspect configurations
   - Command-line utility for configuration management

5. **Environment Template** (`.env.example`)
   - Documents all required environment variables
   - Shows configuration override syntax
   - Security best practices

## Usage

### Basic Usage

```python
from config import get_config

# Get the global config manager
config = get_config()

# Load all configs
config.load_all()

# Get a specific value
max_position_size = config.get('risk', 'position_sizing', 'max_position_size')
# Returns: 100.0

# Get a nested value with default
min_edge = config.get('risk', 'entry_thresholds', 'min_edge', default=0.05)

# Get full config
risk_config = config.get_full_config('risk')
```

### Environment Variable Overrides

Override any configuration value using environment variables:

```bash
# Format: HO_<CONFIG>__<SECTION>__<KEY>=value
# Note: Use double underscores (__) to separate path components

# Override max position size
export HO_RISK__POSITION_SIZING__MAX_POSITION_SIZE=200.0

# Override min confidence
export HO_RISK__ENTRY_THRESHOLDS__MIN_CONFIDENCE=0.80

# Override system mode
export HO_SYSTEM__SYSTEM__DEFAULT_MODE=DRYRUN
```

Type conversion is automatic:
- `true`, `yes`, `1` → `True` (boolean)
- `false`, `no`, `0` → `False` (boolean)
- Numbers with `.` → `float`
- Other numbers → `int`
- Everything else → `string`

### Config CLI Tool

```bash
# List all available configs
python scripts/config_cli.py list

# View all configurations
python scripts/config_cli.py view

# View specific config
python scripts/config_cli.py view risk

# Validate all configs
python scripts/config_cli.py validate

# Validate specific config
python scripts/config_cli.py validate risk

# Get specific value
python scripts/config_cli.py get risk position_sizing max_position_size
# Output: 100.0

# Show environment overrides
python scripts/config_cli.py diff
```

### Hot-Reload

The config manager supports hot-reloading configurations:

```python
from config import get_config

config = get_config()

# Check for changes
changes = config.check_for_changes()
# Returns: {'risk': False, 'system': True, ...}

# Automatically reload changed configs
reloaded = config.auto_reload()
# Returns: {'risk': False, 'system': True, ...}

# Manually reload specific config
config.reload('risk')

# Manually reload all configs
config.reload()
```

## Configuration Reference

### System Configuration (`system.json`)

Core system settings:

```json
{
  "system": {
    "default_mode": "DRYRUN",
    "log_level": "INFO",
    "log_dir": "logs",
    "state_dir": "state",
    "audit_enabled": true
  },
  "nodes": {
    "termux": {...},
    "droplet": {...},
    "github": {...}
  }
}
```

### Risk Configuration (`risk.json`)

Risk management parameters from RISK_MODEL_V1:

```json
{
  "position_sizing": {
    "max_position_size": 100.0,
    "max_bankroll_fraction": 0.10,
    "kelly_fraction_cap": 0.10
  },
  "entry_thresholds": {
    "min_edge": 0.03,
    "min_confidence": 0.70,
    "price_boundaries": {
      "min_price": 0.05,
      "max_price": 0.95
    }
  },
  "daily_limits": {
    "max_daily_risk": 500.0,
    "max_positions": 20,
    "circuit_breaker_loss": -200.0
  }
}
```

### Trading Configuration (`trading.json`)

Trading and execution settings:

```json
{
  "execution": {
    "default_mode": "DRYRUN",
    "order_timeout_seconds": 30
  },
  "markets": {
    "primary_platform": "polymarket",
    "min_liquidity": 1000.0
  },
  "decision_making": {
    "bankroll_default": 1000.0
  }
}
```

### Notifications Configuration (`notifications.json`)

Alert and notification settings:

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "priority_threshold": "INFO"
    }
  },
  "alert_types": {
    "execution": {...},
    "risk": {...},
    "system": {...}
  }
}
```

### Agents Configuration (`agents.json`)

AI agent settings and orchestration:

```json
{
  "default_backend": "openai",
  "backends": {
    "openai": {
      "type": "openai",
      "model": "gpt-4o-mini",
      "temperature": 0.3
    }
  },
  "ai_intake": {
    "enabled": true,
    "issue_number": 1
  }
}
```

## Validation

All configurations are validated against JSON schemas on load. Validation checks:

- Required fields are present
- Data types are correct
- Values are within acceptable ranges
- Nested structures are properly formed

To disable validation (not recommended):

```python
config.load_config('risk', validate=False)
```

## Security

### Best Practices

1. **Never commit secrets** - Use `.env` for sensitive values
2. **Use environment variables** for API keys and tokens
3. **Rotate credentials regularly**
4. **Review `.env.example`** for required environment variables
5. **Enable LIVE mode** only after thorough DRYRUN testing

### Required Environment Variables

See `.env.example` for a complete list of required environment variables:

- `OPENAI_API_KEY` - For AI Intake and planning
- `ANTHROPIC_API_KEY` - For Claude-based agents
- `GITHUB_TOKEN` - For workflow automation (set by GitHub Actions)

## Testing

Run the test suite:

```bash
python tests/unit/test_config_manager.py
```

Tests cover:
- Config loading and validation
- Environment variable overrides
- Type conversion
- Hot-reload functionality
- Error handling
- Singleton pattern

## Integration

### With Existing Components

The config manager is designed to integrate seamlessly with existing components:

```python
# In executor
from config import get_config

config = get_config()
max_position_size = config.get('risk', 'position_sizing', 'max_position_size')

# In decider
risk_config = config.get_full_config('risk')
kelly_cap = risk_config['position_sizing']['kelly_fraction_cap']

# In AI intake handler
agents_config = config.get_full_config('agents')
model = agents_config['backends']['openai']['model']
```

### Migration from Hardcoded Values

To migrate from hardcoded values:

1. Add configuration to appropriate JSON file
2. Update code to use `config.get()`
3. Document in `.env.example` if environment override is needed
4. Add tests for the configuration

## Troubleshooting

### Config file not found

Ensure config files exist in `config/` directory:

```bash
ls -la config/*.json
```

### Validation errors

Use the CLI to identify validation issues:

```bash
python scripts/config_cli.py validate
```

### Environment overrides not working

Check format - use double underscores:

```bash
# Correct
export HO_RISK__POSITION_SIZING__MAX_POSITION_SIZE=200.0

# Incorrect (old format, may not work)
export HO_RISK_POSITION_SIZING_MAX_POSITION_SIZE=200.0
```

Verify environment variable is set:

```bash
echo $HO_RISK__POSITION_SIZING__MAX_POSITION_SIZE
```

### Hot-reload not detecting changes

Check file modification times:

```python
config.check_for_changes()
```

Ensure file system supports `stat().st_mtime`.

## Future Enhancements

Potential future improvements:

1. **Remote config sources** - Load from S3, database, or config service
2. **Config versioning** - Track configuration changes over time
3. **Config inheritance** - Support base configs with overrides
4. **Config encryption** - Encrypt sensitive config values at rest
5. **Config UI** - Web interface for configuration management
6. **Config history** - Audit trail of configuration changes
7. **Dynamic reloading** - Automatically reload on file changes (using watchdog)

## Related Documentation

- [RISK_MODEL_V1](RISK_MODEL_V1.md) - Risk model parameters
- [AI_POLICY](../AI_POLICY.md) - AI policy and roadmap
- [AUDIT_SYSTEM](AUDIT_SYSTEM.md) - Audit logging system

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2025-11-26 | 1.0 | Initial configuration management system |
