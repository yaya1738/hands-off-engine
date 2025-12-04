# System Configuration - Natural Language

**NO JSON EDITING. NO MANUAL CONFIG.**

Just tell the system what you want. It configures itself.

---

## How To Configure

### Option 1: Command Line

```bash
python3 -c "
from autonomous.config_manager import ConfigManager
cm = ConfigManager()
cm.process_instruction('Hire 3 full-stack developers')
"
```

### Option 2: Batch Instructions

Create `config/instructions.txt`:
```
Hire 3 full-stack developers
Increase budget to $20,000
Be more selective in hiring
Focus on AI/ML work
Pay 30% bonus for quality above 95
```

Then run:
```bash
python3 -c "
from autonomous.config_manager import ConfigManager
cm = ConfigManager()
instructions = open('config/instructions.txt').read().splitlines()
cm.process_batch_instructions(instructions)
"
```

### Option 3: Interactive

```bash
python3 autonomous/config_manager.py
# Follow prompts
```

---

## Supported Instructions

### Hiring:

```
"Hire 3 full-stack developers"
"Hire 2 AI/ML engineers"
"Hire 1 DevOps engineer"
"Be more selective in hiring"
"Be less selective"
"Hire faster"
"Raise the hiring bar"
```

### Budget:

```
"Increase budget to $15,000"
"Increase budget to $20k"
"Raise budget to $25,000"
```

### Quality:

```
"Higher quality standards"
"Be stricter with quality"
"Raise the quality bar"
"Move faster" (lower bar)
"Lower quality bar"
```

### Focus:

```
"Focus on AI/ML work"
"Focus on backend development"
"Focus on frontend work"
"Focus on DevOps"
```

### Payments:

```
"Pay 25% bonus for quality above 95"
"Pay 30% bonus for exceptional work"
"Increase hourly rates by $5"
"Raise rates"
```

### Scaling:

```
"Scale up the team"
"Grow the team"
"Expand hiring"
"Scale down"
"Reduce team size"
```

---

## Examples

### Scenario 1: Initial Setup

```bash
python3 -c "
from autonomous.config_manager import ConfigManager
cm = ConfigManager()

# Set up initial configuration
cm.process_batch_instructions([
    'Hire 2 full-stack developers',
    'Hire 1 AI/ML engineer',
    'Set budget to $15,000',
    'Focus on AI work'
])

# Check what was configured
print(cm.get_configuration_summary())
"
```

**Result:**
- 2 Full-Stack Developer positions open
- 1 AI/ML Engineer position open
- Budget: $15k/month
- System starts hiring automatically

### Scenario 2: Adjust Quality

```bash
python3 -c "
from autonomous.config_manager import ConfigManager
cm = ConfigManager()
cm.process_instruction('Be more selective in hiring')
cm.process_instruction('Higher quality standards')
"
```

**Result:**
- Hiring threshold: 85 → 90
- Quality approval threshold: 90 → 95
- Test coverage: 90% → 95%
- System applies new standards immediately

### Scenario 3: Scale Up

```bash
python3 -c "
from autonomous.config_manager import ConfigManager
cm = ConfigManager()
cm.process_batch_instructions([
    'Increase budget to $30,000',
    'Scale up the team',
    'Hire 5 full-stack developers',
    'Hire 3 AI/ML engineers'
])
"
```

**Result:**
- Budget: $10k → $30k
- Hiring rate: 3/week → 5/week
- Positions: Scaled up
- System starts aggressive hiring

---

## What Gets Configured

### When you say "Hire 3 full-stack developers":

System configures:
```json
{
  "positions": [
    {
      "role": "Full Stack Developer",
      "max_count": 3,
      "rate_range": [45, 60],
      "max_hours_per_week": 40,
      "skills_required": ["Python", "React", "FastAPI", "Testing", "Git"]
    }
  ]
}
```

Then automatically:
- Posts jobs to 5+ platforms
- Screens applications (score 85+)
- Sends coding challenges
- Evaluates submissions
- Makes offers
- Onboards

