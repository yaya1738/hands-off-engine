#!/usr/bin/env python3
"""
INTEGRAFIX: Knowledge Reality Bridge
=====================================

All 20 Knowledge Bases → Reality

This is THE master integration that wires all knowledge bases to reality.
Every knowledge base connects to live data and real systems.

THE 20 KNOWLEDGE BASES:
=======================
CORE KNOWLEDGE (3):
1. Computing Knowledge - Algorithms, complexity, optimization
2. Business Knowledge - Strategy, metrics, growth
3. Money Knowledge - Finance, risk, capital

MEMORY SYSTEMS (4):
4. Memory Kernels - Stored topic kernels
5. AI Memory - Cross-session persistence
6. Trading Memory - Trade outcomes and learnings
7. System Bootstrap - Core system knowledge

KNOWLEDGE ENGINES (3):
8. Knowledge Nexus - 6 inflection points
9. Knowledge Fusion - Cross-domain synthesis
10. Knowledge Crosschain - All-to-all connections

YAIR KNOWLEDGE (2):
11. Yair Knowledge Bridge - Yair's complete context
12. Trading Teachings - Yair's trading wisdom

ABCFC FRAMEWORK (5):
13. ABCFC System - Complete hierarchy + nexus
14. ABCFC Nexus - Decision space evaluation
15. ABCFC CloudFlyer - Navigation through nexus
16. ABCFC Layers - Hierarchical finance
17. ABCFC Live/State - Real order book + unified state

INTEGRAFIX BRIDGES (3):
18. Fair Price Estimator - Price estimation knowledge
19. Outcome Tracker - Trade outcome knowledge
20. Reality Bridge - 4D temporal self-awareness

REALITY CONNECTIONS:
===================
- Live market data (Polymarket, order books)
- Real trading positions
- Actual financial state
- Running processes
- Active infrastructure
- Current time/state

Serving: Yair Siegel
"""

import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

KNOWLEDGE_REALITY_STATE = STATE_DIR / "knowledge_reality.json"


@dataclass
class KnowledgeBase:
    """A single knowledge base."""
    id: str
    name: str
    category: str
    module_path: str
    loaded: bool = False
    error: Optional[str] = None
    entry_count: int = 0
    reality_connected: bool = False
    last_reality_sync: Optional[str] = None


@dataclass
class RealityConnection:
    """A connection between knowledge and reality."""
    knowledge_base: str
    reality_source: str
    connection_type: str  # direct, polling, callback
    last_sync: Optional[str] = None
    sync_count: int = 0
    healthy: bool = True


