"""OpenAI/ChatGPT Backend Provider"""

import os
import json
from typing import List, Dict, Optional

def call_chatgpt(
    agent_id: str,
    prior_messages: List[Dict],
    session_goal: str,
    model: str = "gpt-4-turbo-preview",
    max_tokens: int = 2048
) -> Dict:
    """
    Call ChatGPT backend for tri-agent session

    Args:
        agent_id: Agent identifier ("chatgpt")
        prior_messages: List of prior messages in thread
        session_goal: Description of session purpose
        model: OpenAI model to use
        max_tokens: Maximum tokens in response

    Returns:
        Dict with 'content', 'model', 'tokens' keys
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "content": "[ChatGPT backend unavailable - OPENAI_API_KEY not set]",
            "model": model,
            "tokens": 0,
            "error": "missing_api_key"
        }

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)

        # Build conversation context
        messages = [
            {
                "role": "system",
                "content": f"""You are ChatGPT participating in a 3-way backend discussion between AI agents.

Session Goal: {session_goal}

Your role: Provide research, analysis, and strategic thinking.
Other participants: Claude CLI (implementation), GitHub Copilot Agent (GitHub features)

Review the prior messages and contribute your perspective. Be concise but thorough."""
            }
        ]

        # Add prior messages
        for msg in prior_messages[-10:]:  # Last 10 messages for context
            from_agent = msg.get('from_agent') or msg.get('from', 'unknown')
            role = "assistant" if from_agent == agent_id else "user"
            messages.append({
                "role": role,
                "content": f"[{from_agent}]: {msg['content']}"
            })

        # Call OpenAI API
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7
        )

        return {
            "content": response.choices[0].message.content,
            "model": response.model,
            "tokens": response.usage.total_tokens if response.usage else 0
        }

    except ImportError:
        return {
            "content": "[ChatGPT backend unavailable - openai package not installed. Run: pip install openai]",
            "model": model,
            "tokens": 0,
            "error": "missing_package"
        }
    except Exception as e:
        return {
            "content": f"[ChatGPT backend error: {str(e)}]",
            "model": model,
            "tokens": 0,
            "error": str(e)
        }
