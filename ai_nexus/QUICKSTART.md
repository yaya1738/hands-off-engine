# AI Nexus Quick Start Guide

Get up and running with ChatGPT integration in 5 minutes!

## Step 1: Install Dependencies

```bash
cd /home/user/hands-off-engine
pip install -r ai/requirements.txt
```

## Step 2: Configure API Key

Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY=sk-proj-...
```

Or create a `.env` file in the project root:

```bash
echo "OPENAI_API_KEY=sk-proj-..." > .env
```

## Step 3: Test the Integration

Run a simple test to verify everything works:

```bash
cd ai_nexus
python runner.py --once
```

This will process the example tasks in the `tasks/` directory and save results to `output/`.

## Step 4: Review Results

Check the output directory:

```bash
ls -l output/
cat output/chatgpt_market_analysis_result.txt
```

You should see both `.json` (structured) and `.txt` (human-readable) result files.

## Step 5: Create Your Own Task

Create a new task file:

```bash
cat > tasks/my_custom_task.json << 'EOF'
{
  "provider": "chatgpt",
  "prompt": "Explain the executor safety checks in simple terms.",
  "context_files": [
    "executor/ho_executor_plan.py"
  ]
}
EOF
```

Process it:

```bash
python runner.py --once
cat output/my_custom_task_result.txt
```

## Running Continuously

To monitor the tasks directory and automatically process new tasks:

```bash
python runner.py
```

Press Ctrl+C to stop.

## Next Steps

- Read the full [README.md](README.md) for advanced usage
- Explore the example tasks in `tasks/`
- Create custom task templates for your workflow
- Integrate with other Hands-Off Engine components

## Common Commands

```bash
# Process tasks once and exit
python runner.py --once

# Run in monitoring mode (continuous)
python runner.py

# Use custom directories
python runner.py --tasks-dir ../custom-tasks --output-dir ../results

# View logs
tail -f ../state/ai_nexus.log
```

## Troubleshooting

**Problem**: "OpenAI API key not found"
**Solution**: Run `export OPENAI_API_KEY=sk-...` or create `.env` file

**Problem**: "Failed to read context file"
**Solution**: Check file paths are relative to project root (e.g., `executor/ho_executor_plan.py`)

**Problem**: Rate limit errors
**Solution**: Wait a few minutes or upgrade your OpenAI plan

## Integration Examples

### From Python Code

```python
from ai_nexus import ChatGPTProvider

provider = ChatGPTProvider()
result = provider.run_task({
    "provider": "chatgpt",
    "prompt": "Review this code",
    "context_files": ["executor/ho_executor_plan.py"]
})

print(result['content'])
```

### From Command Line

```bash
# Create task
echo '{
  "provider": "chatgpt",
  "prompt": "Summarize the decider logic",
  "context_files": ["decider/ho_decider.py"]
}' > tasks/decider_summary.json

# Process
python runner.py --once

# View result
cat output/decider_summary_result.txt
```

## Success! 🎉

You now have ChatGPT integrated into your Hands-Off Engine!

The AI Nexus system enables:
- ✅ Multi-provider AI routing (ChatGPT, Claude, etc.)
- ✅ Context-aware prompting with file includes
- ✅ Automatic task processing from JSON files
- ✅ Robust error handling with retries
- ✅ Structured and human-readable outputs

Ready to build intelligent automation! 🚀
