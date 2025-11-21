# AI Nexus - Multi-Provider AI Integration System

## Overview

The AI Nexus module provides a flexible, provider-based architecture for integrating multiple AI services (ChatGPT, Claude, etc.) into the Hands-Off Engine. It enables seamless task routing, context-aware prompting, and robust error handling with automatic retries.

## Features

- **Multi-Provider Support**: Easy integration of multiple AI providers (ChatGPT, Claude, etc.)
- **Context-Aware Tasks**: Include context files to provide relevant information to AI models
- **Robust Error Handling**: Automatic retries with exponential backoff for transient failures
- **Structured Results**: Consistent JSON output format across all providers
- **Task Monitoring**: Automatic processing of task files from a monitored directory
- **Secure Configuration**: API keys loaded from environment variables or `.env` files

## Architecture

```
ai_nexus/
├── __init__.py              # Package initialization
├── provider_chatgpt.py      # ChatGPT provider implementation
├── runner.py                # Task dispatcher and executor
├── tasks/                   # Task definitions (JSON files)
│   ├── chatgpt_alpha_merge_plan.json
│   ├── chatgpt_code_review.json
│   └── chatgpt_market_analysis.json
└── output/                  # Task results (auto-generated)
    ├── *_result.json        # Structured JSON results
    └── *_result.txt         # Human-readable output
```

## Installation

### 1. Install Dependencies

```bash
cd /home/user/hands-off-engine
pip install -r ai/requirements.txt
```

The required dependencies are:
- `openai>=1.0.0` - OpenAI API client
- `python-dotenv>=1.0.0` - Environment variable management
- `requests>=2.31.0` - HTTP library

### 2. Configure API Keys

Create a `.env` file in the project root or set environment variables:

```bash
# OpenAI API Key (required for ChatGPT provider)
export OPENAI_API_KEY=sk-...

# Optional: Override default model
export OPENAI_MODEL=gpt-4-1106-preview
```

Or create a `.env` file:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-1106-preview
```

## Usage

### Method 1: Using the Runner Script (Recommended)

The runner script monitors the `tasks/` directory and automatically processes new task files:

```bash
cd ai_nexus

# Run in monitoring mode (continuous)
python runner.py

# Process existing tasks once and exit
python runner.py --once

# Custom directories
python runner.py --tasks-dir /path/to/tasks --output-dir /path/to/output
```

### Method 2: Direct Python API

```python
from ai_nexus import ChatGPTProvider

# Initialize provider
provider = ChatGPTProvider(
    model_name="gpt-4-1106-preview",  # optional
    max_retries=3,                     # optional
    backoff_factor=1.5                 # optional
)

# Define task
task = {
    "provider": "chatgpt",
    "prompt": "Analyze this code for potential bugs.",
    "context_files": [
        "executor/ho_executor_plan.py",
        "decider/ho_decider.py"
    ]
}

# Execute task
result = provider.run_task(task)

# Check result
if result['success']:
    print(f"Response: {result['content']}")
    print(f"Tokens used: {result['usage']['total_tokens']}")
else:
    print(f"Error: {result['error']}")
```

## Task Format

Tasks are defined as JSON files with the following structure:

```json
{
  "provider": "chatgpt",
  "prompt": "Your question or instruction here",
  "context_files": [
    "relative/path/to/file1.py",
    "relative/path/to/file2.json"
  ]
}
```

### Fields

- **provider** (required): The AI provider to use (e.g., "chatgpt")
- **prompt** (required): The main question or instruction for the AI
- **context_files** (optional): Array of file paths to include as context

## Result Format

Results are saved in two formats:

### JSON Format (`*_result.json`)

```json
{
  "provider": "chatgpt",
  "success": true,
  "content": "The AI's response...",
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 200,
    "total_tokens": 350
  },
  "task_file": "chatgpt_code_review.json",
  "timestamp": "2025-11-21T10:30:00.000000"
}
```

### Text Format (`*_result.txt`)

Human-readable format with task metadata and response content.

## Example Tasks

### 1. Code Review

```json
{
  "provider": "chatgpt",
  "prompt": "Review this code for safety checks, edge cases, and error handling.",
  "context_files": [
    "executor/ho_executor_plan.py",
    "decider/ho_decider.py"
  ]
}
```

### 2. Strategic Planning

```json
{
  "provider": "chatgpt",
  "prompt": "Draft a plan to merge the updated alpha strategy. Identify risks.",
  "context_files": [
    "docs/alpha_strategy_update.md",
    "state/alpha_performance_metrics.json"
  ]
}
```

### 3. Market Analysis

```json
{
  "provider": "chatgpt",
  "prompt": "Analyze trading performance and recommend strategy adjustments.",
  "context_files": [
    "state/alpha_performance_metrics.json"
  ]
}
```

## Provider Details

### ChatGPT Provider

**Class**: `ChatGPTProvider`
**File**: `provider_chatgpt.py`

#### Configuration

- **model_name**: OpenAI model to use (default: `gpt-4-1106-preview`)
- **max_retries**: Number of retry attempts on failure (default: 3)
- **backoff_factor**: Exponential backoff multiplier (default: 1.5)

#### Supported Models

- `gpt-4-1106-preview` (GPT-4 Turbo)
- `gpt-4` (GPT-4)
- `gpt-3.5-turbo` (GPT-3.5)
- Future models like `gpt-5.1` (when available)

#### Features

- **Context File Loading**: Automatically reads and includes specified files
- **Retry Logic**: Handles rate limits and transient failures
- **Token Tracking**: Reports usage statistics
- **Logging**: Detailed logging for debugging and monitoring

#### Error Handling

The provider implements robust error handling:

1. **API Key Validation**: Checks for `OPENAI_API_KEY` on initialization
2. **File Reading**: Logs errors for missing or unreadable context files
3. **API Failures**: Retries with exponential backoff
4. **Rate Limits**: Automatically handles rate limit errors with delays

## Integration with Hands-Off Engine

### Existing Components

The AI Nexus system integrates with:

1. **Alpha Generation** (`alpha/ho_alpha_polymarket.py`)
   - Can request ChatGPT analysis of market conditions

2. **Decider** (`decider/ho_decider.py`)
   - Can validate trading decisions with ChatGPT

3. **Executor** (`executor/ho_executor_plan.py`)
   - Can perform pre-execution safety reviews

### Workflow Integration

```
┌─────────────────────────────────────────────────────────────┐
│ Hands-Off Engine Workflow                                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. ALPHA → Generates signals                               │
│     └─ Can query ChatGPT for market analysis                │
│                                                              │
│  2. DECIDER → Makes trading decisions                       │
│     └─ Can request ChatGPT validation                       │
│                                                              │
│  3. EXECUTOR → Validates and executes                       │
│     └─ Can ask ChatGPT for safety checks                    │
│                                                              │
│  4. AI NEXUS → Provides AI capabilities                     │
│     ├─ ChatGPT Provider (implemented)                       │
│     ├─ Claude Provider (future)                             │
│     └─ Custom Providers (extensible)                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Advanced Usage

