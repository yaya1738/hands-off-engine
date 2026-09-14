# System Audit Tool

## Overview

The System Audit tool (`system_audit.py`) performs a comprehensive health check of the entire Hands-Off Engine system. It verifies that all critical components, configurations, and safety mechanisms are properly in place.

## Features

The audit script checks:

- ✅ **Core Components**: Verifies all major system components (alpha, decider, executor, fetchers, audit, AI systems)
- ✅ **Configuration**: Validates state files, knowledge base, and coordination settings
- ✅ **Safety & Security**: Checks DRYRUN enforcement, gitignore patterns, and credential handling
- ✅ **Audit Trails**: Verifies audit logging system and recent activity
- ✅ **Documentation**: Confirms presence of critical documentation files
- ✅ **Tests**: Counts and reports on test infrastructure
- ✅ **Dependencies**: Checks for dependency declaration files
- ✅ **AI Coordination**: Validates autonomous operation and multi-agent coordination
- ✅ **Financial Ledger**: Checks for financial tracking system

## Usage

### Basic Audit

Run the audit with default settings:

```bash
python3 scripts/system_audit.py
```

This will generate a report in `reports/system_audit_TIMESTAMP.md`.

### Verbose Mode

Get detailed output during the audit:

```bash
python3 scripts/system_audit.py --verbose
```

### Custom Output File

Specify a custom output file:

```bash
python3 scripts/system_audit.py --output-file my_audit_report.md
```

### Help

See all available options:

```bash
python3 scripts/system_audit.py --help
```

## Output

The script generates:

1. **Console Output**: Real-time progress with status indicators
2. **Markdown Report**: Comprehensive audit report with:
   - Executive summary with pass/warn/error counts
   - Overall system status
   - Component inventory
   - Detailed findings by category
   - Recommendations for improvements

### Status Indicators

- ✓ **Passed**: Check passed successfully
- ⚠ **Warning**: Non-critical issue detected
- ✗ **Error**: Critical issue detected
- ℹ **Info**: Informational message

### Overall Status

- ✅ **HEALTHY**: All checks passed, no warnings
- ⚠️ **OPERATIONAL (with warnings)**: System operational but has minor issues
- ❌ **ISSUES DETECTED**: Critical issues found requiring immediate attention

## Exit Codes

- `0`: Audit completed successfully (with or without warnings)
- `1`: Critical errors detected

## Integration

### Manual Execution

Run before deployments or after major changes:

```bash
python3 scripts/system_audit.py --verbose
```

### CI/CD Integration

Add to GitHub Actions workflows:

```yaml
- name: System Audit
  run: python3 scripts/system_audit.py --output-file reports/ci_audit.md
```

### Scheduled Audits

Add to cron for regular health checks:

```bash
# Daily audit at 6 AM
0 6 * * * cd ~/hands-off && python3 scripts/system_audit.py
```

## Audit Categories

### 1. Core Components

Verifies presence and health of:
- Alpha (edge estimation)
- Decider (decision making)
- Executor (trade execution)
- Fetchers (data collection)
- Audit (logging system)
- AI Nexus (multi-brain orchestration)
- AI (coordination and intake)

### 2. Configuration

Checks:
- `AI_POLICY.md` and other critical docs
- State JSON files in `state/`
- `knowledge.json` with required reading list
- Coordination status in `ai/coordination/status.json`

### 3. Safety & Security

Validates:
- DRYRUN enforcement in executor
- `.gitignore` patterns for sensitive files
- No committed credentials
- Safety mechanism presence

### 4. Audit Trails

Verifies:
- Audit log directory exists
- Recent audit activity
- Log file structure
- JSONL format compliance

### 5. Documentation

Confirms presence of:
- `AI_POLICY.md`
- `README.md`
- `docs/AUDIT_SYSTEM.md`
- `docs/DEVELOPMENT_STANDARDS.md`
- Research reports and roadmaps

### 6. Tests

Counts:
- Test files in `tests/`
- Coverage by component
- Test infrastructure setup

### 7. Dependencies

Checks for:
- `requirements.txt`
- `setup.py`
- `pyproject.toml`
- Python version information

### 8. AI Coordination

Validates:
- Autonomous mode status
- Active agents list
- Current system phase
- AI Nexus module count

### 9. Financial Ledger

Checks:
- Ledger file existence
- Entry count
- Latest activity timestamp

## Report Structure

```markdown
# Hands-Off Engine System Audit Report

**Generated**: [timestamp]
**Repository**: [path]

## Executive Summary
- Pass/Warn/Error counts
- Overall status

## [Component Sections]
- Detailed inventory

## Detailed Findings
- Errors
- Warnings
- Passed checks
- Info messages

## Recommendations
- Critical actions
- Suggested improvements
```

## Extending the Audit

To add new audit checks:

1. Add a new method to the `SystemAuditor` class:

```python
def audit_new_component(self):
    """Audit new component"""
    print("\n=== Auditing New Component ===")
    
    # Your checks here
    if self.check_file_exists('path/to/file'):
        self.log("Component check passed", 'passed')
    else:
        self.log("Component check failed", 'errors')
```

2. Call it from `run_full_audit()`:

```python
def run_full_audit(self):
    # ... existing checks ...
    self.audit_new_component()
```

## Best Practices

1. **Run Before Deployments**: Always audit before deploying to production
2. **Track Reports**: Keep audit reports for compliance and debugging
3. **Address Errors**: Fix all error-level findings before proceeding
4. **Review Warnings**: Regularly review and address warning-level findings
5. **Schedule Regular Audits**: Run weekly or after major changes
6. **Compare Reports**: Track changes in system health over time

## Troubleshooting

### "No audit logs directory found"

The audit logs directory will be created automatically when the audit system is first used. This is informational only.

### "Missing required file"

Critical files are missing. Review the error messages and ensure all required components are present.

### "Invalid JSON"

State or configuration files contain invalid JSON. Check the file contents and fix syntax errors.

### "No dependency files found"

The system doesn't have a formal dependency declaration. Consider adding `requirements.txt` or similar.

## Related Documentation

- [Audit System Documentation](../docs/AUDIT_SYSTEM.md)
- [Development Standards](../docs/DEVELOPMENT_STANDARDS.md)
- [AI Policy](../AI_POLICY.md)
- [Research Report](../termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md)

## Maintenance

This audit script should be updated when:
- New critical components are added
- Configuration structure changes
- New safety mechanisms are implemented
- Documentation requirements change

Keep the audit in sync with the actual system architecture.
