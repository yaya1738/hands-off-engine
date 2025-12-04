# /dev/llm Virtual Device

FUSE-based virtual device providing file-like interface to LLM operations.

**Bounty:** [cortexlinux/cortex#223](https://github.com/cortexlinux/cortex/issues/223) - $125

## Status: PROTOTYPE COMPLETE

- [x] Core FUSE implementation
- [x] Claude API integration (with mock fallback)
- [x] Session management
- [x] 20/20 tests passing

## Usage

```bash
# Mount the device
python llm_device.py mount /mnt/llm

# It's just files!
echo "What is 2+2?" > /mnt/llm/claude/prompt
cat /mnt/llm/claude/response  # Returns: 4

# Works with any Unix tool
git diff | (echo "Review: $(cat)" > /mnt/llm/claude/prompt && cat /mnt/llm/claude/response)

# Session management
mkdir /mnt/llm/sessions/my-project
echo "Hello" > /mnt/llm/sessions/my-project/prompt
cat /mnt/llm/sessions/my-project/history  # Full conversation
```

## Directory Structure

```
/mnt/llm/
├── claude/              # Claude Sonnet
│   ├── prompt           # Write prompts here
│   ├── response         # Read responses
│   ├── config           # JSON configuration
│   └── metrics          # Usage stats
├── sessions/            # Stateful conversations
│   └── <session-name>/
│       ├── prompt
│       ├── response
│       ├── history
│       └── config
└── status               # System status
```

## Test

```bash
# Quick test without mounting
python llm_device.py test

# Run test suite
python -m pytest test_llm_device.py -v
```

## Files

- `llm_device.py` - Main implementation (~500 lines)
- `test_llm_device.py` - Test suite (~200 lines)

## Requirements

- Python 3.8+
- fusepy
- libfuse (system library)
- anthropic (optional, for real API calls)
