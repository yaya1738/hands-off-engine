#!/usr/bin/env python3
"""
LLM Market Analyst

Main interface for LLM-driven market analysis.
Integrates backend selection, prompt routing, and structured output parsing.

Usage:
    analyst = LLMMarketAnalyst()
    opinion = analyst.analyze_market(market_dict)

The analyst:
1. Selects appropriate backend via backend_selector
2. Routes to category-specific prompt
3. Calls LLM API (or falls back to naive model)
4. Parses and validates JSON response
5. Returns structured Opinion with fair_probability, edge, action
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, Any, Optional

from .backend_selector import Backend, LLMBackend, TaskType, Priority
from .prompt_library import get_prompt_for_market


@dataclass
class LLMOpinion:
    """
    Structured output from LLM market analysis.

    Fields match expected JSON schema from prompts.
    """
    fair_probability: float  # 0-100% probability of YES outcome
    confidence: str          # "low", "medium", "high"
    edge_bps: int           # Basis points edge vs market
    reasoning: str          # 1-2 sentence explanation
    action: str             # "buy_yes", "buy_no", "avoid"

    # Metadata
    backend_used: str       # Which LLM backend was used
    model_name: str         # Specific model (e.g., "claude-sonnet-4")
    prompt_version: str     # Prompt version for tracking
    tokens_used: Optional[int] = None  # Token count if available

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization"""
        return {
            "fair_probability": self.fair_probability,
            "confidence": self.confidence,
            "edge_bps": self.edge_bps,
            "reasoning": self.reasoning,
            "action": self.action,
            "backend_used": self.backend_used,
            "model_name": self.model_name,
            "prompt_version": self.prompt_version,
            "tokens_used": self.tokens_used,
        }

    def to_opinion_format(self) -> Dict[str, Any]:
        """
        Convert to format compatible with polymarket_skeleton Opinion.

        Returns dict with keys: fair_yes, edge, rec, notes
        """
        return {
            "fair_yes": self.fair_probability / 100.0,  # Convert 0-100 to 0-1
            "edge": self.edge_bps / 10000.0,  # Convert bps to decimal
            "rec": self.action.replace("_", " "),  # "buy_yes" -> "buy yes"
            "notes": f"LLM ({self.backend_used}, {self.confidence} confidence): {self.reasoning}",
        }


