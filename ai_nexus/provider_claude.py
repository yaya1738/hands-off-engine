#!/usr/bin/env python3
"""
Claude AI Provider for AI Nexus
Integrates Anthropic's Claude models

HFT Economics: All API calls tracked at microsecond frequency.
"""
import os
import time
from typing import Optional

from .nexus_core import AIProvider, AIProviderType, AIRequest, AIResponse
from audit import AuditLogger, FinancialLedger

# HFT Economics tracking
try:
    from integrafix.hft_economics import track_api_call
    HFT_TRACKING = True
except ImportError:
    HFT_TRACKING = False
    def track_api_call(*args, **kwargs): return 0


class ClaudeProvider(AIProvider):
    """
    Provider for Anthropic Claude models

    Pricing (as of 2024):
    - Claude 3.5 Sonnet: $3/MTok input, $15/MTok output
    - Claude 3 Opus: $15/MTok input, $75/MTok output
    - Claude 3 Haiku: $0.25/MTok input, $1.25/MTok output
    """

    # Token pricing per million tokens
    PRICING = {
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
        "claude-3-5-sonnet-latest": {"input": 3.0, "output": 15.0},
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0}
    }

    def __init__(
        self,
        audit_logger: AuditLogger,
        ledger: FinancialLedger,
        api_key: Optional[str] = None
    ):
        super().__init__(audit_logger, ledger)
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

        if not self.api_key:
            # Claude might be accessed through CLI, not API
            # We'll track actions through audit system even without API
            pass

    def get_provider_type(self) -> AIProviderType:
        return AIProviderType.CLAUDE

    def estimate_cost(self, request: AIRequest) -> float:
        """
        Estimate cost based on prompt length and expected completion

        Args:
            request: AI request

        Returns:
            Estimated cost in USD
        """
        model = request.model or "claude-3-5-sonnet-latest"
        pricing = self.PRICING.get(model, self.PRICING["claude-3-5-sonnet-latest"])

        # Rough estimation: 1 token ≈ 4 characters
        prompt_tokens = len(request.prompt) / 4
        if request.system_message:
            prompt_tokens += len(request.system_message) / 4

        # Estimate completion tokens (default: same as prompt, max: max_tokens)
        completion_tokens = min(
            request.max_tokens or prompt_tokens,
            4096  # reasonable default
        )

        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def execute(self, request: AIRequest) -> AIResponse:
        """
        Execute a Claude request

        Note: This is a tracking wrapper. Actual Claude execution happens
        through the Claude Code CLI. This provider logs the actions for
        audit and financial tracking.

        Args:
            request: AI request

        Returns:
            AI response
        """
        model = request.model or "claude-3-5-sonnet-latest"

        # For now, we track Claude actions through the audit system
        # The actual execution happens through Claude Code CLI
        # This allows us to log costs and track performance

        # Estimate tokens and cost
        prompt_tokens = int(len(request.prompt) / 4)
        if request.system_message:
            prompt_tokens += int(len(request.system_message) / 4)

        # For tracking purposes, we estimate completion
        completion_tokens = request.max_tokens or 2000

        tokens_used = {
            "prompt": prompt_tokens,
            "completion": completion_tokens,
            "total": prompt_tokens + completion_tokens
        }

        cost = self.estimate_cost(request)

        # Track at HFT frequency (microseconds)
        start_us = int(time.time() * 1_000_000)
        if HFT_TRACKING:
            track_api_call(
                provider="anthropic",
                model=model.replace("-latest", ""),
                input_tokens=prompt_tokens,
                output_tokens=completion_tokens,
                latency_us=0  # Actual latency tracked externally
            )
        latency_us = int(time.time() * 1_000_000) - start_us

        return AIResponse(
            request_id=request.request_id,
            provider_type=AIProviderType.CLAUDE,
            content="[Claude execution tracked - see Claude Code CLI output]",
            model_used=model,
            tokens_used=tokens_used,
            cost=cost,
            latency_ms=latency_us / 1000,
            success=True,
            metadata={
                "note": "Claude executes through CLI - this tracks costs and actions",
                "action": request.action,
                "hft_tracked": HFT_TRACKING,
                **request.metadata
            }
        )

    def log_action(
        self,
        action: str,
        files_changed: int = 0,
        lines_added: int = 0,
        lines_removed: int = 0,
        tokens_used: Optional[int] = None,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """
        Log a Claude Code action for tracking

        Args:
            action: Action performed (e.g., "code_generation", "code_review")
            files_changed: Number of files modified
            lines_added: Lines of code added
            lines_removed: Lines of code removed
            tokens_used: Tokens used (if known)
            session_id: Session ID
            metadata: Additional metadata
        """
        # Estimate cost based on code changes if tokens not provided
        if tokens_used is None:
            # Rough estimate: lines of code ≈ tokens
            tokens_used = (lines_added + lines_removed) * 5

        # Estimate cost using Sonnet pricing
        pricing = self.PRICING["claude-3-5-sonnet-latest"]
        input_cost = (tokens_used / 1_000_000) * pricing["input"]
        output_cost = (tokens_used / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost

        # Log to audit system
        self.audit_logger.log_event(
            component="ai.claude",
            action=action,
            metadata={
                "files_changed": files_changed,
                "lines_added": lines_added,
                "lines_removed": lines_removed,
                "tokens_used": tokens_used,
                **(metadata or {})
            },
            cost=total_cost,
            outcome="success",
            session_id=session_id
        )

        # Log to ledger
        self.ledger.add_cost(
            component="ai.claude",
            action=action,
            amount=total_cost,
            session_id=session_id or self.audit_logger.session_id,
            metadata={
                "files_changed": files_changed,
                "lines_added": lines_added,
                "lines_removed": lines_removed,
                "tokens_used": tokens_used
            }
        )


# Standalone function for tri-agent session runner and alpha engine
def call_claude(
    agent_id: str,
    prior_messages: list,
    session_goal: str,
    model: str = "claude-3-5-sonnet-latest",
    max_tokens: int = 2048
) -> dict:
    """
    Call Claude backend for tri-agent session and alpha analysis.

    Args:
        agent_id: Agent identifier ("claude")
        prior_messages: List of prior messages in conversation
        session_goal: Description of session purpose
        model: Anthropic model to use
        max_tokens: Maximum tokens in response

    Returns:
        Dict with 'content', 'model', 'tokens' keys
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
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
        system_prompt = f"""You are Claude providing analysis for an autonomous trading system.

Session Goal: {session_goal}

Provide accurate, data-driven analysis. Be concise but thorough."""

        # Build conversation
        messages = []
        for msg in prior_messages[-10:]:  # Last 10 messages for context
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
                messages.append({"role": role, "content": content})

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
            "content": "[Claude backend unavailable - anthropic package not installed]",
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
