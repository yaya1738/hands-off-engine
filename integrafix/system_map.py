#!/usr/bin/env python3
"""
INTEGRAFIX: System Map & Navigability
======================================

Complete mapping of the hands-off-engine with:
1. Component inventory
2. Connection analysis
3. Navigability paths
4. Integration scores

Serving: Yair Siegel
"""

import json
import importlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import re

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"


class SystemMap:
    """
    Complete system mapping for INTEGRAFIX navigability.
    """

    def __init__(self):
        self.components = {}
        self.connections = defaultdict(set)
        self.import_status = {}

    def scan_components(self) -> Dict:
        """Scan all components in the system."""
        directories = [
            ("autonomous", "Core autonomous systems - self-healing, brain, executor"),
            ("integrafix", "INTEGRAFIX bridges - system wiring"),
            ("trading", "Trading systems - market data, pipeline"),
            ("ai", "AI orchestration - routing, coordination"),
            ("ai_nexus", "AI knowledge nexus - kernels, learning"),
            ("executor", "Trade execution - math, safeguards, polymarket"),
            ("alpha", "Signal generation - alpha models, insights"),
            ("finance", "Financial tracking - costs, ledger"),
            ("health", "Health monitoring - checks, bridges"),
            ("infrastructure", "Infrastructure - errors, state, scaling"),
            ("audit", "Audit logging - events, compliance"),
            ("security", "Security layer - identity, protection"),
            ("hardware", "Hardware control - monitor, kernel"),
            ("scheduler", "Task scheduling - process bridge"),
            ("fetchers", "Data fetchers - market data"),
            ("arbitrage", "Arbitrage detection - merge arb"),
            ("decider", "Decision engine"),
            ("telegram", "Telegram bot interface"),
        ]

        for dir_name, description in directories:
            dir_path = PROJECT_ROOT / dir_name
            if dir_path.exists():
                py_files = [f for f in dir_path.rglob("*.py")
                           if "__pycache__" not in str(f)]
                self.components[dir_name] = {
                    "path": str(dir_path),
                    "description": description,
                    "files": len(py_files),
                    "modules": [f.stem for f in py_files[:10]],  # First 10
                }

        return self.components

    def analyze_connections(self) -> Dict:
        """Analyze import connections between components."""
        key_dirs = list(self.components.keys())

        for dir_name in key_dirs:
            dir_path = PROJECT_ROOT / dir_name
            if not dir_path.exists():
                continue

            for py_file in dir_path.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue

                try:
                    content = py_file.read_text()

                    for target_dir in key_dirs:
                        if target_dir == dir_name:
                            continue

                        patterns = [
                            rf'from {target_dir}\.',
                            rf'from {target_dir} import',
                            rf'import {target_dir}\.',
                        ]

                        for pattern in patterns:
                            if re.search(pattern, content):
                                self.connections[dir_name].add(target_dir)
                                break
                except:
                    pass

        return dict(self.connections)

    def test_imports(self) -> Dict:
        """Test which key modules are importable."""
        modules_to_test = [
            "autonomous.self_healer",
            "autonomous.hardware_brain",
            "autonomous.concrete_executor",
            "autonomous.probability_calibrator",
            "autonomous.self_preservation",
            "autonomous.harm_prevention",
            "autonomous.skill_growth_tracker",
            "autonomous.task_coordinator",
            "integrafix.outcome_tracker",
            "integrafix.trading_pipeline",
            "integrafix.hardware_protection",
            "integrafix.abcfc_cloud_bridge",
            "integrafix.fair_price_estimator",
            "trading.market_data_pipeline",
            "ai.ai_orchestrator",
            "ai_nexus.nexus",
            "executor.math.abcfc_nexus",
            "executor.math.abcfc_system",
            "finance.cost_tracker",
            "infrastructure.error_management",
            "infrastructure.state_backend",
            "health.monitoring_bridge",
            "audit.audit_logger",
        ]

        for module_name in modules_to_test:
            try:
                importlib.import_module(module_name)
                self.import_status[module_name] = {"ok": True}
            except Exception as e:
                self.import_status[module_name] = {
                    "ok": False,
                    "error": str(e)[:100]
                }

        return self.import_status

    def get_navigation_paths(self) -> Dict:
        """Get navigation paths through the system."""
        return {
            "TRADING_FLOW": {
                "description": "Signal → Execute → Record → Learn",
                "path": [
                    ("alpha", "Generate trading signals"),
                    ("executor.trading_safeguards", "Risk check"),
                    ("autonomous.concrete_executor", "Execute trade"),
                    ("integrafix.outcome_tracker", "Record outcome"),
                    ("autonomous.skill_growth_tracker", "Learn from result"),
                ]
            },
            "AI_FLOW": {
                "description": "Route → Consult → Learn",
                "path": [
                    ("ai.ai_orchestrator", "Route AI requests"),
                    ("ai_nexus.nexus", "Consult knowledge"),
                    ("ai_nexus.kernels", "Access kernels"),
                    ("ai_nexus.feedback_loop", "Update learnings"),
                ]
            },
            "ABCFC_FLOW": {
                "description": "Hierarchy → Cloud → Navigate → Decide",
                "path": [
                    ("executor.math.abcfc_system", "Build hierarchy"),
                    ("executor.math.abcfc_nexus", "Evaluate futures"),
                    ("executor.math.abcfc_cloud_flyer", "Navigate cloud"),
                    ("integrafix.abcfc_cloud_bridge", "Wire to trading"),
                ]
            },
            "HEALTH_FLOW": {
                "description": "Monitor → Heal → Protect",
                "path": [
                    ("health.monitoring_bridge", "Monitor health"),
                    ("autonomous.self_healer", "Self-heal issues"),
                    ("autonomous.hardware_brain", "Manage hardware"),
                    ("infrastructure.error_management", "Track errors"),
                ]
            },
            "PROTECTION_FLOW": {
                "description": "Preserve → Prevent → Shield",
                "path": [
                    ("autonomous.self_preservation", "Preserve system"),
                    ("autonomous.harm_prevention", "Prevent harm"),
                    ("integrafix.hardware_protection", "Shield hardware"),
                ]
            },
        }

    def get_entry_points(self) -> List[Dict]:
        """Get system entry points."""
        return [
            {
                "name": "Cron Jobs",
                "type": "scheduled",
                "description": "31+ scheduled tasks running automatically",
                "access": "crontab -l",
            },
            {
                "name": "Background Daemons",
                "type": "persistent",
                "description": "hardware_brain, self_healer, backend_loop, etc.",
                "access": "ps aux | grep hands-off",
            },
            {
                "name": "Telegram Bot",
                "type": "interactive",
                "description": "User interface via Telegram",
                "access": "telegram/telegram_unified.py",
            },
            {
                "name": "CLI Scripts",
                "type": "manual",
                "description": "Manual execution scripts",
                "access": "scripts/*.sh",
            },
            {
                "name": "INTEGRAFIX Bridges",
                "type": "wiring",
                "description": "20 integration bridges",
                "access": "integrafix/*.py",
            },
        ]

    def calculate_scores(self) -> Dict:
        """Calculate integration and navigability scores."""
        # Connectivity score
        total_possible = len(self.components) * (len(self.components) - 1)
        total_connections = sum(len(t) for t in self.connections.values())
        connectivity = total_connections / total_possible if total_possible > 0 else 0

        # Import success rate
        import_success = sum(1 for s in self.import_status.values() if s.get("ok")) / len(self.import_status) if self.import_status else 0

        # INTEGRAFIX coverage (bridges / total dirs)
        integrafix_bridges = self.components.get("integrafix", {}).get("files", 0)
        integrafix_coverage = min(1.0, integrafix_bridges / len(self.components))

        # Overall score
        overall = (connectivity * 0.3 + import_success * 0.4 + integrafix_coverage * 0.3)

        return {
            "connectivity": connectivity,
            "import_success": import_success,
            "integrafix_coverage": integrafix_coverage,
            "overall": overall,
            "grade": self._score_to_grade(overall),
        }

    def _score_to_grade(self, score: float) -> str:
        if score >= 0.9: return "A+"
        if score >= 0.8: return "A"
        if score >= 0.7: return "B+"
        if score >= 0.6: return "B"
        if score >= 0.5: return "C"
        return "D"

    def generate_report(self) -> Dict:
        """Generate complete system map report."""
        self.scan_components()
        self.analyze_connections()
        self.test_imports()

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_directories": len(self.components),
                "total_files": sum(c.get("files", 0) for c in self.components.values()),
                "total_connections": sum(len(t) for t in self.connections.values()),
                "importable_modules": sum(1 for s in self.import_status.values() if s.get("ok")),
            },
            "components": self.components,
            "connections": {k: list(v) for k, v in self.connections.items()},
            "import_status": self.import_status,
            "navigation_paths": self.get_navigation_paths(),
            "entry_points": self.get_entry_points(),
            "scores": self.calculate_scores(),
        }

    def print_report(self):
        """Print formatted report."""
        report = self.generate_report()

        print("=" * 70)
        print("INTEGRAFIX: SYSTEM MAP & NAVIGABILITY REPORT")
        print(f"Generated: {report['generated_at']}")
        print("=" * 70)

        # Summary
        summary = report["summary"]
        print(f"\nSUMMARY:")
        print(f"  Directories: {summary['total_directories']}")
        print(f"  Python Files: {summary['total_files']}")
        print(f"  Connections: {summary['total_connections']}")
        print(f"  Importable: {summary['importable_modules']}/{len(self.import_status)}")

        # Scores
        scores = report["scores"]
        print(f"\nINTEGRATION SCORES:")
        print(f"  Connectivity:       {scores['connectivity']:.1%}")
        print(f"  Import Success:     {scores['import_success']:.1%}")
        print(f"  INTEGRAFIX Coverage: {scores['integrafix_coverage']:.1%}")
        print(f"  ─────────────────────────")
        print(f"  OVERALL GRADE:      {scores['grade']} ({scores['overall']:.1%})")

        # Navigation Paths
        print(f"\nNAVIGATION PATHS:")
        for name, data in report["navigation_paths"].items():
            print(f"\n  {name}: {data['description']}")
            for i, (module, desc) in enumerate(data["path"]):
                prefix = "└──" if i == len(data["path"])-1 else "├──"
                print(f"    {prefix} {module}")

        # Entry Points
        print(f"\nENTRY POINTS:")
        for ep in report["entry_points"]:
            print(f"  • {ep['name']} ({ep['type']}): {ep['description']}")

        # Connection Map
        print(f"\nCONNECTION MAP:")
        for source, targets in sorted(report["connections"].items()):
            if targets:
                print(f"  {source} → {', '.join(sorted(targets))}")

        print("\n" + "=" * 70)


# Global instance
_map: Optional[SystemMap] = None


def get_system_map() -> SystemMap:
    """Get or create system map."""
    global _map
    if _map is None:
        _map = SystemMap()
    return _map


def main():
    import argparse

    parser = argparse.ArgumentParser(description="INTEGRAFIX System Map")
    parser.add_argument("command", choices=["report", "json", "score"],
                       default="report", nargs="?")
    parser.add_argument("--output", help="Output file path")
    args = parser.parse_args()

    smap = get_system_map()

    if args.command == "report":
        smap.print_report()

    elif args.command == "json":
        report = smap.generate_report()
        output = args.output or "/tmp/integrafix_map.json"
        with open(output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Saved to {output}")

    elif args.command == "score":
        smap.scan_components()
        smap.analyze_connections()
        smap.test_imports()
        scores = smap.calculate_scores()
        print(f"INTEGRAFIX Score: {scores['grade']} ({scores['overall']:.1%})")


if __name__ == "__main__":
    main()
