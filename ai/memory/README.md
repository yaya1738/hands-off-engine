# AI Memory (Part 2: Historical Contraction)

This directory contains memory kernels - compressed, topic-specific memories built from historical AI interactions.

## Structure

```
ai/memory/
├── kernels/              # Topic-specific memory kernels
│   ├── risk_model_v2.json
│   ├── infra_architecture.json
│   ├── ai_coordination.json
│   └── ...
└── README.md             # This file
```

## What are Memory Kernels?

Memory kernels are **compressed, topic-focused memories** built from:
- User ↔ ChatGPT interactions
- User ↔ Claude CLI interactions
- Multi-agent CPU discussions (Part 1)
- System actions and decisions

Each kernel contains:
- **Summary**: Tight narrative of what's known and decided
- **Key Decisions**: Durable decisions with rationale and sources
- **Failed Paths**: Attempts that failed and lessons learned
- **Open Questions**: Unresolved questions
- **Source Weights**: Trust levels per agent (ChatGPT > Claude > others)
- **Raw Refs**: Links to original sources in `ai/history/`

## Usage

### Load a Kernel

```python
from ai_nexus.memory_kernels import load_kernel

kernel = load_kernel("risk_model_v2")
print(kernel.summary)
print(f"Decisions: {len(kernel.key_decisions)}")
```

### Append an Update

```python
from ai_nexus.memory_kernels import append_kernel_update
from ai_nexus.spark_plug_types import create_kernel_update_decision

update = create_kernel_update_decision(
    decision="Kelly fraction increased to 0.15",
    rationale="First stage of rollout",
    source="cpu_risk_20251125_01",
    agent="chatgpt"
)

append_kernel_update("risk_model_v2", update)
```

### Create a New Kernel

```python
from ai_nexus.memory_kernels import create_kernel

kernel = create_kernel(
    kernel_id="my_new_topic",
    topic="My New Topic",
    summary="Initial summary..."
)
```

### List All Kernels

```python
from ai_nexus.memory_kernels import list_kernels

kernels = list_kernels()
print(f"Available kernels: {', '.join(kernels)}")
```

## Kernel Lifecycle

1. **Creation**: Manual (for now) via `create_kernel()`
2. **Updates**: CPU (Part 1) writes via `append_kernel_update()`
3. **Reading**: CPU (Part 1) reads via `load_kernel()`
4. **Contraction**: Future engine ingests from `ai/history/*` and builds/updates kernels

## Future: Contraction Engine

The full contraction engine (not yet implemented) will:
- Ingest raw logs from `ai/history/chatgpt/`, `ai/history/claude_cli/`, etc.
- Normalize different log formats
- Extract key decisions, failed paths, open questions
- Compress into kernel summaries
- Auto-update kernels as new interactions happen

For now, kernels are created and updated manually via the API.

## See Also

- `docs/SPARK_PLUG_ARCHITECTURE_v0.1.md` - Full architecture
- `ai_nexus/spark_plug_types.py` - Core types (MemoryKernel, KernelUpdate)
- `ai_nexus/memory_kernels.py` - API implementation

---

**Status:** v0.1 stub - API ready, contraction engine not yet implemented
