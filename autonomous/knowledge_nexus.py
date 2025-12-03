#!/usr/bin/env python3
"""
Knowledge Nexus - System-Wide Knowledge Integration
====================================================

Connects knowledge bases to key system inflection points for maximum potential energy.

INFLECTION POINTS:
------------------
1. TRADING DECISIONS     → Money knowledge (NPV, risk, market structure)
2. INFRASTRUCTURE SCALING → Computing knowledge (optimization, distributed systems)
3. REVENUE OPTIMIZATION   → Business knowledge (economics, strategy)
4. REALITY ASSESSMENT     → All three (holistic understanding)
5. SELF-HEALING          → Computing knowledge (diagnostics, recovery)
6. STRATEGIC PLANNING    → Business + Money (growth, capital allocation)

Serving: Yair Siegel
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

NEXUS_STATE = STATE_DIR / "knowledge_nexus.json"


class KnowledgeNexus:
    """
    Central nexus connecting all knowledge bases to system decision points.

    Like a neural hub - routes relevant knowledge to where it's needed.
    """

    def __init__(self):
        self.master = "Yair Siegel"

        # Load saved state if exists
        saved_state = self._load_saved_state()

        self.initialized = saved_state.get(
            "initialized",
            datetime.now(timezone.utc).isoformat()
        )

        # Load knowledge bases
        self.computing = self._load_computing()
        self.business = self._load_business()
        self.money = self._load_money()

        # Track which systems are connected (restore from saved state)
        self.connections = saved_state.get("connections", {
            "trading": False,
            "infrastructure": False,
            "revenue": False,
            "reality": False,
            "self_healing": False,
            "strategic": False,
        })

        # Query counts from saved state
        self.query_counts = saved_state.get("query_counts", {})

    def _load_saved_state(self) -> Dict[str, Any]:
        """Load saved nexus state."""
        try:
            if NEXUS_STATE.exists():
                with open(NEXUS_STATE) as f:
                    return json.load(f)
        except:
            pass
        return {}

    def _load_computing(self) -> Dict[str, Any]:
        """Load computing knowledge base."""
        try:
            from executor.computing import (
                KNOWLEDGE_PATH,
                KNOWLEDGE_ADVANCED_PATH,
                COMPLEXITY_CLASSES,
                DATA_STRUCTURES,
                PARADIGMS,
                SORTING_ALGORITHMS,
                SEARCH_ALGORITHMS,
                estimate_time_complexity,
                get_complexity,
                get_data_structure_complexity,
            )
            return {
                "loaded": True,
                "knowledge_path": KNOWLEDGE_PATH,
                "advanced_path": KNOWLEDGE_ADVANCED_PATH,
                "complexity_classes": COMPLEXITY_CLASSES,
                "data_structures": DATA_STRUCTURES,
                "paradigms": PARADIGMS,
                "sorting_algorithms": SORTING_ALGORITHMS,
                "search_algorithms": SEARCH_ALGORITHMS,
                "estimate_time_complexity": estimate_time_complexity,
                "get_complexity": get_complexity,
                "get_data_structure_complexity": get_data_structure_complexity,
            }
        except Exception as e:
            return {"loaded": False, "error": str(e)}

    def _load_business(self) -> Dict[str, Any]:
        """Load business knowledge base."""
        try:
            from executor.business import (
                KNOWLEDGE_PATH,
                KNOWLEDGE_ADVANCED_PATH,
                BUSINESS_STRUCTURES,
                PRICING_STRATEGIES,
                STARTUP_METRICS,
                GENERIC_STRATEGIES,
                PORTER_FIVE_FORCES,
                FINANCIAL_RATIOS,
                calculate_ltv_cac_ratio,
                calculate_runway,
                calculate_npv,
                calculate_irr,
                calculate_wacc,
            )
            return {
                "loaded": True,
                "knowledge_path": KNOWLEDGE_PATH,
                "advanced_path": KNOWLEDGE_ADVANCED_PATH,
                "business_structures": BUSINESS_STRUCTURES,
                "pricing_strategies": PRICING_STRATEGIES,
                "startup_metrics": STARTUP_METRICS,
                "competitive_strategies": GENERIC_STRATEGIES,
                "porter_five_forces": PORTER_FIVE_FORCES,
                "financial_ratios": FINANCIAL_RATIOS,
                "calculate_ltv_cac_ratio": calculate_ltv_cac_ratio,
                "calculate_runway": calculate_runway,
                "calculate_npv": calculate_npv,
                "calculate_irr": calculate_irr,
                "calculate_wacc": calculate_wacc,
            }
        except Exception as e:
            return {"loaded": False, "error": str(e)}

    def _load_money(self) -> Dict[str, Any]:
        """Load money/finance knowledge base."""
        try:
            from executor.money import (
                KNOWLEDGE_PATH,
                KNOWLEDGE_ADVANCED_PATH,
                INTEREST_RATE_TYPES,
                ASSET_CLASSES,
                RISK_METRICS,
                MONEY_SUPPLY,
                calculate_compound_interest,
                calculate_npv,
                calculate_irr,
                calculate_bond_price,
                calculate_sharpe_ratio,
                calculate_wacc,
                calculate_loan_payment,
            )
            return {
                "loaded": True,
                "knowledge_path": KNOWLEDGE_PATH,
                "advanced_path": KNOWLEDGE_ADVANCED_PATH,
                "interest_rate_types": INTEREST_RATE_TYPES,
                "asset_classes": ASSET_CLASSES,
                "risk_metrics": RISK_METRICS,
                "money_supply": MONEY_SUPPLY,
                "calculate_compound_interest": calculate_compound_interest,
                "calculate_npv": calculate_npv,
                "calculate_irr": calculate_irr,
                "calculate_bond_price": calculate_bond_price,
                "calculate_sharpe_ratio": calculate_sharpe_ratio,
                "calculate_wacc": calculate_wacc,
                "calculate_loan_payment": calculate_loan_payment,
            }
        except Exception as e:
            return {"loaded": False, "error": str(e)}

    def status(self) -> Dict[str, Any]:
        """Get knowledge nexus status."""
        return {
            "master": self.master,
            "initialized": self.initialized,
            "knowledge_bases": {
                "computing": {
                    "loaded": self.computing.get("loaded", False),
                    "error": self.computing.get("error"),
                },
                "business": {
                    "loaded": self.business.get("loaded", False),
                    "error": self.business.get("error"),
                },
                "money": {
                    "loaded": self.money.get("loaded", False),
                    "error": self.money.get("error"),
                },
            },
            "connections": self.connections,
            "total_loaded": sum([
                self.computing.get("loaded", False),
                self.business.get("loaded", False),
                self.money.get("loaded", False),
            ]),
        }

    # ========== INFLECTION POINT 1: TRADING DECISIONS ==========

    def get_trading_context(self, market_data: Dict = None) -> Dict[str, Any]:
        """
        Provide knowledge context for trading decisions.

        Uses: Money knowledge (risk, valuation, market microstructure)
        """
        self.connections["trading"] = True

        context = {
            "inflection_point": "TRADING_DECISIONS",
            "knowledge_sources": ["money"],
            "available_tools": [],
            "recommendations": [],
        }

        if self.money.get("loaded"):
            context["available_tools"] = [
                "calculate_npv",
                "calculate_sharpe_ratio",
                "calculate_compound_interest",
            ]

            # Risk assessment guidance
            context["risk_framework"] = {
                "metrics": self.money.get("risk_metrics", {}),
                "asset_classes": self.money.get("asset_classes", {}),
            }

            # If market data provided, calculate metrics
            if market_data:
                if "returns" in market_data and "risk_free_rate" in market_data:
                    returns = market_data["returns"]
                    rf = market_data["risk_free_rate"]
                    if returns and len(returns) > 1:
                        import statistics
                        mean_return = statistics.mean(returns)
                        std_dev = statistics.stdev(returns)
                        sharpe = self.money["calculate_sharpe_ratio"](
                            mean_return, rf, std_dev
                        )
                        context["calculated_sharpe"] = sharpe

            context["recommendations"].append(
                "Use Kelly Criterion for position sizing"
            )
            context["recommendations"].append(
                "Monitor VaR for portfolio risk limits"
            )

        return context

    # ========== INFLECTION POINT 2: INFRASTRUCTURE SCALING ==========

    def get_infrastructure_context(self, current_load: Dict = None) -> Dict[str, Any]:
        """
        Provide knowledge context for infrastructure decisions.

        Uses: Computing knowledge (optimization, distributed systems, metrics)
        """
        self.connections["infrastructure"] = True

        context = {
            "inflection_point": "INFRASTRUCTURE_SCALING",
            "knowledge_sources": ["computing"],
            "available_tools": [],
            "recommendations": [],
        }

        if self.computing.get("loaded"):
            context["available_tools"] = [
                "estimate_time_complexity",
                "get_complexity",
                "get_data_structure_complexity",
            ]

            context["complexity_classes"] = self.computing.get("complexity_classes", {})
            context["paradigms"] = self.computing.get("paradigms", {})

            # Scaling recommendations
            if current_load:
                cpu = current_load.get("cpu_percent", 0)
                memory = current_load.get("memory_percent", 0)

                if cpu > 80:
                    context["recommendations"].append(
                        "HIGH CPU: Consider horizontal scaling or algorithmic optimization"
                    )
                if memory > 85:
                    context["recommendations"].append(
                        "HIGH MEMORY: Implement caching layer or memory-efficient data structures"
                    )

            context["recommendations"].append(
                "Monitor O(n) operations that could become O(n²) at scale"
            )

        return context

    # ========== INFLECTION POINT 3: REVENUE OPTIMIZATION ==========

    def get_revenue_context(self, metrics: Dict = None) -> Dict[str, Any]:
        """
        Provide knowledge context for revenue optimization.

        Uses: Business knowledge (growth, pricing, economics)
        """
        self.connections["revenue"] = True

        context = {
            "inflection_point": "REVENUE_OPTIMIZATION",
            "knowledge_sources": ["business", "money"],
            "available_tools": [],
            "recommendations": [],
        }

        if self.business.get("loaded"):
            context["available_tools"].extend([
                "calculate_ltv_cac_ratio",
                "calculate_runway",
                "calculate_wacc",
            ])

            context["business_structures"] = self.business.get("business_structures", {})
            context["pricing_strategies"] = self.business.get("pricing_strategies", {})
            context["startup_metrics"] = self.business.get("startup_metrics", {})

            if metrics:
                # Calculate unit economics
                cac = metrics.get("cac", 0)
                ltv = metrics.get("ltv", 0)
                if cac > 0 and ltv > 0:
                    ratio = self.business["calculate_ltv_cac_ratio"](ltv, cac)
                    context["ltv_cac_ratio"] = ratio
                    if ratio < 3:
                        context["recommendations"].append(
                            f"LTV:CAC ratio is {ratio:.1f}x - aim for 3x+"
                        )

        if self.money.get("loaded"):
            context["available_tools"].extend([
                "calculate_npv",
                "calculate_irr",
            ])

            context["recommendations"].append(
                "Use NPV for evaluating revenue streams"
            )

        return context

    # ========== INFLECTION POINT 4: REALITY ASSESSMENT ==========

    def get_reality_context(self, external_state: Dict = None) -> Dict[str, Any]:
        """
        Provide holistic knowledge context for reality assessment.

        Uses: ALL knowledge bases for comprehensive understanding
        """
        self.connections["reality"] = True

        context = {
            "inflection_point": "REALITY_ASSESSMENT",
            "knowledge_sources": ["computing", "business", "money"],
            "frameworks": {},
            "recommendations": [],
        }

        # Computing lens - system health
        if self.computing.get("loaded"):
            context["frameworks"]["technical"] = {
                "metrics": self.computing.get("system_metrics", {}),
                "optimization": self.computing.get("algorithm_paradigms", {}),
            }

        # Business lens - market position
        if self.business.get("loaded"):
            context["frameworks"]["business"] = {
                "competitive": self.business.get("competitive_strategies", {}),
                "growth": self.business.get("growth_metrics", {}),
            }

        # Money lens - financial health
        if self.money.get("loaded"):
            context["frameworks"]["financial"] = {
                "risk": self.money.get("risk_metrics", {}),
                "assets": self.money.get("asset_classes", {}),
            }

        context["recommendations"].append(
            "Cross-reference technical, business, and financial indicators"
        )
        context["recommendations"].append(
            "Reality = intersection of all three knowledge domains"
        )

        return context

    # ========== INFLECTION POINT 5: SELF-HEALING ==========

    def get_healing_context(self, error_info: Dict = None) -> Dict[str, Any]:
        """
        Provide knowledge context for self-healing operations.

        Uses: Computing knowledge (diagnostics, recovery patterns)
        """
        self.connections["self_healing"] = True

        context = {
            "inflection_point": "SELF_HEALING",
            "knowledge_sources": ["computing"],
            "recovery_patterns": [],
            "recommendations": [],
        }

        if self.computing.get("loaded"):
            context["data_structures"] = self.computing.get("data_structures", {})

            # Recovery patterns from computing knowledge
            context["recovery_patterns"] = [
                "Circuit breaker pattern for cascading failures",
                "Exponential backoff for retries",
                "Bulkhead isolation for fault containment",
                "Health checks with graceful degradation",
            ]

            if error_info:
                error_type = error_info.get("type", "unknown")
                if "memory" in error_type.lower():
                    context["recommendations"].append(
                        "Consider memory-efficient data structures or caching eviction"
                    )
                elif "timeout" in error_type.lower():
                    context["recommendations"].append(
                        "Implement async processing or increase timeout with backoff"
                    )
                elif "connection" in error_type.lower():
                    context["recommendations"].append(
                        "Use connection pooling with circuit breaker"
                    )

        return context

    # ========== INFLECTION POINT 6: STRATEGIC PLANNING ==========

    def get_strategic_context(self, goals: Dict = None) -> Dict[str, Any]:
        """
        Provide knowledge context for strategic planning.

        Uses: Business + Money knowledge (strategy, capital allocation)
        """
        self.connections["strategic"] = True

        context = {
            "inflection_point": "STRATEGIC_PLANNING",
            "knowledge_sources": ["business", "money"],
            "frameworks": {},
            "recommendations": [],
        }

        if self.business.get("loaded"):
            context["frameworks"]["strategy"] = {
                "competitive": self.business.get("competitive_strategies", {}),
                "models": self.business.get("business_models", {}),
            }

            context["recommendations"].append(
                "Use Porter's Five Forces for competitive analysis"
            )

        if self.money.get("loaded"):
            context["frameworks"]["capital"] = {
                "valuation_tools": ["NPV", "IRR", "WACC"],
                "risk_framework": self.money.get("risk_metrics", {}),
            }

            # Capital allocation guidance
            if goals:
                target_return = goals.get("target_return", 0.15)
                risk_tolerance = goals.get("risk_tolerance", "moderate")

                context["capital_guidance"] = {
                    "target_return": target_return,
                    "risk_tolerance": risk_tolerance,
                    "allocation_principle": "Kelly Criterion for sizing, MPT for diversification",
                }

            context["recommendations"].append(
                "Use WACC as hurdle rate for investment decisions"
            )

        return context

    # ========== UNIFIED QUERY INTERFACE ==========

    def query(self, inflection_point: str, data: Dict = None) -> Dict[str, Any]:
        """
        Unified interface to query knowledge for any inflection point.

        Args:
            inflection_point: One of trading, infrastructure, revenue,
                            reality, self_healing, strategic
            data: Optional context data for the query

        Returns:
            Knowledge context for the specified inflection point
        """
        handlers = {
            "trading": self.get_trading_context,
            "infrastructure": self.get_infrastructure_context,
            "revenue": self.get_revenue_context,
            "reality": self.get_reality_context,
            "self_healing": self.get_healing_context,
            "strategic": self.get_strategic_context,
        }

        handler = handlers.get(inflection_point.lower())
        if handler:
            return handler(data)
        else:
            return {
                "error": f"Unknown inflection point: {inflection_point}",
                "available": list(handlers.keys()),
            }

    def save_state(self):
        """Save nexus state including connections."""
        state = self.status()
        state["connections"] = self.connections
        state["query_counts"] = getattr(self, 'query_counts', {})
        state["initialized"] = self.initialized
        state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(NEXUS_STATE, 'w') as f:
            json.dump(state, f, indent=2)


# ========== GLOBAL NEXUS INSTANCE ==========

_nexus = None

def get_nexus() -> KnowledgeNexus:
    """Get or create the global knowledge nexus."""
    global _nexus
    if _nexus is None:
        _nexus = KnowledgeNexus()
    return _nexus


# ========== CLI ==========

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Knowledge Nexus")
    parser.add_argument("command", choices=["status", "query", "test"])
    parser.add_argument("--point", help="Inflection point for query")
    args = parser.parse_args()

    nexus = get_nexus()

    if args.command == "status":
        print(json.dumps(nexus.status(), indent=2))

    elif args.command == "query":
        if args.point:
            result = nexus.query(args.point)
            print(json.dumps(result, indent=2, default=str))
        else:
            print("Use --point to specify inflection point")
            print("Available: trading, infrastructure, revenue, reality, self_healing, strategic")

    elif args.command == "test":
        print("=== KNOWLEDGE NEXUS TEST ===\n")

        status = nexus.status()
        print(f"Knowledge Bases Loaded: {status['total_loaded']}/3")
        for kb, info in status["knowledge_bases"].items():
            mark = "✓" if info["loaded"] else "✗"
            print(f"  {mark} {kb}")

        print("\n=== Testing Inflection Points ===\n")

        for point in ["trading", "infrastructure", "revenue", "reality", "self_healing", "strategic"]:
            result = nexus.query(point)
            sources = result.get("knowledge_sources", [])
            tools = len(result.get("available_tools", []))
            recs = len(result.get("recommendations", []))
            print(f"  {point:15} | sources: {sources} | tools: {tools} | recs: {recs}")

        nexus.save_state()
        print("\n✓ State saved to knowledge_nexus.json")


if __name__ == "__main__":
    main()
