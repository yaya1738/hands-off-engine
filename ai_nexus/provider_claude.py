#!/usr/bin/env python3
"""
Claude AI Provider for AI Nexus
Integrates Anthropic's Claude models
"""
import os
from typing import Optional

from .nexus_core import AIProvider, AIProviderType, AIRequest, AIResponse
from audit import AuditLogger, FinancialLedger


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

        return AIResponse(
            request_id=request.request_id,
            provider_type=AIProviderType.CLAUDE,
            content="[Claude execution tracked - see Claude Code CLI output]",
            model_used=model,
            tokens_used=tokens_used,
            cost=cost,
            latency_ms=0.0,  # Tracked externally
            success=True,
            metadata={
                "note": "Claude executes through CLI - this tracks costs and actions",
                "action": request.action,
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


# Wrapper function for backward compatibility with tri_agent_session_runner
def call_claude(prompt: str, system_message: Optional[str] = None, model: str = "claude-3-5-sonnet-latest") -> str:
    """
    Simple wrapper to call Claude without needing audit setup.

    Args:
        prompt: The user prompt
        system_message: Optional system message
        model: Model to use (default: claude-3-5-sonnet-latest)

    Returns:
        Response text from Claude
    """
    import os

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "[Error: ANTHROPIC_API_KEY not set - Claude runs via CLI in this system]"

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        kwargs = {
            "model": model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_message:
            kwargs["system"] = system_message

        response = client.messages.create(**kwargs)

        return response.content[0].text

    except ImportError:
        return "[Error: anthropic package not installed]"
    except Exception as e:
        return f"[Error calling Claude: {e}]"
