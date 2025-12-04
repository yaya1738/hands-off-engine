# Accelerator-Aware Resource Limits

cgroups v2 wrapper for AI workloads with preset profiles and GPU environment management.

**Bounty:** [cortexlinux/cortex#222](https://github.com/cortexlinux/cortex/issues/222) - $100

## Status: PROTOTYPE COMPLETE

- [x] Workload presets (inference, training, batch, interactive)
- [x] ResourceProfile dataclass with full serialization
- [x] cgroups v2 controller with user delegation support
- [x] GPU environment management (CUDA_VISIBLE_DEVICES, TensorFlow, PyTorch)
- [x] Profile persistence
- [x] Full CLI with create/apply/env/status/list/delete
- [x] 32/32 tests passing

## Usage

```bash
# List available presets
cortex limits presets

# Create an inference profile
cortex limits create llm-serve --preset inference --gpus 2

# Create a training profile with custom resources
cortex limits create train-bert --preset training --cpus 32 --memory 256

# Apply to a running process
cortex limits apply llm-serve --pid 12345

# Set environment for GPU workload
eval $(cortex limits env llm-serve)
python my_inference.py

# Check status
cortex limits status llm-serve

# List profiles
cortex limits list

# Delete profile
cortex limits delete llm-serve
```

## Presets

| Preset      | CPU Cores | Memory | GPU | OOM Score | Use Case           |
|-------------|-----------|--------|-----|-----------|-------------------|
| inference   | 4         | 32 GB  | 100%| -500      | Low-latency serving|
| training    | 16        | 128 GB | 100%| -800      | Long training jobs |
| batch       | 8         | 64 GB  | 80% | 0         | Background work    |
| interactive | 2         | 16 GB  | 50% | -200      | Development        |

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    AcceleratorLimitsCLI                       │
├──────────────────────────────────────────────────────────────┤
│  create │ apply │ env │ status │ list │ delete │ presets     │
└────┬─────────┬─────────┬──────────────────────────────────────┘
     │         │         │
     v         v         v
┌─────────┐ ┌───────────────┐ ┌─────────────┐
│ProfileStore│ │CgroupsController│ │ GPUManager  │
│           │ │               │ │             │
│ save()    │ │ create_cgroup()│ │ get_env_vars()│
│ load()    │ │ apply_to_pid()│ │             │
│ list()    │ │ get_status()  │ │             │
│ delete()  │ │ delete_cgroup()│ │             │
└─────────┘ └───────────────┘ └─────────────┘
     │              │
     v              v
 ~/.config/     /sys/fs/cgroup/
 cortex/limits  cortex.slice/
```

## cgroups v2 Integration

Supports both system-wide and user-delegated cgroups:

```
# System path (root)
/sys/fs/cgroup/cortex.slice/<profile>/

# User delegated path (non-root)
/sys/fs/cgroup/user.slice/user-1000.slice/cortex.slice/<profile>/
```

Controls applied:
- `cpu.weight` - CPU shares (1-10000)
- `cpu.max` - CPU quota (cores * period)
- `memory.max` - Hard memory limit
- `memory.high` - Soft memory limit
- `memory.swap.max` - Swap limit

## GPU Environment Variables

Generated for frameworks:

```bash
# CUDA device selection
export CUDA_VISIBLE_DEVICES=0,1

# TensorFlow memory growth
export TF_FORCE_GPU_ALLOW_GROWTH=true
export TF_GPU_MEMORY_FRACTION=0.5

# PyTorch memory allocation
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:16384
```

## Test

```bash
# Run test suite
python -m pytest test_accelerator_limits.py -v

# Quick CLI test
python accelerator_limits.py presets
python accelerator_limits.py create test-job --preset inference
python accelerator_limits.py status test-job
python accelerator_limits.py env test-job
python accelerator_limits.py delete test-job
```

## Files

- `accelerator_limits.py` - Main implementation (~530 lines)
- `test_accelerator_limits.py` - Test suite (~320 lines)

## Requirements

- Python 3.8+
- Linux with cgroups v2
- Optional: systemd for user delegation
