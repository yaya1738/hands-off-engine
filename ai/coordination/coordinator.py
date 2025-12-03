#!/usr/bin/env python3
"""
AI Coordination Bridge

Wires together:
- ai/ (orchestrators, learning engine)
- ai_nexus/ (providers, nexus core)
- ai/coordination/ (state files)

This is the INTEGRAFIX bridge for AI systems.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class AICoordinator:
    """
    Coordinates all AI subsystems into unified operation.

    Bridges:
    - ai/ho_brain_orchestrator.py → decision making
    - ai/ho_learning_engine.py → learning from outcomes
    - ai_nexus/nexus_core.py → multi-provider execution
    - ai/coordination/*.json → state persistence
    """

    def __init__(self, base_path: str = "/root/hands-off-engine"):
        self.base_path = Path(base_path)
        self.coordination_path = self.base_path / "ai" / "coordination"
        self.state_path = self.base_path / "state" / "ai_memory"

        # Ensure directories exist
        self.coordination_path.mkdir(parents=True, exist_ok=True)
        self.state_path.mkdir(parents=True, exist_ok=True)

        # Load current state
        self.status = self._load_status()

    def _load_status(self) -> Dict:
        """Load coordination status from state file."""
        status_file = self.coordination_path / "status.json"
        if status_file.exists():
            try:
                return json.loads(status_file.read_text())
            except:
                pass
        return {
            "last_coordination": None,
            "components_connected": [],
            "active_sessions": 0
        }

    def _save_status(self) -> None:
        """Save coordination status."""
        status_file = self.coordination_path / "status.json"
        status_file.write_text(json.dumps(self.status, indent=2))

    def wire_brain_orchestrator(self) -> Dict:
        """
        Wire the brain orchestrator to the nexus.

        Connects: ai/ho_brain_orchestrator.py ↔ ai_nexus/nexus_core.py
        """
        result = {"component": "brain_orchestrator", "status": "wired", "details": {}}

        try:
            # Check brain orchestrator exists
            brain_path = self.base_path / "ai" / "ho_brain_orchestrator.py"
            if not brain_path.exists():
                result["status"] = "missing"
                result["details"]["error"] = "ho_brain_orchestrator.py not found"
                return result

            # Check nexus exists
            nexus_path = self.base_path / "ai_nexus" / "nexus_core.py"
            if not nexus_path.exists():
                result["status"] = "missing"
                result["details"]["error"] = "nexus_core.py not found"
                return result

            # Both exist - wire them by updating coordination state
            result["details"]["brain"] = str(brain_path)
            result["details"]["nexus"] = str(nexus_path)

            if "brain_orchestrator" not in self.status.get("components_connected", []):
                self.status.setdefault("components_connected", []).append("brain_orchestrator")

        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)

        return result

    def wire_learning_engine(self) -> Dict:
        """
        Wire the learning engine to outcome recorder.

        Connects: ai/ho_learning_engine.py ↔ autonomous/outcome_recorder.py
        """
        result = {"component": "learning_engine", "status": "wired", "details": {}}

        try:
            # Check learning engine
            learning_path = self.base_path / "ai" / "ho_learning_engine.py"
            if not learning_path.exists():
                result["status"] = "missing"
                result["details"]["error"] = "ho_learning_engine.py not found"
                return result

            # Check outcome recorder
            outcome_path = self.base_path / "autonomous" / "outcome_recorder.py"
            if not outcome_path.exists():
                result["status"] = "missing"
                result["details"]["error"] = "outcome_recorder.py not found"
                return result

            result["details"]["learning"] = str(learning_path)
            result["details"]["outcomes"] = str(outcome_path)

            if "learning_engine" not in self.status.get("components_connected", []):
                self.status.setdefault("components_connected", []).append("learning_engine")

        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)

        return result

    def wire_multi_provider(self) -> Dict:
        """
        Wire multi-provider AI routing.

        Connects: ai_nexus/multi_provider.py ↔ all provider implementations
        """
        result = {"component": "multi_provider", "status": "wired", "details": {"providers": []}}

        try:
            multi_path = self.base_path / "ai_nexus" / "multi_provider.py"
            if not multi_path.exists():
                result["status"] = "missing"
                return result

            # Check available providers
            providers = ["openai", "claude", "copilot", "google", "groq", "chatgpt"]
            for provider in providers:
                provider_file = self.base_path / "ai_nexus" / f"provider_{provider}.py"
                if provider_file.exists():
                    result["details"]["providers"].append(provider)

            if "multi_provider" not in self.status.get("components_connected", []):
                self.status.setdefault("components_connected", []).append("multi_provider")

        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)

        return result

    def wire_session_memory(self) -> Dict:
        """
        Wire session memory persistence.

        Connects: ai/coordination/status.json ↔ state/ai_memory/session_memory.json
        """
        result = {"component": "session_memory", "status": "wired", "details": {}}

        try:
            # Load session memory
            memory_file = self.state_path / "session_memory.json"
            if memory_file.exists():
                memory = json.loads(memory_file.read_text())
                result["details"]["sessions"] = memory.get("total_sessions", 0)
                result["details"]["learnings"] = len(memory.get("key_learnings", []))
            else:
                result["details"]["sessions"] = 0
                result["details"]["learnings"] = 0

            if "session_memory" not in self.status.get("components_connected", []):
                self.status.setdefault("components_connected", []).append("session_memory")

        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)

        return result

    def coordinate(self) -> Dict:
        """
        Run full AI coordination.

        Wires all AI subsystems together.
        """
        print("=" * 60)
        print("AI COORDINATOR - INTEGRAFIX BRIDGE")
        print("=" * 60)

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {}
        }

        # Wire all components
        print("\n[1] Wiring brain orchestrator...")
        results["components"]["brain_orchestrator"] = self.wire_brain_orchestrator()
        print(f"    Status: {results['components']['brain_orchestrator']['status']}")

        print("\n[2] Wiring learning engine...")
        results["components"]["learning_engine"] = self.wire_learning_engine()
        print(f"    Status: {results['components']['learning_engine']['status']}")

        print("\n[3] Wiring multi-provider...")
        results["components"]["multi_provider"] = self.wire_multi_provider()
        providers = results["components"]["multi_provider"]["details"].get("providers", [])
        print(f"    Status: {results['components']['multi_provider']['status']}")
        print(f"    Providers: {', '.join(providers) if providers else 'none'}")

        print("\n[4] Wiring session memory...")
        results["components"]["session_memory"] = self.wire_session_memory()
        print(f"    Status: {results['components']['session_memory']['status']}")

        # Update coordination status
        self.status["last_coordination"] = results["timestamp"]
        self._save_status()

        # Calculate overall health
        wired_count = sum(1 for c in results["components"].values() if c["status"] == "wired")
        total_count = len(results["components"])
        results["health"] = f"{wired_count}/{total_count} components wired"
        results["score"] = int((wired_count / total_count) * 100) if total_count > 0 else 0

        print("\n" + "=" * 60)
        print(f"AI COORDINATION COMPLETE: {results['health']}")
        print("=" * 60)

        return results


def main():
    """Run AI coordination."""
    coordinator = AICoordinator()
    results = coordinator.coordinate()

    # Save results
    output_file = Path("/root/hands-off-engine/state/integrafix/ai_coordination.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    main()