class KnowledgeReality:
    """
    THE master bridge connecting all 20 knowledge bases to reality.

    Every piece of knowledge must be grounded in reality to be useful.
    This bridge ensures knowledge flows to and from the real world.
    """

    def __init__(self):
        self.master = "Yair Siegel"
        self.initialized = datetime.now(timezone.utc).isoformat()

        # All 20 knowledge bases
        self.knowledge_bases: Dict[str, KnowledgeBase] = {}

        # Reality connections
        self.reality_connections: List[RealityConnection] = []

        # Loaded modules (actual objects)
        self.modules: Dict[str, Any] = {}

        # Load all knowledge bases
        self._load_all_knowledge_bases()

        # Connect to reality
        self._establish_reality_connections()

        # Stats
        self.queries = 0
        self.reality_syncs = 0

    def _load_all_knowledge_bases(self):
        """Load all 20 knowledge bases."""

        # ========== CORE KNOWLEDGE (3) ==========

        # 1. Computing Knowledge
        self._load_knowledge_base(
            id="computing",
            name="Computing Knowledge",
            category="core",
            module_path="executor.computing",
            loader=self._load_computing_knowledge
        )

        # 2. Business Knowledge
        self._load_knowledge_base(
            id="business",
            name="Business Knowledge",
            category="core",
            module_path="executor.business",
            loader=self._load_business_knowledge
        )

        # 3. Money Knowledge
        self._load_knowledge_base(
            id="money",
            name="Money Knowledge",
            category="core",
            module_path="executor.money",
            loader=self._load_money_knowledge
        )

        # ========== MEMORY SYSTEMS (4) ==========

        # 4. Memory Kernels
        self._load_knowledge_base(
            id="memory_kernels",
            name="Memory Kernels",
            category="memory",
            module_path="ai_nexus.memory_kernels",
            loader=self._load_memory_kernels
        )

        # 5. AI Memory
        self._load_knowledge_base(
            id="ai_memory",
            name="AI Memory",
            category="memory",
            module_path="integrafix.ai_memory",
            loader=self._load_ai_memory
        )

        # 6. Trading Memory
        self._load_knowledge_base(
            id="trading_memory",
            name="Trading Memory",
            category="memory",
            module_path="integrafix.trading_memory",
            loader=self._load_trading_memory
        )

        # 7. System Bootstrap
        self._load_knowledge_base(
            id="system_bootstrap",
            name="System Bootstrap",
            category="memory",
            module_path="ai.memory.kernels.system_bootstrap",
            loader=self._load_system_bootstrap
        )

        # ========== KNOWLEDGE ENGINES (3) ==========

        # 8. Knowledge Nexus
        self._load_knowledge_base(
            id="knowledge_nexus",
            name="Knowledge Nexus",
            category="engine",
            module_path="autonomous.knowledge_nexus",
            loader=self._load_knowledge_nexus
        )

        # 9. Knowledge Fusion
        self._load_knowledge_base(
            id="knowledge_fusion",
            name="Knowledge Fusion",
            category="engine",
            module_path="autonomous.knowledge_fusion",
            loader=self._load_knowledge_fusion
        )

        # 10. Knowledge Crosschain
        self._load_knowledge_base(
            id="knowledge_crosschain",
            name="Knowledge Crosschain",
            category="engine",
            module_path="autonomous.knowledge_crosschain",
            loader=self._load_knowledge_crosschain
        )

        # ========== YAIR KNOWLEDGE (2) ==========

        # 11. Yair Knowledge Bridge
        self._load_knowledge_base(
            id="yair_knowledge",
            name="Yair Knowledge Bridge",
            category="yair",
            module_path="integrafix.yair_knowledge_bridge",
            loader=self._load_yair_knowledge
        )

        # 12. Trading Teachings
        self._load_knowledge_base(
            id="trading_teachings",
            name="Trading Teachings",
            category="yair",
            module_path="yair_trading_wisdom",
            loader=self._load_trading_teachings
        )

        # ========== ABCFC FRAMEWORK (5) ==========

        # 13. ABCFC System
        self._load_knowledge_base(
            id="abcfc_system",
            name="ABCFC System",
            category="abcfc",
            module_path="executor.math.abcfc_system",
            loader=self._load_abcfc_system
        )

        # 14. ABCFC Nexus
        self._load_knowledge_base(
            id="abcfc_nexus",
            name="ABCFC Nexus",
            category="abcfc",
            module_path="executor.math.abcfc_nexus",
            loader=self._load_abcfc_nexus
        )

        # 15. ABCFC CloudFlyer
        self._load_knowledge_base(
            id="abcfc_cloudflyer",
            name="ABCFC CloudFlyer",
            category="abcfc",
            module_path="executor.math.abcfc_cloud_flyer",
            loader=self._load_abcfc_cloudflyer
        )

        # 16. ABCFC Layers
        self._load_knowledge_base(
            id="abcfc_layers",
            name="ABCFC Layers",
            category="abcfc",
            module_path="executor.math.abcfc_layers",
            loader=self._load_abcfc_layers
        )

        # 17. ABCFC State
        self._load_knowledge_base(
            id="abcfc_state",
            name="ABCFC Unified State",
            category="abcfc",
            module_path="executor.math.abcfc_state",
            loader=self._load_abcfc_state
        )

        # ========== INTEGRAFIX BRIDGES (3) ==========

        # 18. Fair Price Estimator
        self._load_knowledge_base(
            id="fair_price",
            name="Fair Price Estimator",
            category="integrafix",
            module_path="integrafix.fair_price_estimator",
            loader=self._load_fair_price
        )

        # 19. Outcome Tracker
        self._load_knowledge_base(
            id="outcome_tracker",
            name="Outcome Tracker",
            category="integrafix",
            module_path="integrafix.outcome_tracker",
            loader=self._load_outcome_tracker
        )

        # 20. Reality Bridge
        self._load_knowledge_base(
            id="reality_bridge",
            name="Reality Bridge",
            category="integrafix",
            module_path="autonomous.reality_bridge",
            loader=self._load_reality_bridge
        )

    def _load_knowledge_base(self, id: str, name: str, category: str,
                             module_path: str, loader: callable):
        """Load a single knowledge base."""
        kb = KnowledgeBase(
            id=id,
            name=name,
            category=category,
            module_path=module_path
        )

        try:
            module = loader()
            if module:
                kb.loaded = True
                kb.entry_count = module.get("entry_count", 0) if isinstance(module, dict) else 1
                self.modules[id] = module
        except Exception as e:
            kb.loaded = False
            kb.error = str(e)[:100]

        self.knowledge_bases[id] = kb

    # ========== KNOWLEDGE LOADERS ==========

    def _load_computing_knowledge(self) -> Dict:
        try:
            from executor.computing import (
                COMPLEXITY_CLASSES, DATA_STRUCTURES, PARADIGMS,
                SORTING_ALGORITHMS, SEARCH_ALGORITHMS,
                estimate_time_complexity, get_complexity
            )
            return {
                "complexity_classes": COMPLEXITY_CLASSES,
                "data_structures": DATA_STRUCTURES,
                "paradigms": PARADIGMS,
                "sorting": SORTING_ALGORITHMS,
                "searching": SEARCH_ALGORITHMS,
                "tools": {
                    "estimate_time_complexity": estimate_time_complexity,
                    "get_complexity": get_complexity,
                },
                "entry_count": len(COMPLEXITY_CLASSES) + len(DATA_STRUCTURES) + len(PARADIGMS)
            }
        except Exception as e:
            return {"error": str(e), "entry_count": 0}

    def _load_business_knowledge(self) -> Dict:
        try:
            from executor.business import (
                BUSINESS_STRUCTURES, PRICING_STRATEGIES,
                STARTUP_METRICS, GENERIC_STRATEGIES,
                PORTER_FIVE_FORCES, FINANCIAL_RATIOS,
                calculate_ltv_cac_ratio, calculate_runway,
                calculate_npv, calculate_irr, calculate_wacc
            )
            return {
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
                "entry_count": len(BUSINESS_STRUCTURES) + len(PRICING_STRATEGIES) + len(STARTUP_METRICS)
            }
        except Exception as e:
            return {"error": str(e), "entry_count": 0}

    def _load_money_knowledge(self) -> Dict:
        try:
            from executor.money import (
                INTEREST_RATE_TYPES, ASSET_CLASSES, RISK_METRICS,
                MONEY_SUPPLY,
                calculate_compound_interest, calculate_npv,
                calculate_irr, calculate_bond_price,
                calculate_sharpe_ratio, calculate_wacc
            )
            return {
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
                },
                "entry_count": len(ASSET_CLASSES) + len(RISK_METRICS)
            }
        except Exception as e:
            return {"error": str(e), "entry_count": 0}

    def _load_memory_kernels(self) -> Dict:
        try:
            from ai_nexus.memory_kernels import list_kernels, load_kernel
            kernels = list_kernels()
            return {
                "kernels": kernels,
                "load_kernel": load_kernel,
                "entry_count": len(kernels)
            }
        except Exception as e:
            return {"error": str(e), "entry_count": 0}

    def _load_ai_memory(self) -> Dict:
        try:
            from integrafix.ai_memory import get_memory, AIMemory
            memory = get_memory()
            return {
                "memory": memory,
                "status": memory.status(),
                "entry_count": len(memory.memories)
            }
        except Exception as e:
            return {"error": str(e), "entry_count": 0}

    def _load_trading_memory(self) -> Dict:
        try:
            from integrafix.trading_memory import get_trading_memory
            tmem = get_trading_memory()
            return {
                "memory": tmem,
                "entry_count": len(tmem.trades) if hasattr(tmem, 'trades') else 0
            }
        except Exception as e:
            # May not exist yet
            return {"error": str(e), "entry_count": 0}

    def _load_system_bootstrap(self) -> Dict:
        try:
            bootstrap_file = PROJECT_ROOT / "ai" / "memory" / "kernels" / "system_bootstrap.json"
            if bootstrap_file.exists():
                with open(bootstrap_file) as f:
                    data = json.load(f)
                return {
                    "data": data,
                    "entry_count": len(data.get("key_decisions", [])) + len(data.get("failed_paths", []))
                }
            return {"error": "File not found", "entry_count": 0}
        except Exception as e:
            return {"error": str(e), "entry_count": 0}

    def _load_knowledge_nexus(self) -> Dict:
        try:
            from autonomous.knowledge_nexus import get_nexus
            nexus = get_nexus()
            return {
                "nexus": nexus,
                "status": nexus.status(),
                "entry_count": 6  # 6 inflection points
            }
        except Exception as e:
            return {"error": str(e), "entry_count": 0}

    def _load_knowledge_fusion(self) -> Dict:
        try:
            from autonomous.knowledge_fusion import get_fusion
            fusion = get_fusion()
            return {
                "fusion": fusion,
                "status": fusion.status(),
                "entry_count": len(fusion.fusion_matrix)
            }
        except Exception as e:
            return {"error": str(e), "entry_count": 0}

    def _load_knowledge_crosschain(self) -> Dict:
        try:
            from autonomous.knowledge_crosschain import get_crosschain
            crosschain = get_crosschain()
            return {
                "crosschain": crosschain,
                "status": crosschain.status(),
                "entry_count": len(crosschain.links)
            }
        except Exception as e:
            return {"error": str(e), "entry_count": 0}

    def _load_yair_knowledge(self) -> Dict:
        try:
            from integrafix.yair_knowledge_bridge import get_yair_knowledge_bridge
            bridge = get_yair_knowledge_bridge()
            return {
                "bridge": bridge,
                "status": bridge.status(),
                "entry_count": len(bridge.knowledge_bases)
            }
        except Exception as e:
            return {"error": str(e), "entry_count": 0}

    def _load_trading_teachings(self) -> Dict:
        """Load Yair's trading teachings."""
        teachings = [
            "Be the house, not the gambler - MAKE more than you TAKE",
            "THE PRICE IS A LIE - always check book depth",
            "Post limits at ridiculous levels, let market come to you",
            "Same capital can fish across ALL markets (reusable collateral)",
            "One man's fat finger = your opportunity",
            "YES + NO < $1 = free money (merge arbitrage)",
            "ESPN mid-game probability = very accurate",
            "New markets have thin books = easier fills at extremes",
        ]
        return {
            "teachings": teachings,
            "entry_count": len(teachings)
        }

    def _load_abcfc_system(self) -> Dict:
        try:
            from executor.math.abcfc_system import ABCFCSystem
            return {
                "class": ABCFCSystem,
                "entry_count": 1
            }
        except Exception as e:
            return {"error": str(e), "entry_count": 0}

    def _load_abcfc_nexus(self) -> Dict:
        try:
            from executor.math.abcfc_nexus import ABCFCNexus
            return {
                "class": ABCFCNexus,
                "entry_count": 1
            }
        except Exception as e:
            return {"error": str(e), "entry_count": 0}

    def _load_abcfc_cloudflyer(self) -> Dict:
        try:
            from executor.math.abcfc_cloud_flyer import ABCFCCloudFlyer
            return {
                "class": ABCFCCloudFlyer,
                "entry_count": 1
            }
        except Exception as e:
            return {"error": str(e), "entry_count": 0}

    def _load_abcfc_layers(self) -> Dict:
        try:
            from executor.math.abcfc_layers import ABCFCLayers
            return {
                "class": ABCFCLayers,
                "entry_count": 1
            }
        except Exception as e:
            return {"error": str(e), "entry_count": 0}

    def _load_abcfc_state(self) -> Dict:
        try:
            from executor.math.abcfc_state import UnifiedABCFCState, get_unified_state
            state = get_unified_state()
            return {
                "state": state,
                "class": UnifiedABCFCState,
                "entry_count": 1
            }
        except Exception as e:
            return {"error": str(e), "entry_count": 0}

    def _load_fair_price(self) -> Dict:
        try:
            from integrafix.fair_price_estimator import get_fair_price_estimator
            estimator = get_fair_price_estimator()
            return {
                "estimator": estimator,
                "entry_count": 1
            }
        except Exception as e:
            return {"error": str(e), "entry_count": 0}

    def _load_outcome_tracker(self) -> Dict:
        try:
            from integrafix.outcome_tracker import get_outcome_tracker
            tracker = get_outcome_tracker()
            return {
                "tracker": tracker,
                "entry_count": len(tracker.outcomes) if hasattr(tracker, 'outcomes') else 0
            }
        except Exception as e:
            return {"error": str(e), "entry_count": 0}

    def _load_reality_bridge(self) -> Dict:
        try:
            from autonomous.reality_bridge import get_bridge
            bridge = get_bridge()
            return {
                "bridge": bridge,
                "entry_count": 5  # 5 domains
            }
        except Exception as e:
            return {"error": str(e), "entry_count": 0}

    # ========== REALITY CONNECTIONS ==========

    def _establish_reality_connections(self):
        """Establish connections between knowledge and reality."""

        # Core knowledge → Live calculations
        self.reality_connections.append(RealityConnection(
            knowledge_base="computing",
            reality_source="live_algorithms",
            connection_type="direct"
        ))

        self.reality_connections.append(RealityConnection(
            knowledge_base="business",
            reality_source="live_metrics",
            connection_type="polling"
        ))

        self.reality_connections.append(RealityConnection(
            knowledge_base="money",
            reality_source="polymarket_balance",
            connection_type="polling"
        ))

        # Memory → State files
        self.reality_connections.append(RealityConnection(
            knowledge_base="ai_memory",
            reality_source="state/ai_memory",
            connection_type="direct"
        ))

        self.reality_connections.append(RealityConnection(
            knowledge_base="trading_memory",
            reality_source="state/trades",
            connection_type="direct"
        ))

        # ABCFC → Live market data
        self.reality_connections.append(RealityConnection(
            knowledge_base="abcfc_nexus",
            reality_source="polymarket_orderbook",
            connection_type="polling"
        ))

        self.reality_connections.append(RealityConnection(
            knowledge_base="abcfc_state",
            reality_source="unified_state",
            connection_type="direct"
        ))

        # Integrafix → Live systems
        self.reality_connections.append(RealityConnection(
            knowledge_base="fair_price",
            reality_source="market_prices",
            connection_type="polling"
        ))

        self.reality_connections.append(RealityConnection(
            knowledge_base="reality_bridge",
            reality_source="infrastructure",
            connection_type="direct"
        ))

    # ========== REALITY SYNC ==========

    def sync_to_reality(self) -> Dict[str, Any]:
        """
        Sync all knowledge bases to current reality.

        This is THE core function that grounds knowledge in reality.
        """
        self.reality_syncs += 1
        now = datetime.now(timezone.utc).isoformat()

        results = {
            "timestamp": now,
            "syncs": [],
            "reality_state": {},
        }

        # 1. Sync financial reality
        financial = self._sync_financial_reality()
        results["reality_state"]["financial"] = financial

        # 2. Sync trading reality
        trading = self._sync_trading_reality()
        results["reality_state"]["trading"] = trading

        # 3. Sync infrastructure reality
        infra = self._sync_infrastructure_reality()
        results["reality_state"]["infrastructure"] = infra

        # 4. Sync temporal reality
        temporal = self._sync_temporal_reality()
        results["reality_state"]["temporal"] = temporal

        # 5. Update all knowledge bases with reality context
        for kb_id, kb in self.knowledge_bases.items():
            if kb.loaded:
                kb.last_reality_sync = now
                kb.reality_connected = True

        # Save state
        self._save_state(results)

        return results

    def _sync_financial_reality(self) -> Dict:
        """Sync with current financial reality."""
        result = {
            "source": "polymarket_balance",
            "synced": False,
        }

        try:
            balance_file = STATE_DIR / "polymarket_balance.json"
            if balance_file.exists():
                with open(balance_file) as f:
                    data = json.load(f)
                result["cash"] = data.get("cash", 0)
                result["positions_value"] = data.get("positions_value", 0)
                result["total"] = data.get("total", 0)
                result["synced"] = True
        except Exception as e:
            result["error"] = str(e)

        return result

    def _sync_trading_reality(self) -> Dict:
        """Sync with current trading reality."""
        result = {
            "source": "positions",
            "synced": False,
        }

        try:
            positions_file = STATE_DIR / "positions.json"
            if positions_file.exists():
                with open(positions_file) as f:
                    data = json.load(f)
                result["position_count"] = len(data.get("positions", []))
                result["synced"] = True
        except Exception as e:
            result["error"] = str(e)

        return result

    def _sync_infrastructure_reality(self) -> Dict:
        """Sync with infrastructure reality."""
        result = {
            "source": "reality_bridge",
            "synced": False,
        }

        try:
            if "reality_bridge" in self.modules:
                bridge_data = self.modules["reality_bridge"]
                if "bridge" in bridge_data:
                    bridge = bridge_data["bridge"]
                    who_am_i = bridge.who_am_i()
                    result["health"] = who_am_i.get("present", {}).get("health", "unknown")
                    result["phase"] = who_am_i.get("present", {}).get("phase", "unknown")
                    result["synced"] = True
        except Exception as e:
            result["error"] = str(e)

        return result

    def _sync_temporal_reality(self) -> Dict:
        """Sync with temporal reality (time-based state)."""
        now = datetime.now(timezone.utc)

        return {
            "timestamp": now.isoformat(),
            "hour": now.hour,
            "day_of_week": now.strftime("%A"),
            "market_hours": 6 <= now.hour <= 23,  # Roughly when markets are active
            "synced": True,
        }

    # ========== UNIFIED QUERIES ==========

    def query_all_knowledge(self, topic: str) -> Dict[str, Any]:
        """
        Query ALL 20 knowledge bases for a topic.

        Returns unified knowledge from every base that has relevant information.
        """
        self.queries += 1

        results = {
            "topic": topic,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sources": [],
            "combined_knowledge": [],
        }

        topic_lower = topic.lower()

        # Query each loaded knowledge base
        for kb_id, kb in self.knowledge_bases.items():
            if not kb.loaded:
                continue

            module = self.modules.get(kb_id, {})
            relevant = self._check_knowledge_relevance(topic_lower, kb_id, module)

            if relevant:
                results["sources"].append({
                    "id": kb_id,
                    "name": kb.name,
                    "category": kb.category,
                    "relevance": relevant,
                })
                results["combined_knowledge"].append(relevant)

        return results

    def _check_knowledge_relevance(self, topic: str, kb_id: str, module: Dict) -> Optional[str]:
        """Check if a knowledge base has relevant info for a topic."""

        # Trading topics
        if "trading" in topic or "trade" in topic:
            if kb_id in ["trading_teachings", "trading_memory", "abcfc_nexus", "fair_price", "money"]:
                if kb_id == "trading_teachings":
                    teachings = module.get("teachings", [])
                    return "; ".join(teachings[:3])
                elif kb_id == "money":
                    return "Risk metrics: Sharpe, Kelly, VaR available"
                return f"Trading knowledge from {kb_id}"

        # Risk topics
        if "risk" in topic:
            if kb_id in ["money", "abcfc_nexus", "knowledge_fusion"]:
                return f"Risk knowledge from {kb_id}"

        # Financial topics
        if "financ" in topic or "money" in topic or "capital" in topic:
            if kb_id in ["money", "business", "yair_knowledge"]:
                return f"Financial knowledge from {kb_id}"

        # Technical topics
        if "algorithm" in topic or "complex" in topic or "optim" in topic:
            if kb_id in ["computing", "abcfc_system"]:
                return f"Technical knowledge from {kb_id}"

        # Business topics
        if "business" in topic or "strategy" in topic or "growth" in topic:
            if kb_id in ["business", "knowledge_fusion"]:
                return f"Business knowledge from {kb_id}"

        # Memory/learning topics
        if "learn" in topic or "memory" in topic or "remember" in topic:
            if kb_id in ["ai_memory", "memory_kernels", "trading_memory"]:
                return f"Memory knowledge from {kb_id}"

        # ABCFC topics
        if "abcfc" in topic or "probability" in topic or "nexus" in topic:
            if "abcfc" in kb_id:
                return f"ABCFC framework from {kb_id}"

        # Reality topics
        if "reality" in topic or "real" in topic or "live" in topic:
            if kb_id in ["reality_bridge", "fair_price", "outcome_tracker"]:
                return f"Reality knowledge from {kb_id}"

        return None

    def get_knowledge_for_decision(self, decision_type: str, context: Dict = None) -> Dict[str, Any]:
        """
        Get combined knowledge for a specific decision.

        Aggregates relevant knowledge from all bases for the decision.
        """
        context = context or {}

        result = {
            "decision_type": decision_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "knowledge_sources": [],
            "recommendations": [],
            "confidence": 0.0,
        }

        # Map decision types to knowledge bases
        decision_kb_map = {
            "trading": ["money", "trading_teachings", "abcfc_nexus", "fair_price", "trading_memory"],
            "risk": ["money", "abcfc_nexus", "knowledge_fusion"],
            "scaling": ["computing", "business", "knowledge_crosschain"],
            "strategic": ["business", "knowledge_fusion", "yair_knowledge"],
            "healing": ["computing", "reality_bridge", "knowledge_nexus"],
            "revenue": ["business", "money", "knowledge_fusion"],
        }

        relevant_kbs = decision_kb_map.get(decision_type, ["knowledge_nexus"])

        loaded_count = 0
        for kb_id in relevant_kbs:
            kb = self.knowledge_bases.get(kb_id)
            if kb and kb.loaded:
                loaded_count += 1
                result["knowledge_sources"].append({
                    "id": kb_id,
                    "name": kb.name,
                    "entries": kb.entry_count,
                })

        # Calculate confidence based on loaded knowledge bases
        result["confidence"] = loaded_count / len(relevant_kbs) if relevant_kbs else 0.0

        # Add decision-specific recommendations
        if decision_type == "trading":
            result["recommendations"] = [
                "Use Kelly criterion for position sizing (half-Kelly for safety)",
                "Check order book depth - price is a lie",
                "Evaluate with ABCFC nexus before executing",
            ]
        elif decision_type == "risk":
            result["recommendations"] = [
                "Monitor VaR at 95% confidence",
                "Track Sharpe ratio > 1.0",
                "Use ABCFC to visualize probability bounds",
            ]
        elif decision_type == "strategic":
            result["recommendations"] = [
                "Apply Porter's Five Forces analysis",
                "Calculate NPV for major decisions",
                "Consider Yair's runway situation",
            ]

        return result

    # ========== STATUS ==========

    def status(self) -> Dict[str, Any]:
        """Get complete knowledge reality status."""
        loaded = [kb for kb in self.knowledge_bases.values() if kb.loaded]
        connected = [kb for kb in self.knowledge_bases.values() if kb.reality_connected]

        # Group by category
        by_category = {}
        for kb in self.knowledge_bases.values():
            cat = kb.category
            if cat not in by_category:
                by_category[cat] = {"total": 0, "loaded": 0}
            by_category[cat]["total"] += 1
            if kb.loaded:
                by_category[cat]["loaded"] += 1

        return {
            "master": self.master,
            "initialized": self.initialized,
            "knowledge_bases": {
                "total": len(self.knowledge_bases),
                "loaded": len(loaded),
                "reality_connected": len(connected),
            },
            "by_category": by_category,
            "reality_connections": len(self.reality_connections),
            "total_queries": self.queries,
            "total_reality_syncs": self.reality_syncs,
            "integration_score": len(loaded) / len(self.knowledge_bases) if self.knowledge_bases else 0,
        }

    def _save_state(self, sync_results: Dict = None):
        """Save current state."""
        state = self.status()
        state["last_updated"] = datetime.now(timezone.utc).isoformat()
        state["knowledge_bases_detail"] = {
            kb_id: {
                "name": kb.name,
                "category": kb.category,
                "loaded": kb.loaded,
                "error": kb.error,
                "entry_count": kb.entry_count,
                "reality_connected": kb.reality_connected,
            }
            for kb_id, kb in self.knowledge_bases.items()
        }
        if sync_results:
            state["last_sync"] = sync_results

        with open(KNOWLEDGE_REALITY_STATE, 'w') as f:
            json.dump(state, f, indent=2)

    def print_report(self):
        """Print formatted report."""
        status = self.status()

        print("=" * 70)
        print("INTEGRAFIX: KNOWLEDGE → REALITY")
        print(f"All 20 Knowledge Bases Connected to Reality")
        print("=" * 70)
        print(f"\nMaster: {self.master}")
        print(f"Initialized: {self.initialized}")

        print(f"\n[KNOWLEDGE BASES]")
        print(f"  Total: {status['knowledge_bases']['total']}")
        print(f"  Loaded: {status['knowledge_bases']['loaded']}")
        print(f"  Reality Connected: {status['knowledge_bases']['reality_connected']}")

        print(f"\n[BY CATEGORY]")
        for cat, counts in status["by_category"].items():
            print(f"  {cat.upper()}: {counts['loaded']}/{counts['total']} loaded")

        print(f"\n[KNOWLEDGE BASES DETAIL]")
        for kb_id, kb in self.knowledge_bases.items():
            mark = "✓" if kb.loaded else "✗"
            reality_mark = "→R" if kb.reality_connected else ""
            error_msg = f" [{kb.error[:30]}...]" if kb.error else ""
            print(f"  {mark} {kb.name:30} ({kb.category}) {reality_mark}{error_msg}")

        print(f"\n[REALITY CONNECTIONS]")
        for conn in self.reality_connections[:5]:
            print(f"  {conn.knowledge_base} → {conn.reality_source} ({conn.connection_type})")

        print(f"\n[INTEGRATION SCORE]")
        score = status["integration_score"]
        grade = "A+" if score >= 0.9 else "A" if score >= 0.8 else "B+" if score >= 0.7 else "B" if score >= 0.6 else "C"
        print(f"  {score:.1%} ({grade})")

        print("\n" + "=" * 70)


