"""Capability-composition intelligence for the unified Factory runtime.

Turns the existing capability inventory into a reusable search space: for each
objective, rank small compositions of capabilities before creating anything
new. This module is decision-only; execution remains governed by the gateway.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Dict, Iterable, List


@dataclass(frozen=True)
class CapabilityRoute:
    capabilities: tuple[str, ...]
    score: float
    rationale: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "capabilities": list(self.capabilities),
            "score": round(self.score, 4),
            "rationale": self.rationale,
        }


class FactoryCapabilityComposition:
    """Find short paths through capabilities already present in the runtime."""

    SIGNALS = {
        "discover": ("discovery", "capability", "knowledge", "web", "research"),
        "build": ("development", "coding", "software", "artifact", "implementation"),
        "decide": ("decision", "optimization", "abcfc", "planning", "simulation"),
        "money": ("capital", "finance", "revenue", "market", "money", "economic"),
        "compute": ("resource", "compute", "hardware", "capacity"),
        "recover": ("failure", "repair", "healing", "recovery", "integrity"),
        "learn": ("learning", "feedback", "experience", "improvement", "adaptation"),
        "execute": ("execution", "orchestration", "authority", "action", "operations"),
    }

    def __init__(self, runtime):
        self.runtime = runtime

    def _inventory(self) -> List[str]:
        try:
            return list(self.runtime.component_inventory().get("components", []))
        except Exception:
            return []

    def _kind(self, name: str) -> str:
        lowered = name.casefold()
        for kind, words in self.SIGNALS.items():
            if any(word in lowered for word in words):
                return kind
        return "general"

    def rank(self, objective: str, max_width: int = 3, limit: int = 12) -> List[Dict[str, Any]]:
        text = str(objective).casefold()
        inventory = self._inventory()
        candidates = [(name, self._kind(name)) for name in inventory]
        relevant = [(n, k) for n, k in candidates if k != "general"] or candidates
        routes: List[CapabilityRoute] = []

        target_kinds = {kind for kind, words in self.SIGNALS.items() if any(w in text for w in words)}
        if not target_kinds:
            target_kinds = {"discover", "decide", "execute", "learn"}

        for width in range(1, min(max_width, len(relevant)) + 1):
            for combo in combinations(relevant, width):
                kinds = {k for _, k in combo}
                coverage = len(kinds & target_kinds) / max(1, len(target_kinds))
                diversity = len(kinds) / width
                score = 0.70 * coverage + 0.30 * diversity
                if "execute" in kinds:
                    score += 0.05
                routes.append(CapabilityRoute(
                    tuple(n for n, _ in combo), score,
                    f"compose {', '.join(kinds)} for objective signals {', '.join(sorted(target_kinds))}",
                ))

        routes.sort(key=lambda r: (-r.score, len(r.capabilities), r.capabilities))
        return [route.as_dict() for route in routes[:limit]]

    def analyze(self, objective: str) -> Dict[str, Any]:
        ranked = self.rank(objective)
        return {
            "objective": str(objective),
            "strategy": "compose_existing_capabilities_before_creating_new_capability",
            "inventory_size": len(self._inventory()),
            "routes_considered": len(ranked),
            "recommended_route": ranked[0] if ranked else None,
            "alternatives": ranked[1:],
        }
