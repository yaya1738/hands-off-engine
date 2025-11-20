#!/usr/bin/env python3
"""
GitHub Copilot Provider for AI Nexus
Tracks Copilot actions and costs
"""
from typing import Optional

from .nexus_core import AIProvider, AIProviderType, AIRequest, AIResponse
from audit import AuditLogger, FinancialLedger


class CopilotProvider(AIProvider):
    """
    Provider for GitHub Copilot

    Pricing:
    - GitHub Copilot: $10/month per user (flat rate)
    - Estimated per-action cost: $0.01 (amortized from monthly fee)
    """

    COST_PER_ACTION = 0.01  # Amortized cost estimate

    def __init__(self, audit_logger: AuditLogger, ledger: FinancialLedger):
        super().__init__(audit_logger, ledger)

    def get_provider_type(self) -> AIProviderType:
        return AIProviderType.COPILOT

    def estimate_cost(self, request: AIRequest) -> float:
        """
        Estimate cost for Copilot action

        Since Copilot is a flat monthly fee, we use amortized cost

        Args:
            request: AI request

        Returns:
            Estimated cost in USD
        """
        return self.COST_PER_ACTION

    def execute(self, request: AIRequest) -> AIResponse:
        """
        Execute a Copilot request

        Note: This is a tracking wrapper. Actual Copilot execution happens
        through the GitHub Copilot extension. This provider logs the actions
        for audit and financial tracking.

        Args:
            request: AI request

        Returns:
            AI response
        """
        # Track Copilot actions through the audit system
        # The actual execution happens through GitHub Copilot extension

        return AIResponse(
            request_id=request.request_id,
            provider_type=AIProviderType.COPILOT,
            content="[Copilot execution tracked - see editor output]",
            model_used="copilot",
            tokens_used={"prompt": 0, "completion": 0, "total": 0},
            cost=self.COST_PER_ACTION,
            latency_ms=0.0,  # Tracked externally
            success=True,
            metadata={
                "note": "Copilot executes through editor extension - this tracks costs and actions",
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
        suggestions_accepted: int = 0,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """
        Log a Copilot action for tracking

        Args:
            action: Action performed (e.g., "code_completion", "code_suggestion")
            files_changed: Number of files modified
            lines_added: Lines of code added
            lines_removed: Lines of code removed
            suggestions_accepted: Number of suggestions accepted
            session_id: Session ID
            metadata: Additional metadata
        """
        # Use amortized cost
        cost = self.COST_PER_ACTION * max(1, suggestions_accepted)

        # Log to audit system
        self.audit_logger.log_event(
            component="ai.copilot",
            action=action,
            metadata={
                "files_changed": files_changed,
                "lines_added": lines_added,
                "lines_removed": lines_removed,
                "suggestions_accepted": suggestions_accepted,
                **(metadata or {})
            },
            cost=cost,
            outcome="success",
            session_id=session_id
        )

        # Log to ledger
        self.ledger.add_cost(
            component="ai.copilot",
            action=action,
            amount=cost,
            session_id=session_id or self.audit_logger.session_id,
            metadata={
                "files_changed": files_changed,
                "lines_added": lines_added,
                "lines_removed": lines_removed,
                "suggestions_accepted": suggestions_accepted
            }
        )