**Your time: 10 seconds to say it**
**System time: Continuous execution**

### When you say "Increase budget to $20k":

System configures:
```json
{
  "budget_controls": {
    "monthly_budget": 20000,
    "emergency_reserve": 4000
  }
}
```

Then automatically:
- Adjusts hiring capacity
- Processes payments up to limit
- Alerts at 80% utilization

**Your time: 5 seconds**
**System time: Monitors 24/7**

---

## Configuration History

### View what's been configured:

```bash
cat state/config_instructions.json
```

**Output:**
```json
{
  "instructions": [
    {
      "instruction": "hire 3 full-stack developers",
      "timestamp": "2025-12-04T...",
      "changes": [
        {
          "type": "hiring_count",
          "action": "updated",
          "role": "Full Stack Developer",
          "count": 3
        }
      ],
      "status": "applied"
    }
  ],
  "total_instructions": 5,
  "last_instruction": {...}
}
```

---

## Current Configuration

### Check what's active:

```bash
python3 -c "
from autonomous.config_manager import ConfigManager
cm = ConfigManager()
import json
print(json.dumps(cm.get_configuration_summary(), indent=2))
"
```

**Output:**
```json
{
  "hiring": {
    "auto_hire_threshold": "90/100",
    "max_hires_per_week": 3,
    "open_positions": [...]
  },
  "budget": {
    "monthly": "$15,000",
    "emergency_reserve": "$3,000"
  },
  "quality": {
    "auto_approve_work": "90/100",
    "test_coverage_required": "90%"
  },
  "payments": {
    "auto_pay_threshold": "90/100",
    "quality_bonus": "25%"
  }
}
```

---

## Integration with Backend Loop

Configuration changes apply immediately to:
- `autonomous/remote_employee_manager.py`
- `autonomous/email_monitor.py`
- `autonomous/payment_automation.py`
- All autonomous systems

**No restart needed. Hot-reloaded.**

---

## MAX YAIR LEVERAGE Achievement

### Traditional Configuration:
```
1. Research best practices (2 hours)
2. Write JSON config (1 hour)
3. Test configuration (1 hour)
4. Debug issues (2 hours)
5. Update documentation (1 hour)
Total: 7 hours
```

### Autonomous Configuration:
```
1. Say: "Hire 3 developers, budget $15k"
Total: 10 seconds

System does:
- Parses instruction (instant)
- Updates all configs (instant)
- Applies to all subsystems (instant)
- Starts executing (continuous)
```

**Leverage: 7 hours → 10 seconds = 2,520x**

---

## Advanced Usage

### Conditional Configuration:

```python
from autonomous.config_manager import ConfigManager
cm = ConfigManager()

# Get current state
summary = cm.get_configuration_summary()
current_budget = summary["budget"]["monthly"]

# Adjust based on performance
if current_budget < 20000:
    cm.process_instruction("Increase budget to $20,000")
    cm.process_instruction("Hire 2 more developers")
```

### Scheduled Configuration:

```bash
# Cron job for quarterly adjustments
# Every quarter: Scale up
echo "0 0 1 */3 * python3 -c 'from autonomous.config_manager import ConfigManager; ConfigManager().process_instruction(\"Scale up the team\")'" | crontab -
```

---

## Bottom Line

**Configuration is now autonomous.**

You say what you want (natural language).
System configures itself (all subsystems).
Execution starts immediately (continuous).

**No JSON editing. No manual config. No technical knowledge needed.**

**TRUE MAX YAIR LEVERAGE.** ✓

---

## Quick Reference

```bash
# Configure via instruction
python3 -c "from autonomous.config_manager import ConfigManager; ConfigManager().process_instruction('YOUR INSTRUCTION HERE')"

# View current config
python3 -c "from autonomous.config_manager import ConfigManager; import json; print(json.dumps(ConfigManager().get_configuration_summary(), indent=2))"

# View instruction history
cat state/config_instructions.json | jq

# Test configuration
python3 autonomous/config_manager.py
```

🚀
