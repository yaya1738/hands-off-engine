#!/usr/bin/env python3
"""
LLM Cost Tracker

Tracks token usage and simulated costs for LLM API calls.
DRYRUN-safe: tracks both real and simulated usage.

Supports:
- Anthropic Claude API pricing
- OpenRouter pricing (various models)
- Token usage aggregation per session
- Cost reporting and budgeting

Usage:
    tracker = CostTracker()
    tracker.track_call(
        model_name="claude-sonnet-4",
        tokens_in=250,
        tokens_out=150,
        backend="claude-api"
    )
    report = tracker.aggregate_session()
    tracker.export_cost_report(Path("state/llm_cost_report.json"))
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional


@dataclass
class TokenUsage:
    """Single API call token usage"""
    timestamp: str
    model_name: str
    backend: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionSummary:
    """Aggregated session statistics"""
    session_start: str
    session_end: str
    total_calls: int
    total_tokens_in: int
    total_tokens_out: int
    total_cost_usd: float
    calls_by_backend: Dict[str, int]
    calls_by_model: Dict[str, int]
    cost_by_backend: Dict[str, float]


# Pricing table (USD per 1M tokens)
PRICING_TABLE = {
    # Anthropic Claude
    "claude-api": {
        "claude-sonnet-4": {"input": 3.0, "output": 15.0},
        "claude-sonnet-3.5": {"input": 3.0, "output": 15.0},
        "claude-haiku": {"input": 0.25, "output": 1.25},
    },
    # OpenRouter
    "openrouter-gpt4": {
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-4": {"input": 30.0, "output": 60.0},
    },
    "openrouter-claude": {
        "claude-sonnet-4": {"input": 3.0, "output": 15.0},
    },
    "openrouter-llama": {
        "llama-3.1-70b": {"input": 0.35, "output": 0.40},
        "llama-3.1-8b": {"input": 0.06, "output": 0.06},
    },
    # Fallback/simulation
    "fallback-naive": {
        "naive": {"input": 0.0, "output": 0.0},
    },
    "simulation": {
        "dryrun": {"input": 0.0, "output": 0.0},
    },
}


class CostTracker:
    """
    LLM Cost Tracker

    Tracks token usage and costs across LLM API calls.
    Works in both DRYRUN and live modes.
    """

    def __init__(self):
        """Initialize cost tracker"""
        self.calls: List[TokenUsage] = []
        self.session_start = datetime.now(timezone.utc).isoformat()

    def track_call(
        self,
        model_name: str,
        tokens_in: int,
        tokens_out: int,
        backend: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Track a single LLM API call

        Args:
            model_name: Model identifier (e.g., "claude-sonnet-4")
            tokens_in: Input tokens (prompt)
            tokens_out: Output tokens (completion)
            backend: Backend identifier (e.g., "claude-api")
            metadata: Optional metadata dict

        Returns:
            Estimated cost in USD
        """
        # Calculate cost
        cost = self._calculate_cost(backend, model_name, tokens_in, tokens_out)

        # Record usage
        usage = TokenUsage(
            timestamp=datetime.now(timezone.utc).isoformat(),
            model_name=model_name,
            backend=backend,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost,
            metadata=metadata or {},
        )

        self.calls.append(usage)

        return cost

    def _calculate_cost(
        self,
        backend: str,
        model_name: str,
        tokens_in: int,
        tokens_out: int,
    ) -> float:
        """
        Calculate cost for a single call

        Args:
            backend: Backend identifier
            model_name: Model name
            tokens_in: Input tokens
            tokens_out: Output tokens

        Returns:
            Cost in USD
        """
        # Get pricing for backend and model
        backend_pricing = PRICING_TABLE.get(backend, {})
        model_pricing = backend_pricing.get(model_name)

        if not model_pricing:
            # Try to find a default for the backend
            if backend_pricing:
                model_pricing = list(backend_pricing.values())[0]
            else:
                # Fallback to zero cost
                return 0.0

        # Calculate cost
        # Pricing is per 1M tokens, so divide by 1,000,000
        cost_in = (tokens_in / 1_000_000) * model_pricing["input"]
        cost_out = (tokens_out / 1_000_000) * model_pricing["output"]

        return cost_in + cost_out

    def aggregate_session(self) -> SessionSummary:
        """
        Aggregate statistics for the current session

        Returns:
            SessionSummary with totals and breakdowns
        """
        if not self.calls:
            return SessionSummary(
                session_start=self.session_start,
                session_end=datetime.now(timezone.utc).isoformat(),
                total_calls=0,
                total_tokens_in=0,
                total_tokens_out=0,
                total_cost_usd=0.0,
                calls_by_backend={},
                calls_by_model={},
                cost_by_backend={},
            )

        # Aggregate totals
        total_calls = len(self.calls)
        total_tokens_in = sum(c.tokens_in for c in self.calls)
        total_tokens_out = sum(c.tokens_out for c in self.calls)
        total_cost = sum(c.cost_usd for c in self.calls)

        # Breakdown by backend
        calls_by_backend: Dict[str, int] = {}
        cost_by_backend: Dict[str, float] = {}
        for call in self.calls:
            calls_by_backend[call.backend] = calls_by_backend.get(call.backend, 0) + 1
            cost_by_backend[call.backend] = cost_by_backend.get(call.backend, 0.0) + call.cost_usd

        # Breakdown by model
        calls_by_model: Dict[str, int] = {}
        for call in self.calls:
            calls_by_model[call.model_name] = calls_by_model.get(call.model_name, 0) + 1

        return SessionSummary(
            session_start=self.session_start,
            session_end=datetime.now(timezone.utc).isoformat(),
            total_calls=total_calls,
            total_tokens_in=total_tokens_in,
            total_tokens_out=total_tokens_out,
            total_cost_usd=total_cost,
            calls_by_backend=calls_by_backend,
            calls_by_model=calls_by_model,
            cost_by_backend=cost_by_backend,
        )

    def export_cost_report(self, output_path: Path) -> None:
        """
        Export cost report to JSON file

        Args:
            output_path: Path to write JSON report
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build report
        summary = self.aggregate_session()

        report = {
            "summary": asdict(summary),
            "detailed_calls": [asdict(call) for call in self.calls],
        }

        # Write JSON
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    def reset(self) -> None:
        """Reset tracker for new session"""
        self.calls = []
        self.session_start = datetime.now(timezone.utc).isoformat()

    def get_total_cost(self) -> float:
        """Get total cost for current session"""
        return sum(c.cost_usd for c in self.calls)

    def get_total_tokens(self) -> int:
        """Get total tokens (in + out) for current session"""
        return sum(c.tokens_in + c.tokens_out for c in self.calls)

    def check_budget(self, budget_usd: float) -> Dict[str, Any]:
        """
        Check if session is within budget

        Args:
            budget_usd: Budget limit in USD

        Returns:
            Dict with budget status
        """
        total_cost = self.get_total_cost()
        remaining = budget_usd - total_cost
        percent_used = (total_cost / budget_usd * 100) if budget_usd > 0 else 0

        return {
            "budget_usd": budget_usd,
            "spent_usd": total_cost,
            "remaining_usd": remaining,
            "percent_used": percent_used,
            "over_budget": total_cost > budget_usd,
            "total_calls": len(self.calls),
        }
