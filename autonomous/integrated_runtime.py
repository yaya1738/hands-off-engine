"""Integrated live runtime: legacy infrastructure loop + Factory intelligence loop."""
from __future__ import annotations

from typing import Any, Dict

from .orchestrator import UnifiedAutonomousSystem
from ai.factory.authority_gateway import FactoryAuthorityGateway


class IntegratedAutonomousSystem(UnifiedAutonomousSystem):
    """Run the existing live infrastructure loop and Factory improvement loop together."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.factory_authority = FactoryAuthorityGateway()
        self.stats.update({
            "factory_cycles": 0,
            "factory_improvements": 0,
            "capacity_decisions": 0,
        })

    def _autonomous_cycle(self):
        """Execute infrastructure/health work, then feed its result into Factory learning."""
        super()._autonomous_cycle()
        result: Dict[str, Any] = {
            "success": True,
            "source": "integrated_autonomous_cycle",
            "health": self.last_health or {},
            "infrastructure": self.infra_provisioner.get_infrastructure_status(),
        }
        improvement = self.factory_authority.runtime.run_improvement_cycle(result)
        self.stats["factory_cycles"] += 1
        if isinstance(improvement, dict):
            self.stats["factory_improvements"] += int(bool(improvement.get("success", True)))


def start_live_system(
    budget: float = 500.0,
    auto_provision: bool = True,
    auto_upgrade: bool = True,
    dry_run: bool = False,
):
    """Start the integrated live system through the existing production entrypoint."""
    system = IntegratedAutonomousSystem(
        infrastructure_budget=budget,
        auto_provision=auto_provision,
        auto_upgrade=auto_upgrade,
        dry_run=dry_run,
    )
    system.start()