class LLMMarketAnalyst:
    """
    Main LLM Market Analyst class.

    Provides unified interface for LLM-based market analysis with:
    - Automatic backend selection
    - Category-specific prompting
    - Graceful fallback to naive model
    - Structured output validation
    - Cost tracking
    """

    def __init__(
        self,
        default_priority: Priority = Priority.QUALITY,
        enable_fallback: bool = True,
        dry_run: bool = True,  # DRYRUN mode - log only, no real API calls
    ):
        """
        Initialize LLM Market Analyst.

        Args:
            default_priority: Default priority for backend selection
            enable_fallback: Whether to fall back to naive model if LLM fails
            dry_run: If True, simulate LLM calls without real API requests
        """
        self.backend_selector = LLMBackend(default_priority=default_priority)
        self.enable_fallback = enable_fallback
        self.dry_run = dry_run

        # Check if we have any LLM backends available
        self.has_llm_backend = len(self.backend_selector.list_available_backends()) > 0

        if not self.has_llm_backend:
            print("[LLMMarketAnalyst] WARNING: No LLM backends available (missing API keys)")
            print("[LLMMarketAnalyst] Will fall back to naive model")

    def analyze_market(
        self,
        market_data: Dict[str, Any],
        priority: Optional[Priority] = None,
    ) -> Optional[LLMOpinion]:
        """
        Analyze a market using LLM.

        Args:
            market_data: Market dict with keys: question, yes_price, category, etc.
            priority: Override default priority for this request

        Returns:
            LLMOpinion with structured analysis, or None if analysis fails
        """
        # Select backend
        backend = self.backend_selector.select_backend(
            task_type=TaskType.ANALYSIS,
            priority=priority,
        )

        # If no LLM backend, return None (caller should fall back)
        if backend == Backend.FALLBACK_NAIVE:
            return None

        # Get category-specific prompt
        prompt = get_prompt_for_market(market_data)

        # Call LLM (or simulate in dry-run mode)
        if self.dry_run:
            llm_response = self._simulate_llm_call(market_data, backend, prompt)
        else:
            llm_response = self._call_llm_api(backend, prompt, market_data)

        # Parse and validate response
        if llm_response:
            return self._parse_llm_response(llm_response, backend, market_data)

        return None

    def _simulate_llm_call(
        self,
        market_data: Dict[str, Any],
        backend: Backend,
        prompt: str,
    ) -> Optional[str]:
        """
        Simulate LLM call in DRYRUN mode.

        Returns a plausible JSON response based on market price.
        """
        # Log that we're simulating
        print(f"[LLMMarketAnalyst] DRYRUN: Simulating {backend.value} call")
        print(f"[LLMMarketAnalyst] Question: {market_data.get('question', 'N/A')[:80]}")

        # Generate synthetic response
        market_price = market_data.get("yes_price", 0.5) * 100

        # Add some noise to make it realistic
        import random
        fair_prob = max(5, min(95, market_price + random.uniform(-10, 10)))
        edge = int((fair_prob - market_price) * 100)

        if abs(edge) > 500:
            action = "buy_yes" if edge > 0 else "buy_no"
            confidence = "medium"
        else:
            action = "avoid"
            confidence = "low"

        # Return JSON string
        return json.dumps({
            "fair_probability": round(fair_prob, 1),
            "confidence": confidence,
            "edge_bps": edge,
            "reasoning": f"Simulated analysis for DRYRUN mode. Market at {market_price:.1f}%, estimate {fair_prob:.1f}%.",
            "action": action,
        })

    def _call_llm_api(
        self,
        backend: Backend,
        prompt: str,
        market_data: Dict[str, Any],
    ) -> Optional[str]:
        """
        Call actual LLM API.

        This is a stub that will be implemented when API keys are configured.
        Real implementation would use anthropic, openai, or openrouter SDKs.
        """
        # TODO: Implement real API calls
        # For now, just return None to trigger fallback
        print(f"[LLMMarketAnalyst] Real API calls not yet implemented for {backend.value}")
        print(f"[LLMMarketAnalyst] Would call API with prompt: {prompt[:100]}...")
        return None

    def _parse_llm_response(
        self,
        response: str,
        backend: Backend,
        market_data: Dict[str, Any],
    ) -> Optional[LLMOpinion]:
        """
        Parse and validate LLM JSON response.

        Args:
            response: Raw LLM response (should be JSON)
            backend: Backend that was used
            market_data: Original market data (for validation)

        Returns:
            LLMOpinion if parsing succeeds, None otherwise
        """
        try:
            # Parse JSON
            data = json.loads(response)

            # Validate required fields
            required = ["fair_probability", "confidence", "edge_bps", "reasoning", "action"]
            for field in required:
                if field not in data:
                    print(f"[LLMMarketAnalyst] Missing field in response: {field}")
                    return None

            # Validate types and ranges
            fair_prob = float(data["fair_probability"])
            if not (0 <= fair_prob <= 100):
                print(f"[LLMMarketAnalyst] Invalid fair_probability: {fair_prob}")
                return None

            confidence = str(data["confidence"]).lower()
            if confidence not in ["low", "medium", "high"]:
                print(f"[LLMMarketAnalyst] Invalid confidence: {confidence}")
                return None

            edge_bps = int(data["edge_bps"])

            action = str(data["action"]).lower()
            if action not in ["buy_yes", "buy_no", "avoid"]:
                print(f"[LLMMarketAnalyst] Invalid action: {action}")
                return None

            reasoning = str(data["reasoning"])

            # Create LLMOpinion
            return LLMOpinion(
                fair_probability=fair_prob,
                confidence=confidence,
                edge_bps=edge_bps,
                reasoning=reasoning,
                action=action,
                backend_used=backend.value,
                model_name=backend.value,  # TODO: Get actual model name from API
                prompt_version="v1.0.0",  # Match prompt_library version
                tokens_used=data.get("tokens_used"),  # Optional
            )

        except json.JSONDecodeError as e:
            print(f"[LLMMarketAnalyst] Failed to parse JSON: {e}")
            print(f"[LLMMarketAnalyst] Response: {response[:200]}")
            return None
        except (ValueError, KeyError, TypeError) as e:
            print(f"[LLMMarketAnalyst] Validation error: {e}")
            return None

    def get_status(self) -> Dict[str, Any]:
        """
        Get analyst status and available backends.

        Returns:
            Dict with backend availability, dry_run mode, etc.
        """
        return {
            "dry_run": self.dry_run,
            "has_llm_backend": self.has_llm_backend,
            "available_backends": [
                b.value for b in self.backend_selector.list_available_backends()
            ],
            "fallback_enabled": self.enable_fallback,
        }
