"""
Multi-Provider LLM Router
========================
Routes requests to the best available provider based on:
- API key availability
- Cost optimization
- Speed requirements
- Model capabilities
"""

import os
from typing import Dict, Optional, List
from enum import Enum

class Provider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    GOOGLE = "google"
    TOGETHER = "together"


class ProviderStatus:
    """Track which providers are available"""

    @staticmethod
    def check_all() -> Dict[str, bool]:
        """Check which providers have API keys configured"""
        return {
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
            "groq": bool(os.getenv("GROQ_API_KEY")),
            "google": bool(os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")),
            "together": bool(os.getenv("TOGETHER_API_KEY")),
        }

    @staticmethod
    def get_available() -> List[str]:
        """Get list of available providers"""
        status = ProviderStatus.check_all()
        return [p for p, available in status.items() if available]


class MultiProviderLLM:
    """
    Unified interface for calling multiple LLM providers
    """

    # Provider priority for different use cases
    PRIORITY_FAST = ["groq", "google", "openai", "anthropic"]
    PRIORITY_QUALITY = ["anthropic", "openai", "google", "groq"]
    PRIORITY_CHEAP = ["groq", "google", "together", "openai"]

    def __init__(self):
        self.available = ProviderStatus.get_available()

    def call(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        priority: str = "quality",  # "fast", "quality", "cheap"
        max_tokens: int = 2048,
        fallback: bool = True
    ) -> Dict:
        """
        Call LLM with automatic provider selection

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            priority: "fast", "quality", or "cheap"
            max_tokens: Max response tokens
            fallback: Try next provider on failure

        Returns:
            Dict with content, model, tokens, provider
        """
        if priority == "fast":
            order = self.PRIORITY_FAST
        elif priority == "cheap":
            order = self.PRIORITY_CHEAP
        else:
            order = self.PRIORITY_QUALITY

        # Filter to available providers
        providers_to_try = [p for p in order if p in self.available]

        if not providers_to_try:
            return {
                "content": "[No LLM providers available - configure API keys]",
                "error": "no_providers",
                "provider": None
            }

        last_error = None
        for provider in providers_to_try:
            result = self._call_provider(provider, prompt, system_prompt, max_tokens)
            if "error" not in result:
                result["provider"] = provider
                return result
            last_error = result
            if not fallback:
                break

        return last_error or {"content": "[All providers failed]", "error": "all_failed"}

    def _call_provider(
        self,
        provider: str,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int
    ) -> Dict:
        """Call specific provider"""

        if provider == "openai":
            from ai_nexus.provider_openai import call_chatgpt
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            return call_chatgpt(
                agent_id="multi_provider",
                prior_messages=messages,
                session_goal=prompt[:100],
                max_tokens=max_tokens
            )

        elif provider == "groq":
            from ai_nexus.provider_groq import call_groq
            return call_groq(prompt, system_prompt=system_prompt, max_tokens=max_tokens)

        elif provider == "google":
            from ai_nexus.provider_google import call_gemini
            return call_gemini(prompt, system_prompt=system_prompt, max_tokens=max_tokens)

        elif provider == "anthropic":
            # Claude is typically used via CLI, but can add direct API
            return {
                "content": "[Anthropic direct API not implemented - use Claude CLI]",
                "error": "not_implemented"
            }

        else:
            return {"content": f"[Unknown provider: {provider}]", "error": "unknown"}

    def quick(self, prompt: str) -> str:
        """Quick helper - fastest available provider, just returns content"""
        result = self.call(prompt, priority="fast", max_tokens=1024)
        return result.get("content", "")


# Singleton instance
_llm = None

def get_llm() -> MultiProviderLLM:
    """Get singleton LLM instance"""
    global _llm
    if _llm is None:
        _llm = MultiProviderLLM()
    return _llm


def quick_llm(prompt: str) -> str:
    """Quick LLM call - returns just the content string"""
    return get_llm().quick(prompt)


if __name__ == "__main__":
    print("=== Multi-Provider LLM Status ===")
    print(f"Available providers: {ProviderStatus.get_available()}")
    print(f"All status: {ProviderStatus.check_all()}")

    llm = get_llm()
    if llm.available:
        print(f"\nTesting with: {llm.available[0]}")
        result = llm.call("Say 'Multi-provider working!' in exactly those words.")
        print(f"Result: {result}")
