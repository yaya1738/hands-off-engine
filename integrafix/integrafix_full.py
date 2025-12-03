#!/usr/bin/env python3
"""
INTEGRAFIX FULL - Complete System Integration
==============================================

Master integration module that wires ALL Integrafix components together.

COMPONENTS (22 total):
======================
1.  methodology.py          - The science of wiring islands
2.  fair_price_estimator.py - Breaking circular edge detection
3.  process_coordinator.py  - Wiring blind processes
4.  trading_pipeline.py     - End-to-end trading flow
5.  ai_memory.py            - Continuity across AI sessions
6.  cron_coordinator.py     - Coordinating autonomous jobs
7.  recursive_engine.py     - Master integrator
8.  outcome_tracker.py      - Trade outcome feedback
9.  trading_memory.py       - Learning from trades
10. edge_executor.py        - Edge-based execution
11. hardware_protection.py  - Hardware shielding
12. branch_manager.py       - Branch coordination
13. branch_consolidator.py  - Branch merging
14. wisdom_bridge.py        - Yair's teachings → signals
15. yair_knowledge_bridge.py - Knowledge integration
16. yair_siegel_integration.py - Full Yair integration
17. yair_financial_abcfc.py - Financial ABCFC
18. abcfc_nexus_bridge.py   - ABCFC nexus wiring
19. abcfc_cloud_bridge.py   - ABCFC cloud wiring
20. startup.py              - Startup coordination
21. system_map.py           - System mapping
22. integrafix_full.py      - THIS FILE - master integration

CLAUDE CLI SESSION INTEGRATION:
===============================
Detects and coordinates multiple Claude CLI sessions for parallel work.

THE EQUATION:
=============
    Integration = Σ(connections) / Σ(potential_connections)
    When Integration → 1.0, the system becomes whole.

Created for: Yair Siegel
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import importlib

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
INTEGRAFIX_STATE = STATE_DIR / "integrafix_full.json"

sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class ComponentStatus:
    """Status of an Integrafix component."""
    name: str
    module_path: str
    loaded: bool = False
    runnable: bool = False
    last_run: Optional[str] = None
    result: Optional[Dict] = None
    error: Optional[str] = None


@dataclass
class ClaudeSession:
    """A Claude CLI session."""
    pid: int
    cwd: str
    started: str
    command: str
    active: bool = True


class IntegrafixFull:
    """
    Master integration for ALL Integrafix components.

    This is THE unified entry point for:
    - All 22 Integrafix modules
    - Multiple Claude CLI sessions
    - Complete system integration
    """

    def __init__(self):
        self.state = self._load_state()
        self.components: Dict[str, ComponentStatus] = {}
        self.claude_sessions: List[ClaudeSession] = []
        self._modules = {}

    def _load_state(self) -> Dict:
        if INTEGRAFIX_STATE.exists():
            with open(INTEGRAFIX_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "integration_runs": 0,
            "last_run": None,
            "integration_score": 0.0,
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.state["components"] = {
            name: {
                "loaded": c.loaded,
                "runnable": c.runnable,
                "last_run": c.last_run,
                "error": c.error,
            }
            for name, c in self.components.items()
        }
        with open(INTEGRAFIX_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    # ==================== COMPONENT LOADING ====================

    def load_all_components(self) -> Dict[str, bool]:
        """Load all Integrafix components."""
        components = [
            ("methodology", "integrafix.methodology", "get_methodology"),
            ("fair_price_estimator", "integrafix.fair_price_estimator", "get_estimator"),
            ("process_coordinator", "integrafix.process_coordinator", "get_coordinator"),
            ("trading_pipeline", "integrafix.trading_pipeline", "get_pipeline"),
            ("ai_memory", "integrafix.ai_memory", "get_memory"),
            ("cron_coordinator", "integrafix.cron_coordinator", "get_coordinator"),
            ("recursive_engine", "integrafix.recursive_engine", "get_engine"),
            ("outcome_tracker", "integrafix.outcome_tracker", "OutcomeTracker"),
            ("trading_memory", "integrafix.trading_memory", "TradingMemory"),
            ("edge_executor", "integrafix.edge_executor", "EdgeExecutor"),
            ("hardware_protection", "integrafix.hardware_protection", "HardwareProtection"),
            ("branch_manager", "integrafix.branch_manager", "BranchManager"),
            ("branch_consolidator", "integrafix.branch_consolidator", "BranchConsolidator"),
            ("wisdom_bridge", "integrafix.wisdom_bridge", "WisdomBridge"),
            ("yair_knowledge_bridge", "integrafix.yair_knowledge_bridge", "get_yair_knowledge_bridge"),
            ("yair_siegel_integration", "integrafix.yair_siegel_integration", "get_yair_integration"),
            ("yair_financial_abcfc", "integrafix.yair_financial_abcfc", "get_yair_financial"),
            ("abcfc_nexus_bridge", "integrafix.abcfc_nexus_bridge", "ABCFCNexusBridge"),
            ("abcfc_cloud_bridge", "integrafix.abcfc_cloud_bridge", "ABCFCCloudBridge"),
            ("startup", "integrafix.startup", "StartupCoordinator"),
            ("system_map", "integrafix.system_map", "get_system_map"),
        ]

        results = {}

        for name, module_path, factory in components:
            status = ComponentStatus(
                name=name,
                module_path=module_path,
            )

            try:
                module = importlib.import_module(module_path)
                self._modules[name] = module
                status.loaded = True

                # Check if runnable
                if hasattr(module, factory):
                    status.runnable = True

            except Exception as e:
                status.error = str(e)[:100]

            self.components[name] = status
            results[name] = status.loaded

        return results

    # ==================== CLAUDE CLI SESSION DETECTION ====================

    def detect_claude_sessions(self) -> List[ClaudeSession]:
        """Detect all running Claude CLI sessions."""
        self.claude_sessions = []

        try:
            # Find Claude processes
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                timeout=10
            )

            for line in result.stdout.split('\n'):
                if 'claude' in line.lower() and ('node' in line or 'npx' in line):
                    parts = line.split()
                    if len(parts) >= 11:
                        pid = int(parts[1])
                        cmd = ' '.join(parts[10:])

                        # Get working directory
                        try:
                            cwd_result = subprocess.run(
                                ["readlink", "-f", f"/proc/{pid}/cwd"],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            cwd = cwd_result.stdout.strip() or "unknown"
                        except:
                            cwd = "unknown"

                        self.claude_sessions.append(ClaudeSession(
                            pid=pid,
                            cwd=cwd,
                            started=datetime.now(timezone.utc).isoformat(),
                            command=cmd[:100],
                            active=True,
                        ))

        except Exception as e:
            pass

        return self.claude_sessions

    def get_claude_session_info(self) -> Dict:
        """Get information about all Claude sessions."""
        self.detect_claude_sessions()

        return {
            "total_sessions": len(self.claude_sessions),
            "sessions": [
                {
                    "pid": s.pid,
                    "cwd": s.cwd,
                    "command": s.command,
                }
                for s in self.claude_sessions
            ],
            "can_coordinate": len(self.claude_sessions) >= 2,
        }

    def coordinate_sessions(self, task_distribution: Dict[str, str] = None) -> Dict:
        """
        Coordinate multiple Claude sessions for parallel work.

        Args:
            task_distribution: Map of session_id -> task assignment

        Returns:
            Coordination results
        """
        sessions = self.detect_claude_sessions()

        if len(sessions) < 2:
            return {
                "success": False,
                "error": "Need at least 2 Claude sessions for coordination",
                "sessions_found": len(sessions),
            }

        # Create coordination state file
        coordination_state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sessions": [
                {"pid": s.pid, "cwd": s.cwd, "status": "ready"}
                for s in sessions
            ],
            "tasks": task_distribution or {},
            "sync_point": "integrafix_coordination",
        }

        # Write to shared state
        coord_file = STATE_DIR / "claude_coordination.json"
        with open(coord_file, 'w') as f:
            json.dump(coordination_state, f, indent=2)

        return {
            "success": True,
            "sessions_coordinated": len(sessions),
            "coordination_file": str(coord_file),
            "tasks_assigned": len(task_distribution) if task_distribution else 0,
        }

    # ==================== COMPONENT EXECUTION ====================

    def run_component(self, name: str) -> Dict:
        """Run a specific Integrafix component."""
        if name not in self.components:
            return {"success": False, "error": f"Unknown component: {name}"}

        comp = self.components[name]
        if not comp.loaded:
            return {"success": False, "error": f"Component not loaded: {name}"}

        try:
            module = self._modules.get(name)
            if not module:
                return {"success": False, "error": f"Module not found: {name}"}

            result = {"success": True, "component": name}

            # Component-specific execution
            if name == "methodology":
                m = module.get_methodology()
                result["integration_score"] = m.calculate_integration_score()
                result["islands"] = m.find_integration_islands()

            elif name == "fair_price_estimator":
                e = module.get_estimator()
                result["methods_available"] = len(e.methods)

            elif name == "trading_pipeline":
                p = module.get_pipeline()
                result["state"] = p.state

            elif name == "ai_memory":
                m = module.get_memory()
                result["memory_count"] = len(m.memories)

            elif name == "recursive_engine":
                e = module.get_engine()
                cycle_result = e.run_cycle()
                result["cycle_result"] = cycle_result

            elif name == "outcome_tracker":
                t = module.OutcomeTracker()
                status = t.status()
                result["pending_trades"] = status.get("pending_trades", 0)

            elif name == "yair_financial_abcfc":
                f = module.get_yair_financial()
                summary = f.get_summary()
                result["total_expected"] = summary["total_finance"]["expected"]
                result["net_expected"] = summary["net_expected"]

            elif name == "system_map":
                m = module.get_system_map()
                report = m.generate_report()
                result["scores"] = report["scores"]

            else:
                result["status"] = "loaded_only"

            comp.last_run = datetime.now(timezone.utc).isoformat()
            comp.result = result

            return result

        except Exception as e:
            comp.error = str(e)
            return {"success": False, "error": str(e)}

    def run_all_components(self) -> Dict:
        """Run all Integrafix components."""
        results = {}
        successes = 0
        failures = 0

        for name in self.components:
            result = self.run_component(name)
            results[name] = result

            if result.get("success"):
                successes += 1
            else:
                failures += 1

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total": len(self.components),
            "successes": successes,
            "failures": failures,
            "success_rate": successes / len(self.components) if self.components else 0,
            "results": results,
        }

    # ==================== FULL INTEGRATION RUN ====================

    def run_full_integration(self) -> Dict:
        """Run complete Integrafix integration."""
        timestamp = datetime.now(timezone.utc).isoformat()

        results = {
            "timestamp": timestamp,
            "phase_1_loading": {},
            "phase_2_claude_sessions": {},
            "phase_3_execution": {},
            "phase_4_scoring": {},
            "summary": {},
        }

        # Phase 1: Load all components
        print("[1/4] Loading all Integrafix components...")
        load_results = self.load_all_components()
        loaded = sum(1 for v in load_results.values() if v)
        results["phase_1_loading"] = {
            "total": len(load_results),
            "loaded": loaded,
            "success_rate": loaded / len(load_results) if load_results else 0,
        }

        # Phase 2: Detect Claude sessions
        print("[2/4] Detecting Claude CLI sessions...")
        session_info = self.get_claude_session_info()
        results["phase_2_claude_sessions"] = session_info

        # Phase 3: Execute key components
        print("[3/4] Running key components...")
        key_components = [
            "methodology",
            "trading_pipeline",
            "yair_financial_abcfc",
            "outcome_tracker",
            "system_map",
        ]

        execution_results = {}
        for comp in key_components:
            if comp in self.components and self.components[comp].loaded:
                execution_results[comp] = self.run_component(comp)

        results["phase_3_execution"] = execution_results

        # Phase 4: Calculate integration score
        print("[4/4] Calculating integration score...")
        try:
            system_map = self._modules.get("system_map")
            if system_map:
                smap = system_map.get_system_map()
                report = smap.generate_report()
                results["phase_4_scoring"] = report["scores"]
        except Exception as e:
            results["phase_4_scoring"] = {"error": str(e)}

        # Summary
        results["summary"] = {
            "components_loaded": results["phase_1_loading"]["loaded"],
            "components_total": results["phase_1_loading"]["total"],
            "claude_sessions": results["phase_2_claude_sessions"]["total_sessions"],
            "integration_grade": results["phase_4_scoring"].get("grade", "N/A"),
            "integration_score": results["phase_4_scoring"].get("overall", 0),
        }

        # Update state
        self.state["integration_runs"] += 1
        self.state["last_run"] = timestamp
        self.state["integration_score"] = results["summary"]["integration_score"]
        self._save_state()

        return results

    # ==================== STATUS ====================

    def status(self) -> Dict:
        """Get full Integrafix status."""
        self.detect_claude_sessions()

        loaded = sum(1 for c in self.components.values() if c.loaded)
        runnable = sum(1 for c in self.components.values() if c.runnable)

        return {
            "success": True,
            "components_loaded": loaded,
            "components_total": len(self.components),
            "components_runnable": runnable,
            "claude_sessions": len(self.claude_sessions),
            "integration_runs": self.state.get("integration_runs", 0),
            "integration_score": self.state.get("integration_score", 0),
            "last_run": self.state.get("last_run"),
        }

    def print_status(self):
        """Print formatted status."""
        print("=" * 70)
        print("INTEGRAFIX FULL - COMPLETE SYSTEM STATUS")
        print("=" * 70)

        # Load components first
        self.load_all_components()
        status = self.status()

        print(f"\n[COMPONENTS]")
        print(f"  Loaded:   {status['components_loaded']}/{status['components_total']}")
        print(f"  Runnable: {status['components_runnable']}")

        print(f"\n[CLAUDE SESSIONS]")
        print(f"  Active: {status['claude_sessions']}")
        for s in self.claude_sessions:
            print(f"    PID {s.pid}: {s.cwd}")

        print(f"\n[INTEGRATION]")
        print(f"  Runs: {status['integration_runs']}")
        print(f"  Score: {status['integration_score']:.1%}")
        print(f"  Last: {status['last_run'] or 'Never'}")

        print(f"\n[COMPONENT STATUS]")
        for name, comp in sorted(self.components.items()):
            icon = "✓" if comp.loaded else "✗"
            print(f"  {icon} {name}")
            if comp.error:
                print(f"      Error: {comp.error[:50]}...")

        print("\n" + "=" * 70)


# ==================== SINGLETON & BACKEND LOOP FUNCTION ====================

_integrafix_full: Optional[IntegrafixFull] = None


def get_integrafix_full() -> IntegrafixFull:
    """Get or create Integrafix Full singleton."""
    global _integrafix_full
    if _integrafix_full is None:
        _integrafix_full = IntegrafixFull()
        _integrafix_full.load_all_components()
    return _integrafix_full


def run_integrafix_full() -> Dict:
    """Run Integrafix Full for backend loop integration."""
    integrafix = get_integrafix_full()
    return integrafix.status()


def main():
    """Run full Integrafix integration."""
    import argparse

    parser = argparse.ArgumentParser(description="INTEGRAFIX Full Integration")
    parser.add_argument("command", choices=["status", "run", "sessions", "coordinate"],
                       default="status", nargs="?")
    args = parser.parse_args()

    integrafix = get_integrafix_full()

    if args.command == "status":
        integrafix.print_status()

    elif args.command == "run":
        print("Running FULL Integrafix integration...")
        results = integrafix.run_full_integration()

        print("\n" + "=" * 70)
        print("INTEGRATION COMPLETE")
        print("=" * 70)
        summary = results["summary"]
        print(f"  Components: {summary['components_loaded']}/{summary['components_total']}")
        print(f"  Claude Sessions: {summary['claude_sessions']}")
        print(f"  Integration Grade: {summary['integration_grade']}")
        print(f"  Integration Score: {summary['integration_score']:.1%}")

    elif args.command == "sessions":
        info = integrafix.get_claude_session_info()
        print(f"\nClaude CLI Sessions: {info['total_sessions']}")
        for s in info["sessions"]:
            print(f"  PID {s['pid']}: {s['cwd']}")

    elif args.command == "coordinate":
        result = integrafix.coordinate_sessions()
        if result["success"]:
            print(f"Coordinating {result['sessions_coordinated']} sessions")
            print(f"State file: {result['coordination_file']}")
        else:
            print(f"Error: {result['error']}")


if __name__ == "__main__":
    main()
