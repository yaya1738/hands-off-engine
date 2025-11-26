"""Anthropic Claude Backend Provider"""

import os
import json
from typing import List, Dict, Optional

def call_claude(
    agent_id: str,
    prior_messages: List[Dict],
    session_goal: str,
    model: str = "claude-3-5-sonnet-20241022",
    max_tokens: int = 2048
) -> Dict:
    """
    Call Claude backend for tri-agent session

    Args:
        agent_id: Agent identifier ("claude_cli")
        prior_messages: List of prior messages in thread
        session_goal: Description of session purpose
        model: Anthropic model to use
        max_tokens: Maximum tokens in response

    Returns:
        Dict with 'content', 'model', 'tokens' keys
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "content": "[Claude backend unavailable - ANTHROPIC_API_KEY not set]",
            "model": model,
            "tokens": 0,
            "error": "missing_api_key"
        }

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        # Build system prompt
        system_prompt = f"""You are Claude participating in a 3-way backend discussion between AI agents.

Session Goal: {session_goal}

Your role: Provide implementation expertise, code analysis, and practical solutions.
Other participants: ChatGPT (research/strategy), GitHub Copilot Agent (GitHub features)

Review the prior messages and contribute your perspective. Be concise but thorough."""

        # Build conversation
        messages = []
        for msg in prior_messages[-10:]:  # Last 10 messages for context
            role = "assistant" if msg['from_agent'] == agent_id else "user"
            messages.append({
                "role": role,
                "content": f"[{msg['from_agent']}]: {msg['content']}"
            })

        # Add user prompt if last message wasn't from this agent
        if not prior_messages or prior_messages[-1]['from_agent'] != agent_id:
            messages.append({
                "role": "user",
                "content": "Please provide your analysis and recommendations."
            })

        # Call Anthropic API
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages
        )

        return {
            "content": response.content[0].text,
            "model": response.model,
            "tokens": response.usage.input_tokens + response.usage.output_tokens
        }

    except ImportError:
        return {
            "content": "[Claude backend unavailable - anthropic package not installed. Run: pip install anthropic]",
            "model": model,
            "tokens": 0,
            "error": "missing_package"
        }
    except Exception as e:
        return {
            "content": f"[Claude backend error: {str(e)}]",
            "model": model,
            "tokens": 0,
            "error": str(e)
        }
