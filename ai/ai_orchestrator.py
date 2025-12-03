#!/usr/bin/env python3
"""
AI ORCHESTRATOR - INTEGRAFIX BRIDGE #2

Routes requests between autonomous systems and knowledge bases.

Before: 96 autonomous scripts make decisions in isolation, never consulting knowledge
After:  Central orchestrator routes all requests through knowledge bases

Connects:
- autonomous/*.py → ai_nexus/memory_kernels.py
- autonomous/*.py → ai_nexus/feedback_loop.py
- Decision requests → Knowledge consultation → Informed responses

Serving: Yair Siegel
"""

import json
import sys
import uuid
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum

# Add project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"
KERNEL_DIR = PROJECT_ROOT / "ai_nexus" / "kernels"

# INTEGRAFIX: Wire in AI memory system for cross-session persistence
try:
    from integrafix.ai_memory import get_memory, MemoryType, MemoryPriority
    AI_MEMORY_AVAILABLE = True
except ImportError:
    AI_MEMORY_AVAILABLE = False


class RequestType(Enum):
    """Types of requests the orchestrator handles."""
    TRADING_DECISION = "trading_decision"
    RISK_ASSESSMENT = "risk_assessment"
    MARKET_ANALYSIS = "market_analysis"
    SYSTEM_HEALTH = "system_health"
    LEARNING_UPDATE = "learning_update"
    GENERAL_QUERY = "general_query"


