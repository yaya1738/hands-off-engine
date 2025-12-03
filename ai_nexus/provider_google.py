"""Google AI (Gemini) Backend Provider"""

import os
import json
from typing import List, Dict, Optional

def call_gemini(
    prompt: str,
    model: str = "gemini-1.5-flash",
    max_tokens: int = 2048,
    system_prompt: Optional[str] = None
) -> Dict:
    """
    Call Google Gemini API

    Args:
        prompt: User prompt
        model: Gemini model to use
        max_tokens: Maximum tokens in response
        system_prompt: Optional system prompt

    Returns:
        Dict with 'content', 'model', 'tokens' keys
    """
    api_key = os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "content": "[Gemini backend unavailable - GOOGLE_AI_API_KEY not set]",
            "model": model,
            "tokens": 0,
            "error": "missing_api_key"
        }

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        model_obj = genai.GenerativeModel(
            model_name=model,
            system_instruction=system_prompt
        )

        response = model_obj.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.7
            )
        )

        return {
            "content": response.text,
            "model": model,
            "tokens": 0  # Gemini doesn't always report tokens
        }

    except ImportError:
        return {
            "content": "[Google AI SDK not installed - pip install google-generativeai]",
            "model": model,
            "tokens": 0,
            "error": "sdk_not_installed"
        }
    except Exception as e:
        return {
            "content": f"[Gemini error: {str(e)}]",
            "model": model,
            "tokens": 0,
            "error": str(e)
        }


def call_gemini_fast(prompt: str) -> str:
    """Quick helper using fastest model"""
    result = call_gemini(
        prompt=prompt,
        model="gemini-1.5-flash",
        max_tokens=1024
    )
    return result.get("content", "")


# Available Gemini models
GEMINI_MODELS = {
    "gemini-1.5-pro": "Best quality, 1M context window",
    "gemini-1.5-flash": "Fast and efficient, good balance",
    "gemini-1.5-flash-8b": "Fastest, lowest cost"
}


if __name__ == "__main__":
    result = call_gemini("Say 'Gemini is working!' in exactly those words.")
    print(f"Result: {result}")
