#!/usr/bin/env python3
"""
OpenAI Provider for AI Nexus
Integrates OpenAI's GPT models
"""
import os
from typing import Optional

from .nexus_core import AIProvider, AIProviderType, AIRequest, AIResponse
from audit import AuditLogger, FinancialLedger


class OpenAIProvider(AIProvider):
    """
    Provider for OpenAI GPT models

    Pricing (as of 2024):
    - GPT-4o: $2.50/MTok input, $10/MTok output
    - GPT-4o-mini: $0.150/MTok input, $0.600/MTok output
    - GPT-4-turbo: $10/MTok input, $30/MTok output
    """

    # Token pricing per million tokens
    PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.0},
        "gpt-4o-mini": {"input": 0.150, "output": 0.600},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5}
    }

    def __init__(
        self,
        audit_logger: AuditLogger,
        ledger: FinancialLedger,
        api_key: Optional[str] = None
    ):
        super().__init__(audit_logger, ledger)
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = None

        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                pass

    def get_provider_type(self) -> AIProviderType:
        return AIProviderType.OPENAI

    def estimate_cost(self, request: AIRequest) -> float:
        """
        Estimate cost based on prompt length and expected completion

        Args:
            request: AI request

        Returns:
            Estimated cost in USD
        """
        model = request.model or "gpt-4o-mini"
        pricing = self.PRICING.get(model, self.PRICING["gpt-4o-mini"])

        # Rough estimation: 1 token ≈ 4 characters
        prompt_tokens = len(request.prompt) / 4
        if request.system_message:
            prompt_tokens += len(request.system_message) / 4

        # Estimate completion tokens
        completion_tokens = min(
            request.max_tokens or prompt_tokens,
            4096  # reasonable default
        )

        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def execute(self, request: AIRequest) -> AIResponse:
        """
        Execute an OpenAI request

        Args:
            request: AI request

        Returns:
            AI response with actual usage and cost
        """
        if not self.client:
            return AIResponse(
                request_id=request.request_id,
                provider_type=AIProviderType.OPENAI,
                content="",
                model_used=request.model or "gpt-4o-mini",
                tokens_used={"prompt": 0, "completion": 0, "total": 0},
                cost=0.0,
                latency_ms=0.0,
                success=False,
                error="OpenAI client not initialized (missing API key or openai package)"
            )

        model = request.model or "gpt-4o-mini"
        pricing = self.PRICING.get(model, self.PRICING["gpt-4o-mini"])

        # Build messages
        messages = []
        if request.system_message:
            messages.append({"role": "system", "content": request.system_message})
        messages.append({"role": "user", "content": request.prompt})

        # Execute request
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )

            # Extract usage
            usage = response.usage
            tokens_used = {
                "prompt": usage.prompt_tokens,
                "completion": usage.completion_tokens,
                "total": usage.total_tokens
            }

            # Calculate actual cost
            input_cost = (usage.prompt_tokens / 1_000_000) * pricing["input"]
            output_cost = (usage.completion_tokens / 1_000_000) * pricing["output"]
            total_cost = input_cost + output_cost

            content = response.choices[0].message.content

            return AIResponse(
                request_id=request.request_id,
                provider_type=AIProviderType.OPENAI,
                content=content,
                model_used=model,
                tokens_used=tokens_used,
                cost=total_cost,
                latency_ms=0.0,  # Set by nexus core
                success=True
            )

        except Exception as e:
            return AIResponse(
                request_id=request.request_id,
                provider_type=AIProviderType.OPENAI,
                content="",
                model_used=model,
                tokens_used={"prompt": 0, "completion": 0, "total": 0},
                cost=0.0,
                latency_ms=0.0,
                success=False,
                error=str(e)
            )


# Standalone function for tri-agent session runner and alpha engine
def call_chatgpt(
    agent_id: str,
    prior_messages: list,
    session_goal: str,
    model: str = "gpt-4o-mini",
    max_tokens: int = 2048
) -> dict:
    """
    Call ChatGPT backend for tri-agent session and alpha analysis.

    Args:
        agent_id: Agent identifier ("chatgpt")
        prior_messages: List of prior messages in conversation
        session_goal: Description of session purpose
        model: OpenAI model to use
        max_tokens: Maximum tokens in response

    Returns:
        Dict with 'content', 'model', 'tokens' keys
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {
            "content": "[ChatGPT backend unavailable - OPENAI_API_KEY not set]",
            "model": model,
            "tokens": 0,
            "error": "missing_api_key"
        }

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        # Build conversation context
        messages = [
            {
                "role": "system",
                "content": f"""You are ChatGPT providing analysis for an autonomous trading system.

Session Goal: {session_goal}

Provide accurate, data-driven analysis. Be concise but thorough."""
            }
        ]

        # Add prior messages
        for msg in prior_messages[-10:]:  # Last 10 messages for context
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
                messages.append({"role": role, "content": content})

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
            "content": "[ChatGPT backend unavailable - openai package not installed]",
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
