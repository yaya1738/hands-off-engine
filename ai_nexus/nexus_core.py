#!/usr/bin/env python3
"""
Core AI Nexus orchestration system
Routes AI requests through audit system and tracks performance
"""
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from audit import AuditLogger, FinancialLedger


class AIProviderType(Enum):
    """Supported AI providers"""
    CLAUDE = "claude"
    OPENAI = "openai"
    COPILOT = "copilot"


@dataclass
class AIRequest:
    """Request to an AI provider"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    provider_type: AIProviderType = AIProviderType.OPENAI
    action: str = "completion"
    prompt: str = ""
    system_message: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.3
    max_tokens: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AIResponse:
    """Response from an AI provider"""
    request_id: str
    provider_type: AIProviderType
    content: str
    model_used: str
    tokens_used: Dict[str, int]  # {"prompt": N, "completion": M, "total": T}
    cost: float  # Estimated cost in USD
    latency_ms: float
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AIProvider(ABC):
    """
    Abstract base class for AI providers
    All providers must implement this interface
    """

    def __init__(self, audit_logger: AuditLogger, ledger: FinancialLedger):
        self.audit_logger = audit_logger
        self.ledger = ledger

    @abstractmethod
    def execute(self, request: AIRequest) -> AIResponse:
        """Execute an AI request and return response"""
        pass

    @abstractmethod
    def estimate_cost(self, request: AIRequest) -> float:
        """Estimate cost for a request before execution"""
        pass

    @abstractmethod
    def get_provider_type(self) -> AIProviderType:
        """Get the provider type"""
        pass


class NexusCore:
    """
    Core orchestration system for AI Nexus

    Features:
    - Routes requests to appropriate AI providers
    - Comprehensive audit logging
    - Financial tracking (costs and revenues)
    - Performance monitoring
    - Self-improvement recommendations
    - Budget management
    """

    def __init__(
        self,
        audit_logger: Optional[AuditLogger] = None,
        ledger: Optional[FinancialLedger] = None
    ):
        self.audit_logger = audit_logger or AuditLogger()
        self.ledger = ledger or FinancialLedger()
        self.providers: Dict[AIProviderType, AIProvider] = {}
        self.session_id = self.audit_logger.session_id

    def register_provider(self, provider: AIProvider):
        """Register an AI provider with the nexus"""
        provider_type = provider.get_provider_type()
        self.providers[provider_type] = provider

        self.audit_logger.log_event(
            component="ai_nexus.core",
            action="register_provider",
            metadata={"provider": provider_type.value}
        )

    def execute_request(self, request: AIRequest) -> AIResponse:
        """
        Execute an AI request through the nexus

        This method:
        1. Routes to appropriate provider
        2. Logs the request
        3. Executes the request
        4. Records costs in ledger
        5. Logs the response
        6. Returns the response
        """
        # Ensure session_id is set
        if not request.session_id:
            request.session_id = self.session_id

        # Get provider
        provider = self.providers.get(request.provider_type)
        if not provider:
            error_msg = f"Provider {request.provider_type.value} not registered"
            self.audit_logger.log_event(
                component="ai_nexus.core",
                action="execute_request",
                metadata={"error": error_msg},
                error=error_msg,
                session_id=request.session_id
            )
            return AIResponse(
                request_id=request.request_id,
                provider_type=request.provider_type,
                content="",
                model_used="",
                tokens_used={"prompt": 0, "completion": 0, "total": 0},
                cost=0.0,
                latency_ms=0.0,
                success=False,
                error=error_msg
            )

        # Log request start
        start_time = time.time()
        self.audit_logger.log_event(
            component=f"ai_nexus.{request.provider_type.value}",
            action=f"request_start_{request.action}",
            metadata={
                "request_id": request.request_id,
                "model": request.model,
                "temperature": request.temperature,
                "prompt_length": len(request.prompt),
                **request.metadata
            },
            session_id=request.session_id
        )

        # Execute request
        try:
            response = provider.execute(request)
            latency_ms = (time.time() - start_time) * 1000
            response.latency_ms = latency_ms

            # Record cost in ledger
            if response.cost > 0:
                self.ledger.add_cost(
                    component=f"ai.{request.provider_type.value}",
                    action=request.action,
                    amount=response.cost,
                    session_id=request.session_id,
                    metadata={
                        "request_id": request.request_id,
                        "model": response.model_used,
                        "tokens": response.tokens_used
                    }
                )

            # Log response
            self.audit_logger.log_event(
                component=f"ai_nexus.{request.provider_type.value}",
                action=f"request_complete_{request.action}",
                metadata={
                    "request_id": request.request_id,
                    "model": response.model_used,
                    "tokens": response.tokens_used,
                    "latency_ms": latency_ms,
                    "content_length": len(response.content)
                },
                cost=response.cost,
                outcome="success" if response.success else "error",
                error=response.error,
                session_id=request.session_id
            )

            return response

        except Exception as e:
            error_msg = str(e)
            latency_ms = (time.time() - start_time) * 1000

            # Log error
            self.audit_logger.log_event(
                component=f"ai_nexus.{request.provider_type.value}",
                action=f"request_error_{request.action}",
                metadata={
                    "request_id": request.request_id,
                    "latency_ms": latency_ms
                },
                error=error_msg,
                session_id=request.session_id
            )

            return AIResponse(
                request_id=request.request_id,
                provider_type=request.provider_type,
                content="",
                model_used=request.model or "",
                tokens_used={"prompt": 0, "completion": 0, "total": 0},
                cost=0.0,
                latency_ms=latency_ms,
                success=False,
                error=error_msg
            )

    def record_revenue(
        self,
        component: str,
        action: str,
        amount: float,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record revenue generated by AI-driven actions

        Args:
            component: Component generating revenue (e.g., "trading.polymarket")
            action: Action that generated revenue
            amount: Revenue amount in USD
            session_id: Optional session ID
            metadata: Additional context
        """
        sid = session_id or self.session_id

        # Add to ledger
        self.ledger.add_revenue(
            component=component,
            action=action,
            amount=amount,
            session_id=sid,
            metadata=metadata or {}
        )

        # Log the event
        self.audit_logger.log_event(
            component=component,
            action=action,
            metadata=metadata or {},
            revenue=amount,
            outcome="success",
            session_id=sid
        )

    def get_session_metrics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive metrics for a session

        Returns:
            Dictionary with audit and financial metrics
        """
        sid = session_id or self.session_id

        # Get audit summary
        audit_summary = self.audit_logger.get_session_summary(sid)

        # Get financial summary
        financial_summary = self.ledger.get_balance(sid)

        # Get component performance
        component_perf = self.ledger.get_component_performance()

        return {
            "session_id": sid,
            "audit": audit_summary,
            "financial": financial_summary,
            "component_performance": component_perf,
            "recommendations": self._generate_recommendations(audit_summary, financial_summary)
        }

    def _generate_recommendations(
        self,
        audit_summary: Dict[str, Any],
        financial_summary: Dict[str, Any]
    ) -> List[str]:
        """
        Generate self-improvement recommendations based on metrics

        Args:
            audit_summary: Audit statistics
            financial_summary: Financial statistics

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Check profitability
        roi = financial_summary.get("roi_percent", 0)
        if roi < 0:
            recommendations.append(
                f"⚠️  Session is unprofitable (ROI: {roi:.1f}%). "
                "Consider reducing AI costs or increasing revenue-generating activities."
            )
        elif roi > 100:
            recommendations.append(
                f"✅ Session is highly profitable (ROI: {roi:.1f}%). "
                "Consider increasing AI budget to scale successful strategies."
            )

        # Check for errors
        total_events = audit_summary.get("total_events", 0)
        if total_events > 0:
            for component, stats in audit_summary.get("component_stats", {}).items():
                error_rate = stats["errors"] / stats["event_count"] * 100
                if error_rate > 10:
                    recommendations.append(
                        f"⚠️  High error rate in {component}: {error_rate:.1f}%. "
                        "Investigate and fix issues."
                    )

        # Cost efficiency check
        total_costs = financial_summary.get("total_costs", 0)
        if total_costs > 100:
            recommendations.append(
                "💡 High AI costs detected. Consider using cheaper models for "
                "non-critical tasks or implementing caching."
            )

        return recommendations

    def verify_ledger_integrity(self) -> bool:
        """
        Verify financial ledger integrity

        Returns:
            True if ledger is intact, False if tampered
        """
        return self.ledger.verify_integrity()
