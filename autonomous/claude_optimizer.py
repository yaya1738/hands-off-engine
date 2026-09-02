#!/usr/bin/env python3
"""Legacy Claude optimizer facade; authority lives in FactoryAuthorityGateway."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = BASE_DIR / "state"
MASTER = "Yair Siegel"
OPTIMIZER_STATE_FILE = STATE_DIR / "claude_optimizer.json"


class ClaudeOptimizer:
    """Read-only context/validation facade. Legacy mutation is fail-closed."""

    def __init__(self):
        self.state = self._load_state()
        self.context = self._build_context()

    def _load_state(self) -> Dict:
        if OPTIMIZER_STATE_FILE.exists():
            try:
                return json.loads(OPTIMIZER_STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"master": MASTER, "sessions_optimized": 0, "last_optimization": None, "rules_enforced": 0}

    def _build_context(self) -> Dict:
        return {
            "master": MASTER,
            "system_name": "hands-off-engine",
            "purpose": "Autonomous trading and infrastructure management",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "financial": self._get_financial_state(),
            "infrastructure": self._get_infrastructure_state(),
            "protections": self._get_protection_status(),
            "agents": [],
            "rules": self._get_system_rules(),
        }

    def _read_json(self, path: Path):
        try:
            return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        except Exception:
            return None

    def _get_financial_state(self) -> Dict:
        for name, source in (("polymarket-model.json", "polymarket"), ("brain_state.json", "brain")):
            data = self._read_json(STATE_DIR / name)
            if data is not None:
                return {"balance": data.get("balance", 0), "positions": data.get("active_positions", len(data.get("positions", []))), "source": source}
        return {"balance": "unknown", "positions": "unknown", "source": "none"}

    def _get_infrastructure_state(self) -> Dict:
        data = self._read_json(STATE_DIR / "infra_state.json")
        if data is not None:
            return {"nodes": data.get("healthy_nodes", 0), "total": data.get("total_nodes", 0), "primary": data.get("primary", "unknown")}
        return {"nodes": "unknown", "total": "unknown"}

    def _get_protection_status(self) -> Dict:
        protections = {}
        for key, module, getter in (("self_preservation", "autonomous.self_preservation", "get_preservation"), ("system_immunity", "autonomous.security_layer", "get_immunity"), ("harm_prevention", "autonomous.harm_prevention", "get_harm_prevention")):
            try:
                mod = __import__(module, fromlist=[getter])
                status = getattr(mod, getter)().get_status()
                protections[key] = {"enabled": status.get("enabled", True), "blocked_count": status.get("blocked_count", status.get("blocked_commands", status.get("harmful_changes", 0)))}
            except Exception:
                protections[key] = {"enabled": "unknown"}
        return protections

    def _get_system_rules(self) -> List[str]:
        return [
            "All changes go through FactoryAuthorityGateway before execution.",
            "Legacy ClaudeOptimizer execution and file mutation are disabled.",
            "When in doubt, preserve system stability over action.",
            "Document significant changes.",
        ]

    def get_system_prompt_prefix(self) -> str:
        fin, infra, prots = self.context["financial"], self.context["infrastructure"], self.context["protections"]
        rules = "\n".join(f"{i}. {r}" for i, r in enumerate(self.context["rules"], 1))
        return f"# SYSTEM CONTEXT - HANDS-OFF ENGINE\n\nMaster: {MASTER}\nBalance: ${fin.get('balance', 'unknown')}\nActive Positions: {fin.get('positions', 'unknown')}\nInfrastructure: {infra.get('nodes', '?')}/{infra.get('total', '?')} nodes healthy\nProtections: {prots}\n\n## Critical Rules\n{rules}\n\nTimestamp: {self.context['timestamp']}\n"

    def get_context_json(self) -> str:
        return json.dumps(self.context, indent=2)

    def validate_action(self, action_type: str, target: str, **kwargs) -> Tuple[bool, str]:
        try:
            from autonomous.self_preservation import block_self_harm
            allowed, reason = block_self_harm(action_type, target, **kwargs)
            if not allowed:
                return False, f"[SELF-PRESERVATION] {reason}"
        except Exception:
            pass
        try:
            from autonomous.security_layer import get_immunity
            immunity = get_immunity()
            if action_type == "execute_command":
                allowed, reason = immunity.validate_command(target)
            elif action_type in {"write_code", "modify_code"}:
                allowed, reason = immunity.validate_code(target)
            else:
                allowed, reason = True, "ok"
            if not allowed:
                return False, f"[SYSTEM-IMMUNITY] {reason}"
        except Exception:
            pass
        return True, "Action validated; legacy mutation remains disabled"

    def safe_execute(self, command: str) -> Tuple[bool, str]:
        allowed, reason = self.validate_action("execute_command", command)
        if not allowed:
            return False, reason
        return False, "[FACTORY-AUTHORITY] Legacy ClaudeOptimizer execution is disabled; submit through FactoryAuthorityGateway."

    def safe_file_modify(self, file_path: str, intention: str) -> Tuple[bool, str]:
        allowed, reason = self.validate_action("modify_file", file_path, intention=intention)
        if not allowed:
            return False, reason
        return False, "[FACTORY-AUTHORITY] Legacy ClaudeOptimizer file mutation is disabled; submit through FactoryAuthorityGateway."

    def update_claude_instructions(self):
        return False

    def get_status(self) -> Dict:
        return {
            "master": MASTER,
            "sessions_optimized": self.state.get("sessions_optimized", 0),
            "last_optimization": self.state.get("last_optimization"),
            "context_age_seconds": self._get_context_age(),
            "protection_layers": len(self.context.get("protections", {})),
            "active_agents": 0,
            "rules_count": len(self.context.get("rules", [])),
        }

    def _get_context_age(self) -> float:
        try:
            ts = datetime.fromisoformat(self.context["timestamp"])
            return (datetime.now(timezone.utc) - ts).total_seconds()
        except Exception:
            return -1


_optimizer = None


def get_optimizer() -> ClaudeOptimizer:
    global _optimizer
    if _optimizer is None:
        _optimizer = ClaudeOptimizer()
    return _optimizer


def optimize_claude():
    return False


def get_system_context() -> str:
    return get_optimizer().get_system_prompt_prefix()


def validate_claude_action(action_type: str, target: str, **kwargs) -> Tuple[bool, str]:
    return get_optimizer().validate_action(action_type, target, **kwargs)


if __name__ == "__main__":
    print("[FACTORY-AUTHORITY] Legacy ClaudeOptimizer mutation/execution is disabled.")
