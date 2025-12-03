# Spark Plug v0.2 - Quick Start Guide

**Status:** Ready to use (2025-11-25)

## What is v0.2?

Spark Plug v0.2 adds **continuous CPU mode** and **kernel auto-updates** to the tri-agent infrastructure.

- **v0.1**: Burst mode only (fixed number of rounds)
- **v0.2**: Continuous mode (loop with safety caps) + kernels evolve from sessions

## Quick Examples

### 1. Burst Mode (v0.1 - unchanged)

```bash
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251125_burst_test \
    --session-goal "Quick sanity check" \
    --rounds 2 \
    --agents chatgpt,claude_cli
```

**What happens:**
- Runs 2 rounds (each agent speaks twice)
- Stops after 2 rounds
- Output in `ai/intercom/20251125_burst_test/`

---

### 2. Continuous Mode (v0.2 - new!)

```bash
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251125_continuous_test \
    --session-goal "Deep dive on risk models" \
    --continuous \
    --max-steps 10 \
    --max-duration-seconds 300 \
    --agents chatgpt,claude_cli
```

**What happens:**
- Runs continuous loop
- Stops when EITHER:
  - 10 steps completed OR
  - 300 seconds elapsed
- Output in `ai/intercom/20251125_continuous_test/`

---

### 3. Continuous + Kernel Updates (v0.2 - new!)

First, create a test kernel:

```bash
python -m ai_nexus.memory_kernels
```

Then run continuous mode with kernel binding:

```bash
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251125_kernel_test \
    --session-goal "Research and update risk kernel" \
    --continuous \
    --max-steps 5 \
    --bind-kernels example_test_kernel \
    --kernel-update-mode append_notes \
    --agents chatgpt,claude_cli
```

**What happens:**
- Runs 5 continuous steps
- Kernels bound and loaded at start
- At end: session summary appended to `example_test_kernel`
- Check `ai/memory/kernels/example_test_kernel.json` for updates

---

## New CLI Flags (v0.2)

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--continuous` | bool | false | Enable continuous mode |
| `--max-steps` | int | 20 | Max steps for continuous mode |
| `--max-duration-seconds` | int | 900 | Max wall-clock seconds |
| `--kernel-update-mode` | choice | none | `none` or `append_notes` |

---

## Safety

✅ **Design-only:** No trading/execution access
✅ **Safety caps:** max-steps and max-duration-seconds prevent runaway
✅ **Append-only:** Kernel updates don't destroy data
✅ **Isolated:** No wires to decider/executor/risk

---

## Running Tests

```bash
cd /root/hands-off-engine
python -m pytest tests/unit/test_tri_agent_cpu_v02.py -v
```

**Tests cover:**
- Continuous mode stops on max-steps ✅
- Continuous mode stops on max-duration ✅
- Kernel updates applied ✅
- Burst mode still works ✅
- Serialization ✅

All tests offline (no real LLM calls).

---

## Output Files

After running a session, you'll find:

```
ai/intercom/{conversation_id}/
├── thread.jsonl          # All messages (CpuMessage JSONL)
├── metadata.json         # Legacy session metadata
└── cpu_instance.json     # CPU state (v0.2 tracking)
```

**v0.2 fields in `cpu_instance.json`:**
- `steps_completed` - Total steps
- `duration_seconds` - Total time
- `kernel_updates_applied` - Whether kernel updates written

---

## Smoke Test (Quick Validation)

Run this to verify v0.2 works:

```bash
# Create test kernel
python -m ai_nexus.memory_kernels

# Run continuous mode with kernel update
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id smoke_test_v02 \
    --session-goal "Smoke test v0.2" \
    --continuous \
    --max-steps 3 \
    --bind-kernels example_test_kernel \
    --kernel-update-mode append_notes \
    --agents chatgpt,claude_cli

# Check outputs
ls -la ai/intercom/smoke_test_v02/
cat ai/intercom/smoke_test_v02/cpu_instance.json | grep steps_completed
cat ai/memory/kernels/example_test_kernel.json | grep smoke_test
```

Expected:
- `steps_completed: 3` in cpu_instance.json
- Reference to smoke_test in kernel

---

## Troubleshooting

### "OPENAI_API_KEY not set"

```bash
export OPENAI_API_KEY="sk-..."
```

### "ANTHROPIC_API_KEY not set"

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### "Kernel not found"

Create kernels first:
```bash
python -m ai_nexus.memory_kernels
```

Or list available:
```bash
ls ai/memory/kernels/
```

---

## See Also

- **Full Architecture:** `docs/SPARK_PLUG_ARCHITECTURE_v0.1.md` (now v0.2)
- **Types:** `ai_nexus/spark_plug_types.py`
- **Runner:** `ai_nexus/tri_agent_session_runner.py`
- **Tests:** `tests/unit/test_tri_agent_cpu_v02.py`

---

**Created:** 2025-11-25
**Version:** 0.2
