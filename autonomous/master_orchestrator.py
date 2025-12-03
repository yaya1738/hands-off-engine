#!/usr/bin/env python3
"""
Master Orchestrator - Ultimate System Control
Runs ALL autonomous systems in coordinated sequence.

Serving: Yair Siegel
"""

import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
sys.path.insert(0, str(PROJECT_ROOT))

MASTER = "Yair Siegel"
ORCHESTRATOR_STATE = STATE_DIR / "master_orchestrator.json"


class MasterOrchestrator:
    """Coordinate all autonomous systems."""

    def __init__(self):
        self.results = {}
        self.errors = []

    def _run_system(self, name: str, func) -> Dict:
        """Run a system and capture results."""
        try:
            print(f"\n{'='*60}")
            print(f"RUNNING: {name}")
            print('='*60)
            result = func()
            return {"status": "success", "result": result}
        except Exception as e:
            self.errors.append({"system": name, "error": str(e)})
            print(f"ERROR in {name}: {e}")
            return {"status": "error", "error": str(e)}

    def run_all(self) -> Dict:
        """Run all autonomous systems."""
        print("=" * 70)
        print("MASTER ORCHESTRATOR - FULL SYSTEM EXECUTION")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)

        # 1. System Dashboard
        try:
            from autonomous.system_dashboard import print_dashboard
            self.results["dashboard"] = self._run_system("System Dashboard", print_dashboard)
        except ImportError as e:
            self.results["dashboard"] = {"status": "import_error", "error": str(e)}

        # 2. Reality Feedback
        try:
            from autonomous.reality_feedback import RealityFeedback
            rf = RealityFeedback()
            self.results["reality"] = self._run_system("Reality Feedback", rf.reality_check)
        except ImportError as e:
            self.results["reality"] = {"status": "import_error", "error": str(e)}

        # 3. Conversion Optimizer
        try:
            from autonomous.conversion_optimizer import ConversionOptimizer
            co = ConversionOptimizer()
            self.results["conversion"] = self._run_system("Conversion Optimizer", co.adapt_now)
        except ImportError as e:
            self.results["conversion"] = {"status": "import_error", "error": str(e)}

        # 4. Active Pursuit
        try:
            from autonomous.active_pursuit import ActivePursuit
            ap = ActivePursuit()
            self.results["pursuit"] = self._run_system("Active Pursuit", ap.pursue_actively)
        except ImportError as e:
            self.results["pursuit"] = {"status": "import_error", "error": str(e)}

        # 5. Aggressive Executor
        try:
            from autonomous.aggressive_executor import AggressiveExecutor
            ae = AggressiveExecutor()
            self.results["aggressive"] = self._run_system("Aggressive Executor", ae.execute_sprint)
        except ImportError as e:
            self.results["aggressive"] = {"status": "import_error", "error": str(e)}

        # 6. Trade Executor
        try:
            from autonomous.trade_executor import TradeExecutor
            te = TradeExecutor()
            self.results["trading"] = self._run_system("Trade Executor", te.run_trading_cycle)
        except ImportError as e:
            self.results["trading"] = {"status": "import_error", "error": str(e)}

        # 7. Web Executor
        try:
            from autonomous.web_executor import WebExecutor
            we = WebExecutor()
            self.results["web"] = self._run_system("Web Executor", lambda: {
                "github": we.execute_github_contribution(),
                "content": we.generate_content_for_platforms(),
                "freelance": we.scan_freelance_platforms()
            })
        except ImportError as e:
            self.results["web"] = {"status": "import_error", "error": str(e)}

        # 8. Income Accelerator
        try:
            from autonomous.income_accelerator import IncomeAccelerator
            ia = IncomeAccelerator()
            self.results["income"] = self._run_system("Income Accelerator", ia.execute_income_sprint)
        except ImportError as e:
            self.results["income"] = {"status": "import_error", "error": str(e)}

        # 9. Learning Engine
        try:
            from autonomous.learning_engine import LearningEngine
            le = LearningEngine()
            self.results["learning"] = self._run_system("Learning Engine", le.run_learning_cycle)
        except ImportError as e:
            self.results["learning"] = {"status": "import_error", "error": str(e)}

        # 10. Self Modification
        try:
            from autonomous.self_modification import SelfModificationEngine
            sme = SelfModificationEngine()
            self.results["self_mod"] = self._run_system(
                "Self Modification",
                sme.verify_self_modification_capability
            )
        except ImportError as e:
            self.results["self_mod"] = {"status": "import_error", "error": str(e)}

        # Summary
        print("\n" + "=" * 70)
        print("ORCHESTRATION COMPLETE")
        print("=" * 70)

        successful = sum(1 for r in self.results.values() if r.get("status") == "success")
        failed = sum(1 for r in self.results.values() if r.get("status") != "success")

        print(f"\n  Systems run: {len(self.results)}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Errors: {len(self.errors)}")

        if self.errors:
            print("\n  ERRORS:")
            for err in self.errors[:5]:
                print(f"    - {err['system']}: {err['error'][:50]}")

        # Save state
        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "master": MASTER,
            "systems_run": len(self.results),
            "successful": successful,
            "failed": failed,
            "errors": self.errors[:10]
        }
        with open(ORCHESTRATOR_STATE, 'w') as f:
            json.dump(state, f, indent=2)

        return {
            "timestamp": state["timestamp"],
            "summary": {
                "total": len(self.results),
                "successful": successful,
                "failed": failed
            },
            "errors": self.errors
        }


def main():
    orchestrator = MasterOrchestrator()
    return orchestrator.run_all()


if __name__ == "__main__":
    main()