### Custom Provider Implementation

To add a new provider (e.g., Claude):

```python
class ClaudeProvider:
    def __init__(self, model_name: str = None, max_retries: int = 3):
        # Initialize Claude client
        pass

    def run_task(self, task: dict) -> dict:
        """
        Execute task and return result in standard format.

        Returns:
            {
                "provider": "claude",
                "success": bool,
                "content": str,
                "error": str or None
            }
        """
        pass
```

### Batch Processing

Process multiple tasks programmatically:

```python
from pathlib import Path
from ai_nexus.runner import AIRunner

runner = AIRunner(tasks_dir="./tasks", output_dir="./output")
runner.process_tasks(once=True)  # Process all tasks once
```

### Custom Logging

```python
import logging

# Configure custom logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_nexus.log'),
        logging.StreamHandler()
    ]
)

# Then use the provider
provider = ChatGPTProvider()
```

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** or `.env` files for secrets
3. **Restrict file access** - ensure context files don't contain sensitive data
4. **Monitor usage** - track API costs and token consumption
5. **Validate inputs** - sanitize prompts and file paths

## Troubleshooting

### Common Issues

#### 1. "OpenAI API key not found"

**Solution**: Set `OPENAI_API_KEY` environment variable or add to `.env` file

```bash
export OPENAI_API_KEY=sk-...
```

#### 2. "Failed to read context file"

**Solution**: Check that file paths are correct and files exist

```bash
# Use relative paths from project root
"context_files": ["executor/ho_executor_plan.py"]
```

#### 3. Rate Limit Errors

**Solution**: The provider automatically retries with exponential backoff. Increase `max_retries` if needed:

```python
provider = ChatGPTProvider(max_retries=5, backoff_factor=2.0)
```

#### 4. Model Not Found

**Solution**: Verify model name is correct and available:

```python
provider = ChatGPTProvider(model_name="gpt-4-1106-preview")
```

## Performance Considerations

- **Context Size**: Large context files increase token usage and cost
- **Model Selection**: GPT-4 is more expensive but more capable than GPT-3.5
- **Batch Processing**: Process multiple tasks in parallel when possible
- **Caching**: Results are saved to avoid re-processing identical tasks

## Future Enhancements

- [ ] Claude provider integration
- [ ] Anthropic API provider
- [ ] Task priority queue
- [ ] Result caching and deduplication
- [ ] Async/concurrent task processing
- [ ] Web UI for task management
- [ ] Real-time monitoring dashboard
- [ ] Cost tracking and budgets

## Contributing

To add a new provider:

1. Create `provider_<name>.py` in `ai_nexus/`
2. Implement the provider interface (see `provider_chatgpt.py`)
3. Register in `runner.py`'s `_init_providers()` method
4. Add documentation and examples
5. Submit pull request

## References

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Rate Limits Guide](https://cookbook.openai.com/examples/how_to_handle_rate_limits)
- [ChatCompletion Example](https://gist.github.com/pszemraj/c643cfe422d3769fd13b97729cf517c5)

## License

Part of the Hands-Off Engine project.

## Support

For issues or questions:
- Open an issue on GitHub
- Check the troubleshooting section above
- Review logs in `ai_nexus.log`
