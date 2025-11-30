"""Groq Backend Provider - Extremely fast inference"""

import os
import json
from typing import List, Dict, Optional

def call_groq(
    prompt: str,
    model: str = "llama-3.1-70b-versatile",
    max_tokens: int = 2048,
    system_prompt: Optional[str] = None
) -> Dict:
    """
    Call Groq API for fast inference

    Args:
        prompt: User prompt
        model: Groq model to use
        max_tokens: Maximum tokens in response
        system_prompt: Optional system prompt

    Returns:
        Dict with 'content', 'model', 'tokens' keys
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {
            "content": "[Groq backend unavailable - GROQ_API_KEY not set]",
            "model": model,
            "tokens": 0,
            "error": "missing_api_key"
        }

    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7
        )

        return {
            "content": response.choices[0].message.content,
            "model": model,
            "tokens": response.usage.total_tokens if response.usage else 0
        }

    except ImportError:
        return {
            "content": "[Groq SDK not installed - pip install groq]",
            "model": model,
            "tokens": 0,
            "error": "sdk_not_installed"
        }
    except Exception as e:
        return {
            "content": f"[Groq error: {str(e)}]",
            "model": model,
            "tokens": 0,
            "error": str(e)
        }


def call_groq_fast(prompt: str) -> str:
    """Quick helper for simple prompts using fastest model"""
    result = call_groq(
        prompt=prompt,
        model="llama-3.1-8b-instant",  # Fastest model
        max_tokens=1024
    )
    return result.get("content", "")


# Available Groq models
GROQ_MODELS = {
    "llama-3.1-70b-versatile": "Best quality, slower",
    "llama-3.1-8b-instant": "Fastest, good for simple tasks",
    "mixtral-8x7b-32768": "Good balance, 32K context",
    "gemma2-9b-it": "Google's Gemma, efficient"
}


if __name__ == "__main__":
    # Test Groq connection
    result = call_groq("Say 'Groq is working!' in exactly those words.")
    print(f"Result: {result}")
