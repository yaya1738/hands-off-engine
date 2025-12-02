# Bin Directory - Utility Scripts

This directory contains utility scripts for the Hands-Off Engine.

## Available Scripts

### `process-agent-sessions.sh` ⭐ NEW

**Purpose:** Process outputs from tri-agent sessions (ChatGPT, Claude, Copilot)

Extract and apply recommendations from previous agent discussions to system memory kernels.

```bash
# List recent sessions
./bin/process-agent-sessions.sh list

# Review a specific session
./bin/process-agent-sessions.sh review autokernel_risk_model_v2_20251127

# Apply updates (dry-run by default)
./bin/process-agent-sessions.sh apply autokernel_risk_model_v2_20251127

# Actually apply updates
./bin/process-agent-sessions.sh apply autokernel_risk_model_v2_20251127 --for-real

# Process multiple recent sessions interactively
./bin/process-agent-sessions.sh batch --recent 5
```

See: [docs/TRI_AGENT_SESSION_OUTPUT_HANDLING.md](../docs/TRI_AGENT_SESSION_OUTPUT_HANDLING.md)

---

### `ho-market-scanner.py`

**Purpose:** Scan Polymarket for trading opportunities

```bash
python bin/ho-market-scanner.py
```

---

### `ho-decision-infra.py`

**Purpose:** Decision infrastructure utilities

```bash
python bin/ho-decision-infra.py
```

---

### `decision_enricher.py`

**Purpose:** Enrich trading decisions with additional context

```bash
python bin/decision_enricher.py
```

---

## Adding New Scripts

When adding new utility scripts to this directory:

1. Make them executable: `chmod +x bin/your-script.sh`
2. Add shebang line: `#!/usr/bin/env bash` or `#!/usr/bin/env python3`
3. Include usage/help: `--help` flag or internal documentation
4. Update this README with a brief description
5. Link to detailed docs if the script is complex

## Naming Conventions

- Shell scripts: `kebab-case.sh`
- Python scripts: `snake_case.py` or `kebab-case.py`
- Prefix with `ho-` if directly related to core engine functionality
- Use descriptive names that indicate purpose
