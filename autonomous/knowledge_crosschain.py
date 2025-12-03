#!/usr/bin/env python3
"""
Knowledge Crosschain - All Bases Connected to All Processes
============================================================

Cross-chains all knowledge bases and injects into active processes.

CROSSCHAIN TOPOLOGY:
===================

    Computing ◄──────────────────►  Business
         │                              │
         │    ┌──────────────────┐     │
         │    │   CROSSCHAIN     │     │
         └───►│     NEXUS        │◄────┘
              │                  │
              └────────┬─────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
         ▼             ▼             ▼
      Money ◄─────► Computing ◄─────► Business
                       │
                       ▼
            ┌─────────────────────┐
            │  ACTIVE PROCESSES   │
            │                     │
            │  • hardware_brain   │
            │  • scaling_engine   │
            │  • self_healer      │
            │  • backend_loop     │
            │  • trade_executor   │
            │  • reality_feedback │
            └─────────────────────┘

CROSS-CHAIN KNOWLEDGE LINKS:
===========================
Computing ↔ Business: Tech scalability → business growth
Computing ↔ Money: Algorithm efficiency → trading performance
Business ↔ Money: Unit economics → capital allocation
All Three: Unified optimization framework

Serving: Yair Siegel
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

CROSSCHAIN_STATE = STATE_DIR / "knowledge_crosschain.json"


@dataclass
class CrosschainLink:
    """A bidirectional link between knowledge domains."""
    domain_a: str
    domain_b: str
    link_type: str
    strength: float = 1.0
    insights: List[str] = field(default_factory=list)
    active: bool = True


@dataclass
class ProcessInjection:
    """Knowledge injection point for an active process."""
    process_name: str
    knowledge_domains: List[str]
    injection_method: str  # direct, callback, polling
    last_injection: Optional[str] = None
    injection_count: int = 0


class KnowledgeCrosschain:
    """
    Cross-chains all knowledge bases and injects into active processes.

    Creates a unified knowledge mesh where:
    - All domains are connected to all other domains
    - Combined insights emerge from intersections
    - Every active process receives relevant knowledge
    """

    def __init__(self):
        self.master = "Yair Siegel"
        self.initialized = datetime.now(timezone.utc).isoformat()

        # Load all knowledge bases
        self.knowledge = self._load_all_knowledge()

        # Create crosschain links
        self.links = self._create_crosschain_links()

        # Define process injections
        self.injections = self._define_injections()

        # Cross-chain state
        self.queries = 0
        self.injections_performed = 0

    def _load_all_knowledge(self) -> Dict[str, Any]:
        """Load all three knowledge bases."""
        knowledge = {}

        # Computing
        try:
            from executor.computing import (
                KNOWLEDGE_PATH, KNOWLEDGE_ADVANCED_PATH,
                COMPLEXITY_CLASSES, DATA_STRUCTURES, PARADIGMS,
                SORTING_ALGORITHMS, SEARCH_ALGORITHMS,
                estimate_time_complexity, get_complexity,
            )
            knowledge["computing"] = {
                "loaded": True,
                "complexity_classes": COMPLEXITY_CLASSES,
                "data_structures": DATA_STRUCTURES,
                "paradigms": PARADIGMS,
                "sorting": SORTING_ALGORITHMS,
                "searching": SEARCH_ALGORITHMS,
                "tools": {
                    "estimate_time_complexity": estimate_time_complexity,
                    "get_complexity": get_complexity,
                },
            }
        except Exception as e:
            knowledge["computing"] = {"loaded": False, "error": str(e)}

        # Business
        try:
            from executor.business import (
                KNOWLEDGE_PATH, KNOWLEDGE_ADVANCED_PATH,
                BUSINESS_STRUCTURES, PRICING_STRATEGIES,
                STARTUP_METRICS, GENERIC_STRATEGIES,
                PORTER_FIVE_FORCES, FINANCIAL_RATIOS,
                calculate_ltv_cac_ratio, calculate_runway,
                calculate_npv, calculate_irr, calculate_wacc,
            )
            knowledge["business"] = {
                "loaded": True,
                "structures": BUSINESS_STRUCTURES,
                "pricing": PRICING_STRATEGIES,
                "metrics": STARTUP_METRICS,
                "strategies": GENERIC_STRATEGIES,
                "porter": PORTER_FIVE_FORCES,
                "ratios": FINANCIAL_RATIOS,
                "tools": {
                    "calculate_ltv_cac_ratio": calculate_ltv_cac_ratio,
                    "calculate_runway": calculate_runway,
                    "calculate_npv": calculate_npv,
                    "calculate_irr": calculate_irr,
                    "calculate_wacc": calculate_wacc,
                },
            }
        except Exception as e:
            knowledge["business"] = {"loaded": False, "error": str(e)}

        # Money
        try:
            from executor.money import (
                KNOWLEDGE_PATH, KNOWLEDGE_ADVANCED_PATH,
                INTEREST_RATE_TYPES, ASSET_CLASSES, RISK_METRICS,
                MONEY_SUPPLY,
                calculate_compound_interest, calculate_npv,
                calculate_irr, calculate_bond_price,
                calculate_sharpe_ratio, calculate_wacc,
                calculate_loan_payment,
            )
            knowledge["money"] = {
                "loaded": True,
                "interest_rates": INTEREST_RATE_TYPES,
                "asset_classes": ASSET_CLASSES,
                "risk_metrics": RISK_METRICS,
                "money_supply": MONEY_SUPPLY,
                "tools": {
                    "calculate_compound_interest": calculate_compound_interest,
                    "calculate_npv": calculate_npv,
                    "calculate_irr": calculate_irr,
                    "calculate_bond_price": calculate_bond_price,
                    "calculate_sharpe_ratio": calculate_sharpe_ratio,
                    "calculate_wacc": calculate_wacc,
                    "calculate_loan_payment": calculate_loan_payment,
                },
            }
        except Exception as e:
            knowledge["money"] = {"loaded": False, "error": str(e)}

        return knowledge

    def _create_crosschain_links(self) -> Dict[str, CrosschainLink]:
        """Create bidirectional links between all knowledge domains."""
        return {
            # Computing ↔ Business
            "computing_business": CrosschainLink(
                domain_a="computing",
                domain_b="business",
                link_type="scalability_growth",
                strength=0.9,
                insights=[
                    "O(n) algorithms scale linearly with business growth",
                    "System architecture determines scaling ceiling",
                    "Technical debt compounds like financial debt",
                    "Automation ROI follows diminishing returns curve",
                ],
            ),
            # Computing ↔ Money
            "computing_money": CrosschainLink(
                domain_a="computing",
                domain_b="money",
                link_type="efficiency_performance",
                strength=0.95,
                insights=[
                    "Latency directly impacts trading profit",
                    "Algorithm complexity affects transaction costs",
                    "Data structure choice impacts memory costs",
                    "Optimization has diminishing returns like investments",
                ],
            ),
            # Business ↔ Money
            "business_money": CrosschainLink(
                domain_a="business",
                domain_b="money",
                link_type="economics_capital",
                strength=0.85,
                insights=[
                    "Unit economics must support capital structure",
                    "LTV:CAC ratio determines sustainable growth rate",
                    "Cash flow timing affects NPV calculations",
                    "Risk-adjusted returns inform strategic decisions",
                ],
            ),
            # Triple intersection
            "all_three": CrosschainLink(
                domain_a="computing+business",
                domain_b="money",
                link_type="unified_optimization",
                strength=1.0,
                insights=[
                    "Optimal system: efficient tech + sound economics + capital efficiency",
                    "Kelly criterion applies to resource allocation across all domains",
                    "Compound growth principles work in code, business, and capital",
                    "Risk management is universal: technical, business, and financial",
                ],
            ),
        }

    def _define_injections(self) -> Dict[str, ProcessInjection]:
        """Define knowledge injection points for each active process."""
        return {
            "hardware_brain": ProcessInjection(
                process_name="hardware_brain",
                knowledge_domains=["computing"],
                injection_method="direct",
            ),
            "scaling_engine": ProcessInjection(
                process_name="scaling_engine",
                knowledge_domains=["computing", "business"],
                injection_method="direct",
            ),
            "self_healer": ProcessInjection(
                process_name="self_healer",
                knowledge_domains=["computing"],
                injection_method="direct",
            ),
            "backend_loop": ProcessInjection(
                process_name="backend_loop",
                knowledge_domains=["computing", "business", "money"],
                injection_method="callback",
            ),
            "trade_executor": ProcessInjection(
                process_name="trade_executor",
                knowledge_domains=["money", "computing"],
                injection_method="direct",
            ),
            "reality_feedback": ProcessInjection(
                process_name="reality_feedback",
                knowledge_domains=["computing", "business", "money"],
                injection_method="polling",
            ),
            "ai_core": ProcessInjection(
                process_name="ai_core",
                knowledge_domains=["computing", "business", "money"],
                injection_method="direct",
            ),
            "circuit_board": ProcessInjection(
                process_name="circuit_board",
                knowledge_domains=["computing", "business", "money"],
                injection_method="direct",
            ),
        }

    def crosschain_query(self, domains: List[str] = None) -> Dict[str, Any]:
        """
        Query across multiple knowledge domains.

        Returns combined knowledge from specified domains with cross-links.
        """
        self.queries += 1

        if domains is None:
            domains = ["computing", "business", "money"]

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "domains_queried": domains,
            "knowledge": {},
            "crosslinks": [],
            "unified_insights": [],
        }

        # Gather knowledge from each domain
        for domain in domains:
            if domain in self.knowledge and self.knowledge[domain].get("loaded"):
                result["knowledge"][domain] = {
                    "loaded": True,
                    "tools_available": list(self.knowledge[domain].get("tools", {}).keys()),
                }
            else:
                result["knowledge"][domain] = {"loaded": False}

        # Add relevant crosslinks
        for link_name, link in self.links.items():
            domains_in_link = [link.domain_a.replace("+", ",").split(",")[0],
                              link.domain_b]
            if any(d in domains for d in domains_in_link):
                result["crosslinks"].append({
                    "name": link_name,
                    "type": link.link_type,
                    "strength": link.strength,
                    "insights": link.insights,
                })

        # Generate unified insights from intersections
        if "computing" in domains and "business" in domains:
            result["unified_insights"].append(
                "Tech scalability directly enables business growth rate"
            )
        if "computing" in domains and "money" in domains:
            result["unified_insights"].append(
                "Algorithm efficiency translates to trading alpha"
            )
        if "business" in domains and "money" in domains:
            result["unified_insights"].append(
                "Unit economics determine sustainable capital deployment"
            )
        if len(domains) == 3:
            result["unified_insights"].append(
                "UNIFIED: Optimize across tech, economics, and capital simultaneously"
            )

        return result

    def inject_to_process(self, process_name: str, context: Dict = None) -> Dict[str, Any]:
        """
        Inject knowledge into a specific active process.

        Returns knowledge package tailored for the process.
        """
        self.injections_performed += 1

        if process_name not in self.injections:
            return {"error": f"Unknown process: {process_name}"}

        injection = self.injections[process_name]
        injection.last_injection = datetime.now(timezone.utc).isoformat()
        injection.injection_count += 1

        # Build knowledge package for this process
        package = {
            "process": process_name,
            "timestamp": injection.last_injection,
            "injection_count": injection.injection_count,
            "domains": {},
            "tools": {},
            "recommendations": [],
        }

        # Gather relevant knowledge
        for domain in injection.knowledge_domains:
            if domain in self.knowledge and self.knowledge[domain].get("loaded"):
                package["domains"][domain] = True

                # Add tools
                for tool_name, tool_func in self.knowledge[domain].get("tools", {}).items():
                    package["tools"][f"{domain}.{tool_name}"] = tool_func

        # Process-specific recommendations
        if process_name == "hardware_brain":
            package["recommendations"] = [
                "Monitor O(n²) operations in hot paths",
                "Use memory-efficient data structures",
                "Implement circuit breaker patterns",
            ]
        elif process_name == "scaling_engine":
            package["recommendations"] = [
                "Scale horizontally before vertically",
                "Monitor resource utilization vs cost",
                "Apply auto-scaling based on load patterns",
            ]
        elif process_name == "trade_executor":
            package["recommendations"] = [
                "Minimize latency in order execution",
                "Use Kelly criterion for position sizing",
                "Monitor Sharpe ratio continuously",
            ]
        elif process_name == "backend_loop":
            package["recommendations"] = [
                "Balance cycle frequency with resource usage",
                "Prioritize high-value operations",
                "Maintain state consistency across components",
            ]
        elif process_name == "ai_core":
            package["recommendations"] = [
                "Synthesize knowledge across all domains",
                "Amplify high-confidence signals",
                "Crystallize decisions with maximum clarity",
            ]

        return package

    def inject_all_processes(self) -> Dict[str, Any]:
        """Inject knowledge into all active processes."""
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "processes": {},
        }

        for process_name in self.injections:
            results["processes"][process_name] = self.inject_to_process(process_name)

        return results

    def get_tool(self, domain: str, tool_name: str) -> Optional[Callable]:
        """Get a specific tool function from a knowledge domain."""
        if domain in self.knowledge and self.knowledge[domain].get("loaded"):
            return self.knowledge[domain].get("tools", {}).get(tool_name)
        return None

    def calculate_crosschain(self, operation: str, **kwargs) -> Any:
        """
        Perform cross-chain calculations using tools from multiple domains.

        Operations:
        - risk_adjusted_growth: Combine business growth with money risk metrics
        - efficient_capital: Combine computing efficiency with money allocation
        - unified_npv: NPV calculation with tech cost considerations
        """
        if operation == "risk_adjusted_growth":
            # Combine LTV/CAC with Sharpe ratio concept
            ltv = kwargs.get("ltv", 100)
            cac = kwargs.get("cac", 30)
            volatility = kwargs.get("volatility", 0.2)

            ltv_cac_tool = self.get_tool("business", "calculate_ltv_cac_ratio")
            if ltv_cac_tool:
                ratio = ltv_cac_tool(ltv, cac)
                risk_adjusted = ratio / (1 + volatility)
                return {
                    "ltv_cac_ratio": ratio,
                    "risk_adjusted_ratio": risk_adjusted,
                    "recommendation": "Good" if risk_adjusted > 2.5 else "Improve",
                }

        elif operation == "efficient_capital":
            # Combine algorithm efficiency with capital efficiency
            complexity = kwargs.get("complexity", "O(n)")
            capital = kwargs.get("capital", 1000)
            rate = kwargs.get("rate", 0.1)

            compound_tool = self.get_tool("money", "calculate_compound_interest")
            if compound_tool:
                future_value = compound_tool(capital, rate, 1, 5)
                efficiency_multiplier = {
                    "O(1)": 2.0,
                    "O(log n)": 1.5,
                    "O(n)": 1.0,
                    "O(n log n)": 0.8,
                    "O(n²)": 0.5,
                }.get(complexity, 1.0)

                return {
                    "base_future_value": future_value,
                    "efficiency_multiplier": efficiency_multiplier,
                    "adjusted_value": future_value * efficiency_multiplier,
                }

        elif operation == "unified_npv":
            # NPV with cross-domain considerations
            cash_flows = kwargs.get("cash_flows", [100, 100, 100])
            rate = kwargs.get("rate", 0.1)
            tech_cost = kwargs.get("tech_cost", 0.05)  # Tech maintenance cost

            npv_tool = self.get_tool("money", "calculate_npv")
            if npv_tool:
                base_npv = npv_tool(cash_flows, rate)
                tech_adjusted = npv_tool(
                    [cf * (1 - tech_cost) for cf in cash_flows],
                    rate
                )
                return {
                    "base_npv": base_npv,
                    "tech_adjusted_npv": tech_adjusted,
                    "tech_cost_impact": base_npv - tech_adjusted,
                }

        return {"error": f"Unknown operation: {operation}"}

    def status(self) -> Dict[str, Any]:
        """Get crosschain status."""
        return {
            "master": self.master,
            "initialized": self.initialized,
            "knowledge_bases": {
                domain: {"loaded": k.get("loaded", False)}
                for domain, k in self.knowledge.items()
            },
            "crosslinks": len(self.links),
            "injection_points": len(self.injections),
            "total_queries": self.queries,
            "total_injections": self.injections_performed,
            "processes": {
                name: {
                    "domains": inj.knowledge_domains,
                    "injection_count": inj.injection_count,
                }
                for name, inj in self.injections.items()
            },
        }

    def save_state(self):
        """Save crosschain state."""
        state = self.status()
        state["saved_at"] = datetime.now(timezone.utc).isoformat()
        with open(CROSSCHAIN_STATE, 'w') as f:
            json.dump(state, f, indent=2)


# ========== GLOBAL INSTANCE ==========

_crosschain = None

def get_crosschain() -> KnowledgeCrosschain:
    """Get or create the global crosschain."""
    global _crosschain
    if _crosschain is None:
        _crosschain = KnowledgeCrosschain()
    return _crosschain


# ========== CLI ==========

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Knowledge Crosschain")
    parser.add_argument("command", choices=["status", "query", "inject", "inject-all", "calculate"])
    parser.add_argument("--domains", nargs="+", default=["computing", "business", "money"])
    parser.add_argument("--process", help="Process to inject into")
    parser.add_argument("--operation", help="Cross-chain calculation operation")
    args = parser.parse_args()

    crosschain = get_crosschain()

    if args.command == "status":
        print(json.dumps(crosschain.status(), indent=2))

    elif args.command == "query":
        result = crosschain.crosschain_query(args.domains)
        print(json.dumps(result, indent=2))

    elif args.command == "inject":
        if args.process:
            result = crosschain.inject_to_process(args.process)
            # Convert tools to string representation
            result["tools"] = {k: str(v) for k, v in result.get("tools", {}).items()}
            print(json.dumps(result, indent=2))
        else:
            print("Use --process to specify target process")

    elif args.command == "inject-all":
        result = crosschain.inject_all_processes()
        # Convert tools to string representation
        for proc in result["processes"].values():
            proc["tools"] = {k: str(v) for k, v in proc.get("tools", {}).items()}
        print(json.dumps(result, indent=2))

    elif args.command == "calculate":
        if args.operation:
            result = crosschain.calculate_crosschain(
                args.operation,
                ltv=100, cac=30, volatility=0.2,
                capital=1000, rate=0.1, complexity="O(n)",
            )
            print(json.dumps(result, indent=2))
        else:
            print("Operations: risk_adjusted_growth, efficient_capital, unified_npv")

    crosschain.save_state()


if __name__ == "__main__":
    main()