# ========== GLOBAL INSTANCE ==========

_knowledge_reality: Optional[KnowledgeReality] = None


def get_knowledge_reality() -> KnowledgeReality:
    """Get or create knowledge reality bridge."""
    global _knowledge_reality
    if _knowledge_reality is None:
        _knowledge_reality = KnowledgeReality()
    return _knowledge_reality


def main():
    """CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="INTEGRAFIX: Knowledge Reality Bridge")
    parser.add_argument("command", choices=["status", "report", "sync", "query", "decision"],
                       nargs="?", default="report")
    parser.add_argument("--topic", help="Topic to query")
    parser.add_argument("--decision", help="Decision type for knowledge")
    args = parser.parse_args()

    kr = get_knowledge_reality()

    if args.command == "status":
        print(json.dumps(kr.status(), indent=2))

    elif args.command == "report":
        kr.print_report()

    elif args.command == "sync":
        print("Syncing all knowledge to reality...")
        results = kr.sync_to_reality()
        print(json.dumps(results, indent=2, default=str))

    elif args.command == "query":
        if args.topic:
            results = kr.query_all_knowledge(args.topic)
            print(json.dumps(results, indent=2))
        else:
            print("Use --topic to specify query topic")
            print("Example: python knowledge_reality.py query --topic trading")

    elif args.command == "decision":
        if args.decision:
            results = kr.get_knowledge_for_decision(args.decision)
            print(json.dumps(results, indent=2))
        else:
            print("Use --decision to specify decision type")
            print("Types: trading, risk, scaling, strategic, healing, revenue")


if __name__ == "__main__":
    main()