@dataclass
class AIRequest:
    """Request to the AI orchestrator."""
    request_id: str = field(default_factory=lambda: f"REQ-{str(uuid.uuid4())[:8]}")
    source: str = "unknown"  # Which module is asking
    request_type: str = "general_query"
    context: Dict = field(default_factory=dict)
    kernels_needed: List[str] = field(default_factory=list)
    deadline_seconds: int = 30
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AIResponse:
    """Response from the AI orchestrator."""
    request_id: str
    status: str  # success, error, timeout
    response: Dict = field(default_factory=dict)
    kernels_consulted: List[str] = field(default_factory=list)
    confidence: float = 0.5
    elapsed_ms: int = 0
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AIOrchestrator:
    """
    Central AI coordination system.

    Routes requests between autonomous systems and knowledge bases.
    Ensures all decisions are informed by relevant kernels.
    Records decision flow for learning.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self.state_file = STATE_DIR / "ai_orchestrator_state.json"
        self.log_file = STATE_DIR / "ai_orchestrator_log.jsonl"
        self.state = self._load_state()
        self.kernels: Dict[str, Dict] = {}
        self.memory = None

        # Ensure directories
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        KERNEL_DIR.mkdir(parents=True, exist_ok=True)

        # Load available kernels
        self._load_kernels()

        # INTEGRAFIX: Initialize AI memory for cross-session persistence
        if AI_MEMORY_AVAILABLE:
            try:
                self.memory = get_memory(session_id=f"orchestrator_{datetime.now().strftime('%Y%m%d')}")
                self._load_memories_into_context()
            except Exception:
                pass

    def _load_memories_into_context(self):
        """Load relevant memories from previous sessions into current context."""
        if not self.memory:
            return

        try:
            # Load learnings about trading decisions
            trading_memories = self.memory.recall_about("trading", limit=5)
            for mem in trading_memories:
                if "edge" in mem.content.lower() or "threshold" in mem.content.lower():
                    # Apply learned edge thresholds
                    if "alpha_polymarket_core" in self.kernels:
                        # Just log that we loaded the memory
                        pass

            # Load error memories to avoid repeating mistakes
            error_memories = self.memory.recall_errors(limit=3)
            self.state["recent_error_memories"] = len(error_memories)

            # Load success memories
            success_memories = self.memory.recall(memory_type=MemoryType.SUCCESS, limit=3)
            self.state["recent_success_memories"] = len(success_memories)
        except Exception:
            pass

    def _remember_decision(self, request: AIRequest, response: AIResponse):
        """Record a decision to memory for future sessions."""
        if not self.memory or response.status != "success":
            return

        try:
            # Only record significant trading decisions
            if request.request_type == RequestType.TRADING_DECISION.value:
                resp_data = response.response
                if resp_data.get("should_trade"):
                    self.memory.remember_decision(
                        decision=f"Trade {resp_data.get('recommended_action', 'unknown')} with size {resp_data.get('position_size', 0)}",
                        reasoning=resp_data.get("reasoning", ""),
                        outcome=""  # Will be updated when outcome is known
                    )

            # Record learning updates
            elif request.request_type == RequestType.LEARNING_UPDATE.value:
                updates = response.response.get("updates_applied", [])
                if updates:
                    self.memory.remember_learning(
                        what_learned=f"Applied updates: {', '.join(updates)}",
                        how_learned=f"Learning update from {request.source}"
                    )
        except Exception:
            pass

    def _load_state(self) -> Dict:
        """Load orchestrator state."""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except:
                pass
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "requests_processed": 0,
            "successful_requests": 0,
            "failed_requests": 0
        }

    def _save_state(self):
        """Save orchestrator state."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def _load_kernels(self):
        """Load all available knowledge kernels."""
        self.kernels = {}

        # Load from ai_nexus/kernels/
        if KERNEL_DIR.exists():
            for kf in KERNEL_DIR.glob("*.json"):
                try:
                    self.kernels[kf.stem] = json.loads(kf.read_text())
                except:
                    pass

        # Load from ai_nexus/memory_kernels.py if available
        try:
            from ai_nexus.memory_kernels import load_kernel, list_kernels
            for kernel_name in list_kernels():
                try:
                    kernel = load_kernel(kernel_name)
                    # Convert MemoryKernel objects to dict if needed
                    if hasattr(kernel, 'to_dict'):
                        self.kernels[kernel_name] = kernel.to_dict()
                    elif hasattr(kernel, '__dict__'):
                        self.kernels[kernel_name] = vars(kernel)
                    elif isinstance(kernel, dict):
                        self.kernels[kernel_name] = kernel
                    else:
                        # Try to get attributes as dict
                        self.kernels[kernel_name] = {
                            "name": kernel_name,
                            "data": str(kernel)[:200]
                        }
                except:
                    pass
        except ImportError:
            pass

        # Ensure kernels are dicts, not objects
        for name, kernel in list(self.kernels.items()):
            if not isinstance(kernel, dict):
                if hasattr(kernel, 'to_dict'):
                    self.kernels[name] = kernel.to_dict()
                elif hasattr(kernel, '__dict__'):
                    self.kernels[name] = dict(vars(kernel))
                else:
                    self.kernels[name] = {"name": name, "data": str(kernel)[:200]}

        # Create default kernels if none exist
        if not self.kernels:
            self._create_default_kernels()

    def _create_default_kernels(self):
        """Create default knowledge kernels."""
        default_kernels = {
            "risk_model_v2": {
                "name": "Risk Model V2",
                "description": "Risk assessment parameters",
                "max_position_size": 10.0,
                "max_daily_loss": 50.0,
                "risk_per_trade": 0.02,
                "current_risk_level": 0.5,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            "alpha_polymarket_core": {
                "name": "Alpha Polymarket Core",
                "description": "Polymarket trading knowledge",
                "min_edge_threshold": 0.10,
                "max_confidence": 0.85,
                "preferred_categories": ["politics", "crypto", "sports"],
                "latest_edge": 0.15,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            "trading_params": {
                "name": "Trading Parameters",
                "description": "Dynamic trading parameters",
                "base_position_size": 2.0,
                "edge_multiplier": 1.0,
                "confidence_threshold": 0.5,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        }

        for name, data in default_kernels.items():
            self.kernels[name] = data
            kernel_file = KERNEL_DIR / f"{name}.json"
            with open(kernel_file, "w") as f:
                json.dump(data, f, indent=2)

    def route_request(self, request: AIRequest) -> AIResponse:
        """
        Route a request to appropriate knowledge bases.

        This is the main entry point for all AI consultations.
        """
        start_time = datetime.now(timezone.utc)

        with self._lock:
            self.state["requests_processed"] = self.state.get("requests_processed", 0) + 1

        try:
            # Determine which kernels to consult
            kernels_to_consult = request.kernels_needed or self._select_kernels(request)

            # Load kernel data
            kernel_data = {}
            for kernel_name in kernels_to_consult:
                if kernel_name in self.kernels:
                    kernel_data[kernel_name] = self.kernels[kernel_name]

            # Route based on request type
            if request.request_type == RequestType.TRADING_DECISION.value:
                response_data = self._handle_trading_decision(request, kernel_data)
            elif request.request_type == RequestType.RISK_ASSESSMENT.value:
                response_data = self._handle_risk_assessment(request, kernel_data)
            elif request.request_type == RequestType.MARKET_ANALYSIS.value:
                response_data = self._handle_market_analysis(request, kernel_data)
            elif request.request_type == RequestType.SYSTEM_HEALTH.value:
                response_data = self._handle_system_health(request, kernel_data)
            elif request.request_type == RequestType.LEARNING_UPDATE.value:
                response_data = self._handle_learning_update(request, kernel_data)
            else:
                response_data = self._handle_general_query(request, kernel_data)

            # Calculate elapsed time
            elapsed_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

            # Build response
            response = AIResponse(
                request_id=request.request_id,
                status="success",
                response=response_data,
                kernels_consulted=list(kernel_data.keys()),
                confidence=response_data.get("confidence", 0.5),
                elapsed_ms=elapsed_ms
            )

            with self._lock:
                self.state["successful_requests"] = self.state.get("successful_requests", 0) + 1

        except Exception as e:
            elapsed_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            response = AIResponse(
                request_id=request.request_id,
                status="error",
                error=str(e),
                elapsed_ms=elapsed_ms
            )

            with self._lock:
                self.state["failed_requests"] = self.state.get("failed_requests", 0) + 1

        # Log request/response
        self._log_interaction(request, response)

        # INTEGRAFIX: Record decision to AI memory for cross-session learning
        self._remember_decision(request, response)

        self._save_state()

        return response

    def _select_kernels(self, request: AIRequest) -> List[str]:
        """Select appropriate kernels based on request type."""
        kernel_map = {
            RequestType.TRADING_DECISION.value: ["alpha_polymarket_core", "risk_model_v2", "trading_params"],
            RequestType.RISK_ASSESSMENT.value: ["risk_model_v2"],
            RequestType.MARKET_ANALYSIS.value: ["alpha_polymarket_core"],
            RequestType.SYSTEM_HEALTH.value: ["risk_model_v2"],
            RequestType.LEARNING_UPDATE.value: ["trading_params", "alpha_polymarket_core"],
            RequestType.GENERAL_QUERY.value: list(self.kernels.keys())[:3]
        }
        return kernel_map.get(request.request_type, [])

    def _handle_trading_decision(self, request: AIRequest, kernels: Dict) -> Dict:
        """Handle trading decision request."""
        alpha_kernel = kernels.get("alpha_polymarket_core", {})
        risk_kernel = kernels.get("risk_model_v2", {})
        params_kernel = kernels.get("trading_params", {})

        context = request.context

        # Extract market info from context
        market_price = context.get("market_price", 0.5)
        estimated_price = context.get("estimated_price", market_price)
        edge = (estimated_price - market_price) / market_price if market_price > 0 else 0

        # Get thresholds from kernels
        min_edge = alpha_kernel.get("min_edge_threshold", 0.10)
        max_position = risk_kernel.get("max_position_size", 10.0)
        base_size = params_kernel.get("base_position_size", 2.0)

        # Make decision
        should_trade = abs(edge) >= min_edge
        recommended_action = "buy" if edge > 0 else ("sell" if edge < -min_edge else "hold")

        # Calculate position size
        if should_trade:
            edge_multiplier = min(2.0, 1.0 + abs(edge))
            position_size = min(base_size * edge_multiplier, max_position)
        else:
            position_size = 0

        confidence = min(0.85, 0.5 + abs(edge) * 0.5) if should_trade else 0.3

        return {
            "recommended_action": recommended_action,
            "should_trade": should_trade,
            "position_size": round(position_size, 2),
            "edge": edge,
            "confidence": confidence,
            "risk_score": risk_kernel.get("current_risk_level", 0.5),
            "reasoning": f"Edge {edge:.1%} vs threshold {min_edge:.1%}"
        }

    def _handle_risk_assessment(self, request: AIRequest, kernels: Dict) -> Dict:
        """Handle risk assessment request."""
        risk_kernel = kernels.get("risk_model_v2", {})
        context = request.context

        current_exposure = context.get("current_exposure", 0)
        max_daily_loss = risk_kernel.get("max_daily_loss", 50.0)
        risk_per_trade = risk_kernel.get("risk_per_trade", 0.02)

        # Calculate risk metrics
        exposure_ratio = current_exposure / max_daily_loss if max_daily_loss > 0 else 0
        risk_level = min(1.0, exposure_ratio)

        can_trade = exposure_ratio < 0.8
        max_new_position = (max_daily_loss - current_exposure) * risk_per_trade if can_trade else 0

        return {
            "risk_level": risk_level,
            "can_trade": can_trade,
            "current_exposure": current_exposure,
            "max_new_position": round(max_new_position, 2),
            "exposure_ratio": round(exposure_ratio, 2),
            "confidence": 0.8
        }

    def _handle_market_analysis(self, request: AIRequest, kernels: Dict) -> Dict:
        """Handle market analysis request."""
        alpha_kernel = kernels.get("alpha_polymarket_core", {})
        context = request.context

        market_category = context.get("category", "unknown")
        preferred = alpha_kernel.get("preferred_categories", [])

        is_preferred = market_category.lower() in [c.lower() for c in preferred]
        category_bonus = 0.1 if is_preferred else 0

        return {
            "category": market_category,
            "is_preferred_category": is_preferred,
            "category_bonus": category_bonus,
            "latest_edge": alpha_kernel.get("latest_edge", 0.15),
            "confidence": 0.7
        }

    def _handle_system_health(self, request: AIRequest, kernels: Dict) -> Dict:
        """Handle system health check request."""
        risk_kernel = kernels.get("risk_model_v2", {})

        # Check system health indicators
        health_score = 1.0

        # Check error rates (would integrate with error_management in production)
        recent_errors = 0  # Placeholder

        if recent_errors > 10:
            health_score *= 0.5

        risk_level = risk_kernel.get("current_risk_level", 0.5)
        if risk_level > 0.8:
            health_score *= 0.7

        return {
            "health_score": health_score,
            "status": "healthy" if health_score > 0.7 else "degraded",
            "risk_level": risk_level,
            "recent_errors": recent_errors,
            "confidence": 0.9
        }

    def _handle_learning_update(self, request: AIRequest, kernels: Dict) -> Dict:
        """Handle learning update request."""
        context = request.context

        # Extract learnings
        learnings = context.get("learnings", [])

        updates_applied = []
        for learning in learnings:
            if isinstance(learning, dict):
                learning_type = learning.get("type")
                value = learning.get("value")

                if learning_type == "execution_success_rate" and value is not None:
                    # Update trading params based on success rate
                    if "trading_params" in self.kernels:
                        if value < 0.5:
                            self.kernels["trading_params"]["base_position_size"] *= 0.9
                            updates_applied.append("reduced base_position_size")
                        elif value > 0.8:
                            self.kernels["trading_params"]["base_position_size"] *= 1.1
                            updates_applied.append("increased base_position_size")

        # Save updated kernels
        for name, data in self.kernels.items():
            if name in ["trading_params", "alpha_polymarket_core", "risk_model_v2"]:
                kernel_file = KERNEL_DIR / f"{name}.json"
                data["last_updated"] = datetime.now(timezone.utc).isoformat()
                with open(kernel_file, "w") as f:
                    json.dump(data, f, indent=2)

        return {
            "updates_applied": updates_applied,
            "kernels_updated": len(updates_applied),
            "confidence": 0.8
        }

    def _handle_general_query(self, request: AIRequest, kernels: Dict) -> Dict:
        """Handle general query request."""
        return {
            "available_kernels": list(self.kernels.keys()),
            "kernel_count": len(self.kernels),
            "context_received": bool(request.context),
            "confidence": 0.5
        }

    def _log_interaction(self, request: AIRequest, response: AIResponse):
        """Log request/response for auditing."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request": asdict(request),
            "response": asdict(response)
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def get_kernel(self, kernel_name: str) -> Optional[Dict]:
        """Get a specific kernel."""
        return self.kernels.get(kernel_name)

    def update_kernel(self, kernel_name: str, updates: Dict):
        """Update a kernel with new data."""
        if kernel_name in self.kernels:
            self.kernels[kernel_name].update(updates)
            self.kernels[kernel_name]["last_updated"] = datetime.now(timezone.utc).isoformat()

            kernel_file = KERNEL_DIR / f"{kernel_name}.json"
            with open(kernel_file, "w") as f:
                json.dump(self.kernels[kernel_name], f, indent=2)


# Singleton instance for easy access
_orchestrator_instance: Optional[AIOrchestrator] = None


def get_orchestrator() -> AIOrchestrator:
    """Get the global orchestrator instance."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AIOrchestrator()
    return _orchestrator_instance


def consult(
    source: str,
    request_type: str,
    context: Dict = None,
    kernels: List[str] = None
) -> Dict:
    """
    Convenience function for consulting the orchestrator.

    Usage in autonomous scripts:
        from ai.ai_orchestrator import consult

        response = consult(
            source="evolution_engine",
            request_type="trading_decision",
            context={"market_price": 0.05, "estimated_price": 0.08}
        )

        if response["status"] == "success":
            guidance = response["response"]
            # Use guidance to make informed decision
    """
    orchestrator = get_orchestrator()

    request = AIRequest(
        source=source,
        request_type=request_type,
        context=context or {},
        kernels_needed=kernels or []
    )

    response = orchestrator.route_request(request)
    return asdict(response)


def main():
    """Demo the AI orchestrator."""
    print("=" * 70)
    print("AI ORCHESTRATOR - INTEGRAFIX BRIDGE #2")
    print("=" * 70)

    orchestrator = AIOrchestrator()

    print(f"\nLoaded {len(orchestrator.kernels)} kernels:")
    for name in orchestrator.kernels:
        print(f"  - {name}")

    # Test trading decision
    print("\n" + "-" * 70)
    print("Test 1: Trading Decision")
    print("-" * 70)

    request = AIRequest(
        source="market_data_pipeline",
        request_type="trading_decision",
        context={
            "market_price": 0.05,
            "estimated_price": 0.075,
            "market_slug": "test-market"
        }
    )

    response = orchestrator.route_request(request)
    print(f"Status: {response.status}")
    print(f"Kernels consulted: {response.kernels_consulted}")
    print(f"Response: {json.dumps(response.response, indent=2)}")

    # Test risk assessment
    print("\n" + "-" * 70)
    print("Test 2: Risk Assessment")
    print("-" * 70)

    request = AIRequest(
        source="trading_hub",
        request_type="risk_assessment",
        context={"current_exposure": 25.0}
    )

    response = orchestrator.route_request(request)
    print(f"Status: {response.status}")
    print(f"Response: {json.dumps(response.response, indent=2)}")

    # Test system health
    print("\n" + "-" * 70)
    print("Test 3: System Health")
    print("-" * 70)

    request = AIRequest(
        source="system_monitor",
        request_type="system_health",
        context={}
    )

    response = orchestrator.route_request(request)
    print(f"Status: {response.status}")
    print(f"Response: {json.dumps(response.response, indent=2)}")

    print("\n" + "=" * 70)
    print(f"Orchestrator state saved to: {orchestrator.state_file}")
    print(f"Interaction log: {orchestrator.log_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()
