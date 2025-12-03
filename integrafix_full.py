#!/usr/bin/env python3
"""
INTEGRAFIX FULL SYSTEM
Methodologize the entire hands-off system across all aspects.

ASPECTS:
1. QUALITY      → Standards, testing, validation
2. WORKFLOWS    → Development, deployment, trading, learning
3. ARCHITECTURE → Components, boundaries, data flow
4. COMPONENTS   → Registry, status, health
5. DOCUMENTATION → Generate, validate, update
6. SCOPE        → Boundaries, responsibilities
7. EXECUTION    → Pipeline, scheduling, recovery
8. PROCESSES    → Coordination, monitoring, healing

Serving: Yair Siegel
"""

import json
import os
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

STATE_DIR = PROJECT_ROOT / "state"
INTEGRAFIX_DIR = STATE_DIR / "integrafix"
INTEGRAFIX_DIR.mkdir(parents=True, exist_ok=True)


class IntegrafixFull:
    """
    Full system integration across all aspects.
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.results = {
            "timestamp": self.timestamp,
            "aspects": {},
            "integration_score": 0,
            "recommendations": []
        }

    def _print(self, msg: str, indent: int = 0):
        if self.verbose:
            print("  " * indent + msg)

    def _save_aspect(self, name: str, data: Dict):
        path = INTEGRAFIX_DIR / f"{name}.json"
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    # ==================== ASPECT 1: QUALITY ====================

    def integrafix_quality(self) -> Dict:
        """Map and integrate quality across the system."""
        self._print("\n" + "=" * 70)
        self._print("ASPECT 1: QUALITY")
        self._print("=" * 70)

        quality = {
            "standards": {},
            "testing": {},
            "validation": {},
            "metrics": {}
        }

        # Check for test files
        test_files = list(PROJECT_ROOT.glob("**/test_*.py"))
        tests_dir = PROJECT_ROOT / "tests"
        quality["testing"] = {
            "test_files_found": len(test_files),
            "tests_dir_exists": tests_dir.exists(),
            "locations": [str(f.relative_to(PROJECT_ROOT)) for f in test_files[:10]]
        }
        self._print(f"Test files: {len(test_files)}", 1)

        # Check for type hints (basic check)
        py_files = list(PROJECT_ROOT.glob("**/*.py"))
        py_files = [f for f in py_files if ".git" not in str(f)]
        quality["standards"]["total_py_files"] = len(py_files)
        self._print(f"Python files: {len(py_files)}", 1)

        # Check for docstrings in key files
        key_files = [
            "integrafix.py",
            "autonomous/concrete_executor.py",
            "autonomous/yair_wisdom_engine.py"
        ]
        docstring_count = 0
        for kf in key_files:
            path = PROJECT_ROOT / kf
            if path.exists():
                content = path.read_text()
                if '"""' in content[:500]:
                    docstring_count += 1

        quality["standards"]["key_files_with_docstrings"] = docstring_count
        quality["standards"]["key_files_total"] = len(key_files)
        self._print(f"Key files with docstrings: {docstring_count}/{len(key_files)}", 1)

        # Quality score
        quality["score"] = min(100, (
            (len(test_files) * 2) +
            (docstring_count * 10) +
            (20 if tests_dir.exists() else 0)
        ))
        self._print(f"Quality score: {quality['score']}/100", 1)

        self._save_aspect("quality", quality)
        self.results["aspects"]["quality"] = quality
        return quality

    # ==================== ASPECT 2: WORKFLOWS ====================

    def integrafix_workflows(self) -> Dict:
        """Map and integrate workflows."""
        self._print("\n" + "=" * 70)
        self._print("ASPECT 2: WORKFLOWS")
        self._print("=" * 70)

        workflows = {
            "development": {},
            "deployment": {},
            "trading": {},
            "learning": {},
            "feedback": {}
        }

        # Development workflow
        git_exists = (PROJECT_ROOT / ".git").exists()
        github_workflows = list((PROJECT_ROOT / ".github" / "workflows").glob("*.yml"))
        workflows["development"] = {
            "git_initialized": git_exists,
            "github_workflows": len(github_workflows),
            "workflow_files": [f.name for f in github_workflows]
        }
        self._print(f"Git: {'✓' if git_exists else '✗'}, Workflows: {len(github_workflows)}", 1)

        # Trading workflow
        trading_components = [
            "autonomous/concrete_executor.py",
            "autonomous/yair_wisdom_engine.py",
            "autonomous/probability_calibrator.py",
            "autonomous/outcome_recorder.py",
            "autonomous/glitch_detector.py"
        ]
        trading_exists = sum(1 for c in trading_components if (PROJECT_ROOT / c).exists())
        workflows["trading"] = {
            "components_exist": trading_exists,
            "components_total": len(trading_components),
            "pipeline_wired": (PROJECT_ROOT / "integrafix.py").exists()
        }
        self._print(f"Trading components: {trading_exists}/{len(trading_components)}", 1)

        # Learning workflow
        learning_components = [
            "ai/ho_learning_engine.py",
            "autonomous/outcome_recorder.py",
            "autonomous/skill_growth_tracker.py"
        ]
        learning_exists = sum(1 for c in learning_components if (PROJECT_ROOT / c).exists())
        workflows["learning"] = {
            "components_exist": learning_exists,
            "components_total": len(learning_components)
        }
        self._print(f"Learning components: {learning_exists}/{len(learning_components)}", 1)

        # Workflow score
        workflows["score"] = min(100, (
            (20 if git_exists else 0) +
            (len(github_workflows) * 10) +
            (trading_exists * 10) +
            (learning_exists * 10)
        ))
        self._print(f"Workflow score: {workflows['score']}/100", 1)

        self._save_aspect("workflows", workflows)
        self.results["aspects"]["workflows"] = workflows
        return workflows

    # ==================== ASPECT 3: ARCHITECTURE ====================

    def integrafix_architecture(self) -> Dict:
        """Map and integrate architecture."""
        self._print("\n" + "=" * 70)
        self._print("ASPECT 3: ARCHITECTURE")
        self._print("=" * 70)

        architecture = {
            "layers": {},
            "boundaries": {},
            "data_flow": {},
            "integration_points": []
        }

        # Discover architecture layers
        top_dirs = [d for d in PROJECT_ROOT.iterdir()
                   if d.is_dir() and not d.name.startswith('.')]

        layers = {}
        for d in top_dirs:
            py_count = len(list(d.glob("**/*.py")))
            if py_count > 0:
                layers[d.name] = {
                    "python_files": py_count,
                    "type": self._categorize_layer(d.name)
                }

        architecture["layers"] = layers
        self._print(f"Layers discovered: {len(layers)}", 1)
        for name, info in sorted(layers.items(), key=lambda x: -x[1]["python_files"])[:5]:
            self._print(f"  {name}: {info['python_files']} files ({info['type']})", 1)

        # Integration points
        integration_files = [
            "integrafix.py",
            "autonomous/backend_loop.py",
            "ai/ho_brain_orchestrator.py",
            "ai_nexus/nexus_core.py"
        ]
        for f in integration_files:
            if (PROJECT_ROOT / f).exists():
                architecture["integration_points"].append(f)

        self._print(f"Integration points: {len(architecture['integration_points'])}", 1)

        # Architecture score
        architecture["score"] = min(100, (
            len(layers) * 5 +
            len(architecture["integration_points"]) * 15
        ))
        self._print(f"Architecture score: {architecture['score']}/100", 1)

        self._save_aspect("architecture", architecture)
        self.results["aspects"]["architecture"] = architecture
        return architecture

    def _categorize_layer(self, name: str) -> str:
        categories = {
            "autonomous": "core_automation",
            "ai": "ai_layer",
            "ai_nexus": "ai_coordination",
            "trading": "trading_layer",
            "executor": "execution_layer",
            "alpha": "signal_layer",
            "fetchers": "data_layer",
            "state": "persistence",
            "logs": "observability",
            "config": "configuration",
            "docs": "documentation",
            "tests": "quality",
            "scripts": "tooling"
        }
        return categories.get(name, "other")

    # ==================== ASPECT 4: COMPONENTS ====================

    def integrafix_components(self) -> Dict:
        """Map and integrate all components."""
        self._print("\n" + "=" * 70)
        self._print("ASPECT 4: COMPONENTS")
        self._print("=" * 70)

        components = {
            "registry": {},
            "by_category": defaultdict(list),
            "health": {}
        }

        # Build component registry
        py_files = list(PROJECT_ROOT.glob("**/*.py"))
        py_files = [f for f in py_files if ".git" not in str(f) and "venv" not in str(f)]

        for f in py_files:
            rel_path = str(f.relative_to(PROJECT_ROOT))
            category = rel_path.split("/")[0] if "/" in rel_path else "root"
            components["by_category"][category].append(rel_path)

        # Convert defaultdict to regular dict for JSON
        components["by_category"] = dict(components["by_category"])

        self._print(f"Total components: {len(py_files)}", 1)
        self._print("By category:", 1)
        for cat, files in sorted(components["by_category"].items(), key=lambda x: -len(x[1]))[:7]:
            self._print(f"  {cat}: {len(files)} files", 1)

        # Check component health (are key ones importable?)
        key_components = [
            ("autonomous.concrete_executor", "ConcreteExecutor"),
            ("autonomous.yair_wisdom_engine", "YairWisdomEngine"),
            ("autonomous.outcome_recorder", "OutcomeRecorder"),
        ]

        healthy = 0
        for module, cls in key_components:
            try:
                exec(f"from {module} import {cls}")
                healthy += 1
                components["health"][module] = "healthy"
            except Exception as e:
                components["health"][module] = f"error: {str(e)[:50]}"

        self._print(f"Key components healthy: {healthy}/{len(key_components)}", 1)

        components["registry"]["total"] = len(py_files)
        components["registry"]["categories"] = len(components["by_category"])

        # Component score
        components["score"] = min(100, (
            (healthy / len(key_components) * 50) +
            (len(components["by_category"]) * 3)
        ))
        self._print(f"Component score: {components['score']:.0f}/100", 1)

        self._save_aspect("components", components)
        self.results["aspects"]["components"] = components
        return components

    # ==================== ASPECT 5: DOCUMENTATION ====================

    def integrafix_documentation(self) -> Dict:
        """Map and integrate documentation."""
        self._print("\n" + "=" * 70)
        self._print("ASPECT 5: DOCUMENTATION")
        self._print("=" * 70)

        documentation = {
            "files": {},
            "coverage": {},
            "types": {}
        }

        # Find all markdown files
        md_files = list(PROJECT_ROOT.glob("**/*.md"))
        md_files = [f for f in md_files if ".git" not in str(f)]

        documentation["files"]["markdown"] = len(md_files)
        self._print(f"Markdown files: {len(md_files)}", 1)

        # Categorize docs
        doc_types = defaultdict(list)
        for f in md_files:
            name = f.name.upper()
            if "README" in name:
                doc_types["readme"].append(str(f.relative_to(PROJECT_ROOT)))
            elif "STATUS" in name or "REPORT" in name:
                doc_types["status"].append(str(f.relative_to(PROJECT_ROOT)))
            elif "KNOWLEDGE" in name:
                doc_types["knowledge"].append(str(f.relative_to(PROJECT_ROOT)))
            elif "BATCH" in name:
                doc_types["batch_logs"].append(str(f.relative_to(PROJECT_ROOT)))
            else:
                doc_types["other"].append(str(f.relative_to(PROJECT_ROOT)))

        documentation["types"] = dict(doc_types)
        self._print("Doc types:", 1)
        for dtype, files in doc_types.items():
            self._print(f"  {dtype}: {len(files)}", 1)

        # Check for key docs
        key_docs = ["README.md", "KNOWLEDGE.md", "docs/"]
        docs_exist = sum(1 for d in key_docs if (PROJECT_ROOT / d).exists())
        documentation["coverage"]["key_docs"] = docs_exist

        # Documentation score
        documentation["score"] = min(100, (
            len(md_files) * 2 +
            docs_exist * 10 +
            len(doc_types.get("knowledge", [])) * 5
        ))
        self._print(f"Documentation score: {documentation['score']}/100", 1)

        self._save_aspect("documentation", documentation)
        self.results["aspects"]["documentation"] = documentation
        return documentation

    # ==================== ASPECT 6: SCOPE ====================

    def integrafix_scope(self) -> Dict:
        """Map and integrate scope definitions."""
        self._print("\n" + "=" * 70)
        self._print("ASPECT 6: SCOPE")
        self._print("=" * 70)

        scope = {
            "features": {},
            "boundaries": {},
            "responsibilities": {},
            "bridges": {}
        }

        # Run AI coordinator bridge to check status
        ai_coordination_status = "partial"
        monitoring_status = "partial"

        try:
            ai_coord_file = INTEGRAFIX_DIR / "ai_coordination.json"
            if ai_coord_file.exists():
                ai_data = json.loads(ai_coord_file.read_text())
                if ai_data.get("score", 0) >= 75:
                    ai_coordination_status = "wired"
                    scope["bridges"]["ai_coordination"] = ai_data
        except:
            pass

        try:
            monitoring_file = INTEGRAFIX_DIR / "monitoring.json"
            if monitoring_file.exists():
                mon_data = json.loads(monitoring_file.read_text())
                if mon_data.get("score", 0) >= 75:
                    monitoring_status = "wired"
                    scope["bridges"]["monitoring"] = mon_data
        except:
            pass

        # Define feature scope with bridge status
        features = {
            "trading": {
                "description": "Polymarket prediction market trading",
                "components": ["autonomous/", "trading/", "executor/"],
                "status": "active"
            },
            "ai_coordination": {
                "description": "Multi-AI provider coordination",
                "components": ["ai/", "ai_nexus/"],
                "status": ai_coordination_status,
                "bridge": "ai/coordination/coordinator.py"
            },
            "automation": {
                "description": "Autonomous operation and healing",
                "components": ["autonomous/", "scheduler/"],
                "status": "active"
            },
            "monitoring": {
                "description": "System health and observability",
                "components": ["health/", "logs/", "audit/"],
                "status": monitoring_status,
                "bridge": "health/monitoring_bridge.py"
            },
            "learning": {
                "description": "Outcome-based learning loop",
                "components": ["ai/ho_learning_engine.py", "autonomous/outcome_recorder.py"],
                "status": "wired"
            }
        }

        scope["features"] = features
        self._print(f"Features defined: {len(features)}", 1)
        for name, info in features.items():
            self._print(f"  {name}: {info['status']}", 1)

        # System boundaries
        scope["boundaries"] = {
            "internal": ["autonomous/", "ai/", "executor/"],
            "external": ["Polymarket API", "GitHub", "ESPN"],
            "storage": ["state/", "logs/", "backups/"]
        }

        # Scope score - now counts wired bridges
        active_features = sum(1 for f in features.values() if f["status"] in ["active", "wired"])
        scope["score"] = min(100, active_features * 20)
        self._print(f"Scope score: {scope['score']}/100", 1)

        self._save_aspect("scope", scope)
        self.results["aspects"]["scope"] = scope
        return scope

    # ==================== ASPECT 7: EXECUTION ====================

    def integrafix_execution(self) -> Dict:
        """Map and integrate execution paths."""
        self._print("\n" + "=" * 70)
        self._print("ASPECT 7: EXECUTION")
        self._print("=" * 70)

        execution = {
            "pipelines": {},
            "entry_points": [],
            "cron_jobs": {},
            "processes": {}
        }

        # Find entry points (files with if __name__ == "__main__")
        py_files = list(PROJECT_ROOT.glob("**/*.py"))
        py_files = [f for f in py_files if ".git" not in str(f)]

        entry_points = []
        for f in py_files:
            try:
                content = f.read_text()
                if 'if __name__ == "__main__"' in content or "if __name__ == '__main__'" in content:
                    entry_points.append(str(f.relative_to(PROJECT_ROOT)))
            except:
                pass

        execution["entry_points"] = entry_points[:20]  # Top 20
        self._print(f"Entry points: {len(entry_points)}", 1)

        # Get cron jobs
        try:
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            cron_lines = [l for l in result.stdout.split("\n") if l.strip() and not l.startswith("#")]
            execution["cron_jobs"]["count"] = len(cron_lines)
            execution["cron_jobs"]["jobs"] = cron_lines[:10]
            self._print(f"Cron jobs: {len(cron_lines)}", 1)
        except:
            execution["cron_jobs"]["count"] = 0

        # Check running processes
        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            python_procs = [l for l in result.stdout.split("\n") if "python" in l.lower() and "hands-off" in l.lower()]
            execution["processes"]["running"] = len(python_procs)
            self._print(f"Running processes: {len(python_procs)}", 1)
        except:
            execution["processes"]["running"] = 0

        # Execution score
        execution["score"] = min(100, (
            len(entry_points) * 2 +
            execution["cron_jobs"].get("count", 0) * 3 +
            execution["processes"].get("running", 0) * 10
        ))
        self._print(f"Execution score: {execution['score']}/100", 1)

        self._save_aspect("execution", execution)
        self.results["aspects"]["execution"] = execution
        return execution

    # ==================== ASPECT 8: PROCESSES ====================

    def integrafix_processes(self) -> Dict:
        """Map and integrate all processes."""
        self._print("\n" + "=" * 70)
        self._print("ASPECT 8: PROCESSES")
        self._print("=" * 70)

        processes = {
            "background": [],
            "scheduled": [],
            "coordination": {},
            "health": {},
            "bridge": {}
        }

        # Check background processes
        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            for line in result.stdout.split("\n"):
                if "python" in line.lower() and any(x in line for x in ["backend_loop", "hardware_brain", "scaling_engine", "self_healer"]):
                    # Extract script name
                    parts = line.split()
                    script = [p for p in parts if ".py" in p]
                    if script:
                        processes["background"].append(script[0].split("/")[-1])
        except:
            pass

        self._print(f"Background processes: {len(processes['background'])}", 1)
        for p in processes["background"]:
            self._print(f"  ✓ {p}", 1)

        # Coordination status
        coord_files = [
            "ai/coordination/status.json",
            "ai/coordination/handoffs.json",
            "state/integrafix_state.json"
        ]
        for cf in coord_files:
            path = PROJECT_ROOT / cf
            if path.exists():
                try:
                    with open(path) as f:
                        data = json.load(f)
                    processes["coordination"][cf] = "exists"
                except:
                    processes["coordination"][cf] = "invalid"
            else:
                processes["coordination"][cf] = "missing"

        self._print(f"Coordination files: {sum(1 for v in processes['coordination'].values() if v == 'exists')}/{len(coord_files)}", 1)

        # Load process bridge data if available
        try:
            bridge_file = INTEGRAFIX_DIR / "processes_bridge.json"
            if bridge_file.exists():
                bridge_data = json.loads(bridge_file.read_text())
                processes["bridge"] = bridge_data
                processes["scheduled"] = bridge_data.get("components", {}).get("execution_state", {}).get("details", {}).get("processes", [])
                self._print(f"Process bridge: wired ({len(processes['scheduled'])} scheduled)", 1)
        except:
            pass

        # Process score - include bridge
        bridge_score = 0
        if processes.get("bridge", {}).get("score", 0) >= 50:
            bridge_score = 20

        processes["score"] = min(100, (
            len(processes["background"]) * 15 +
            sum(1 for v in processes["coordination"].values() if v == "exists") * 10 +
            bridge_score
        ))
        self._print(f"Process score: {processes['score']}/100", 1)

        self._save_aspect("processes", processes)
        self.results["aspects"]["processes"] = processes
        return processes

    # ==================== FULL INTEGRATION ====================

    def run_full_integrafix(self) -> Dict:
        """Run complete system integrafix."""
        self._print("=" * 70)
        self._print("INTEGRAFIX FULL SYSTEM ANALYSIS")
        self._print(f"Time: {self.timestamp}")
        self._print("=" * 70)

        # Run all aspects
        self.integrafix_quality()
        self.integrafix_workflows()
        self.integrafix_architecture()
        self.integrafix_components()
        self.integrafix_documentation()
        self.integrafix_scope()
        self.integrafix_execution()
        self.integrafix_processes()

        # Calculate overall integration score
        scores = [a.get("score", 0) for a in self.results["aspects"].values()]
        self.results["integration_score"] = sum(scores) / len(scores) if scores else 0

        # Generate recommendations
        self._generate_recommendations()

        # Summary
        self._print("\n" + "=" * 70)
        self._print("INTEGRAFIX SUMMARY")
        self._print("=" * 70)

        self._print("\nAspect Scores:")
        for aspect, data in self.results["aspects"].items():
            score = data.get("score", 0)
            bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))
            self._print(f"  {aspect:15} [{bar}] {score:.0f}/100")

        self._print(f"\nOVERALL INTEGRATION: {self.results['integration_score']:.0f}/100")

        if self.results["recommendations"]:
            self._print("\nTop Recommendations:")
            for rec in self.results["recommendations"][:5]:
                self._print(f"  → {rec}")

        # Save full results
        self._save_aspect("full_integrafix", self.results)

        return self.results

    def _generate_recommendations(self):
        """Generate integration recommendations based on scores."""
        recs = []

        aspects = self.results["aspects"]

        if aspects.get("quality", {}).get("score", 0) < 50:
            recs.append("Add more tests to improve quality coverage")

        if aspects.get("workflows", {}).get("score", 0) < 50:
            recs.append("Wire up GitHub Actions for CI/CD")

        if aspects.get("execution", {}).get("processes", {}).get("running", 0) < 3:
            recs.append("Start key background processes (concrete_executor, outcome_recorder)")

        if aspects.get("processes", {}).get("score", 0) < 50:
            recs.append("Add process coordination layer")

        if aspects.get("documentation", {}).get("score", 0) < 50:
            recs.append("Generate API documentation from docstrings")

        # Always recommend
        recs.append("Run 'python3 integrafix.py --live' when ready for live trading")

        self.results["recommendations"] = recs


def main():
    import argparse
    parser = argparse.ArgumentParser(description="INTEGRAFIX Full System")
    parser.add_argument("--quiet", action="store_true", help="Reduce output")
    args = parser.parse_args()

    integrafix = IntegrafixFull(verbose=not args.quiet)
    return integrafix.run_full_integrafix()


if __name__ == "__main__":
    main()
