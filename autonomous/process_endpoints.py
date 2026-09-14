#!/usr/bin/env python3
"""
🔄 PROCESS ENDPOINTS - Maps Evolution Decisions to Running Processes
Serving: Yair Siegel

Complete cycle: Decision → Endpoint → Execute → Feedback → Next Decision

Each capability maps to:
- A running process or HTTP endpoint
- A feedback mechanism
- A health check
"""

import json
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Callable
from dataclasses import dataclass

BASE_DIR = Path("/root/hands-off-engine")
STATE_DIR = BASE_DIR / "state"

# Endpoint registry state
ENDPOINT_STATE = STATE_DIR / "endpoint_registry.json"
CYCLE_LOG = STATE_DIR / "process_cycles.jsonl"


@dataclass
class Endpoint:
    """Represents a process endpoint."""
    name: str
    endpoint_type: str  # "script", "http", "actuator", "process"
    target: str  # script path, URL, or actuator name
    args: list = None
    health_check: str = None  # Optional health check command
    feedback_file: str = None  # Where this endpoint writes feedback


# Complete endpoint registry - maps capabilities to actual processes
ENDPOINT_REGISTRY: Dict[str, Endpoint] = {
    # Core income generation
    "outreach": Endpoint(
        name="Active Outreach",
        endpoint_type="script",
        target="autonomous/active_pursuit.py",
        args=["pursue"],
        feedback_file="state/active_pursuit.json",
    ),
    "conversion": Endpoint(
        name="Conversion Optimizer",
        endpoint_type="script",
        target="autonomous/conversion_optimizer.py",
        args=["experiment"],
        feedback_file="state/conversion_optimizer.json",
    ),

    # Reality and monitoring
    "reality_check": Endpoint(
        name="Reality Feedback",
        endpoint_type="script",
        target="autonomous/reality_feedback.py",
        args=["check"],
        feedback_file="state/reality_feedback.json",
    ),
    "helicopter": Endpoint(
        name="Helicopter View",
        endpoint_type="script",
        target="autonomous/helicopter.py",
        args=["broadcast"],
        feedback_file="state/helicopter_state.json",
    ),

    # System maintenance
    "self_heal": Endpoint(
        name="Self Healing Agent",
        endpoint_type="script",
        target="scripts/self_healing_agent.py",
        args=[],
        feedback_file="state/self_healing_state.json",
    ),
    "cost_audit": Endpoint(
        name="Cost Gate",
        endpoint_type="script",
        target="finance/cost_gate.py",
        args=["audit"],
        feedback_file="state/cost_gate_state.json",
    ),

    # War room / preparation
    "war_room": Endpoint(
        name="War Room",
        endpoint_type="script",
        target="autonomous/corporate_meeting.py",
        args=["observe"],
        feedback_file="state/war_room.jsonl",
    ),

    # Trading
    "trading_check": Endpoint(
        name="Trading Status",
        endpoint_type="actuator",
        target="polymarket_status",
        feedback_file="state/trading_status.json",
    ),
    "trading_execute": Endpoint(
        name="Execute Trade",
        endpoint_type="actuator",
        target="polymarket_trade",
        feedback_file="state/trading_executions.jsonl",
    ),

    # Notifications
    "notify": Endpoint(
        name="Telegram Notify",
        endpoint_type="actuator",
        target="telegram",
        feedback_file="state/notifications.jsonl",
    ),

    # Living system processes
    "stage_conversation": Endpoint(
        name="Self Conversation",
        endpoint_type="script",
        target="autonomous/self_conversation.py",
        args=["turn"],
        feedback_file="state/self_conversation.jsonl",
    ),
    "gallery": Endpoint(
        name="Peanut Gallery",
        endpoint_type="script",
        target="autonomous/peanut_gallery.py",
        args=["observe"],
        feedback_file="state/peanut_gallery.jsonl",
    ),

    # Coordination
    "coordinate": Endpoint(
        name="Coordination Agent",
        endpoint_type="script",
        target="scripts/coordination_agent.py",
        args=["cycle"],
        feedback_file="state/coordination_state.json",
    ),

    # Doctor
    "doctor_examine": Endpoint(
        name="System Doctor Examination",
        endpoint_type="script",
        target="autonomous/system_doctor.py",
        args=["examine"],
        feedback_file="state/doctor_state.json",
    ),
    "doctor_report": Endpoint(
        name="System Doctor Report",
        endpoint_type="script",
        target="autonomous/system_doctor.py",
        args=["report"],
        feedback_file="state/diagnosis_log.jsonl",
    ),
    "doctor_meeting": Endpoint(
        name="Doctor Consultation Meeting",
        endpoint_type="script",
        target="autonomous/doctor_meeting.py",
        args=["meeting"],
        feedback_file="state/meeting_actions.json",
    ),
    "sage_session": Endpoint(
        name="Sage Wisdom Session",
        endpoint_type="script",
        target="autonomous/system_sage.py",
        args=["session"],
        feedback_file="state/sage_state.json",
    ),
    "sage_morning": Endpoint(
        name="Sage Morning Guidance",
        endpoint_type="script",
        target="autonomous/system_sage.py",
        args=["morning"],
        feedback_file="state/daily_guidance.json",
    ),
    "battery_status": Endpoint(
        name="Battery Status",
        endpoint_type="script",
        target="autonomous/system_battery.py",
        args=["status"],
        feedback_file="state/system_battery.json",
    ),
    "battery_check": Endpoint(
        name="Battery Quick Check",
        endpoint_type="script",
        target="autonomous/system_battery.py",
        args=["check"],
        feedback_file="state/system_battery.json",
    ),
}


class ProcessCycler:
    """
    Manages process cycling - ensures each decision flows through
    complete cycle: execute → feedback → next decision
    """

    def __init__(self):
        self.state = self._load_state()
        self.actuators = None
        self._init_actuators()

    def _init_actuators(self):
        try:
            from autonomous.actuators import ActuatorHub
            self.actuators = ActuatorHub()
        except ImportError:
            pass

    def _load_state(self) -> Dict:
        if ENDPOINT_STATE.exists():
            return json.loads(ENDPOINT_STATE.read_text())
        return {
            "cycles": 0,
            "endpoints": {},
            "last_cycle": None,
        }

    def _save_state(self):
        ENDPOINT_STATE.write_text(json.dumps(self.state, indent=2))

    def _log_cycle(self, endpoint: str, success: bool, result: str, duration: float):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "endpoint": endpoint,
            "success": success,
            "result": result[:200],
            "duration_ms": int(duration * 1000),
        }
        with open(CYCLE_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def execute_endpoint(self, endpoint_name: str, context: Dict = None) -> Dict:
        """
        Execute an endpoint and return structured result.
        This is the core of process cycling.
        """
        if endpoint_name not in ENDPOINT_REGISTRY:
            return {"success": False, "error": f"Unknown endpoint: {endpoint_name}"}

        endpoint = ENDPOINT_REGISTRY[endpoint_name]
        start_time = datetime.now(timezone.utc)

        try:
            if endpoint.endpoint_type == "script":
                result = self._execute_script(endpoint, context)
            elif endpoint.endpoint_type == "actuator":
                result = self._execute_actuator(endpoint, context)
            elif endpoint.endpoint_type == "http":
                result = self._execute_http(endpoint, context)
            else:
                result = {"success": False, "error": f"Unknown endpoint type: {endpoint.endpoint_type}"}

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            # Update state
            self.state["cycles"] += 1
            self.state["last_cycle"] = {
                "endpoint": endpoint_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "success": result.get("success", False),
            }
            if endpoint_name not in self.state["endpoints"]:
                self.state["endpoints"][endpoint_name] = {"executions": 0, "successes": 0}
            self.state["endpoints"][endpoint_name]["executions"] += 1
            if result.get("success"):
                self.state["endpoints"][endpoint_name]["successes"] += 1
            self._save_state()

            # Log cycle
            self._log_cycle(endpoint_name, result.get("success", False),
                          result.get("output", "")[:200], duration)

            # Read feedback if available
            if endpoint.feedback_file:
                feedback_path = BASE_DIR / endpoint.feedback_file
                if feedback_path.exists():
                    result["feedback"] = self._read_feedback(feedback_path)

            return result

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self._log_cycle(endpoint_name, False, str(e), duration)
            return {"success": False, "error": str(e)}

    def _execute_script(self, endpoint: Endpoint, context: Dict = None) -> Dict:
        """Execute a Python script endpoint."""
        script_path = BASE_DIR / endpoint.target
        if not script_path.exists():
            return {"success": False, "error": f"Script not found: {endpoint.target}"}

        cmd = ["python3", str(script_path)] + (endpoint.args or [])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(BASE_DIR),
                env={"PYTHONPATH": str(BASE_DIR), **dict(__import__('os').environ)}
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout[-500:] if result.stdout else "",
                "error": result.stderr[-200:] if result.returncode != 0 else None,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Script timed out (120s)"}

    def _execute_actuator(self, endpoint: Endpoint, context: Dict = None) -> Dict:
        """Execute an actuator-based endpoint."""
        if not self.actuators:
            return {"success": False, "error": "Actuators not available"}

        actuator_name = endpoint.target

        if actuator_name == "telegram":
            message = context.get("message", "System notification") if context else "System notification"
            success = self.actuators.notify(message)
            return {"success": success, "output": "Message sent" if success else "Send failed"}

        elif actuator_name == "polymarket_status":
            status = self.actuators.status()
            pm_status = status.get("polymarket", {})
            return {
                "success": pm_status.get("healthy", False),
                "output": json.dumps(pm_status),
                "data": pm_status,
            }

        elif actuator_name == "polymarket_trade":
            if not context or "token_id" not in context:
                return {"success": False, "error": "Missing trade parameters"}
            result = self.actuators.trade(
                context["token_id"],
                context.get("amount", 1.0),
                context.get("side", "BUY")
            )
            return {
                "success": "error" not in result,
                "output": json.dumps(result),
                "data": result,
            }

        return {"success": False, "error": f"Unknown actuator: {actuator_name}"}

    def _execute_http(self, endpoint: Endpoint, context: Dict = None) -> Dict:
        """Execute an HTTP endpoint."""
        try:
            req = urllib.request.Request(endpoint.target)
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read().decode()
                return {"success": True, "output": data[:500]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _read_feedback(self, path: Path) -> Dict:
        """Read feedback from endpoint's feedback file."""
        try:
            if path.suffix == ".jsonl":
                lines = path.read_text().strip().split("\n")
                if lines and lines[-1]:
                    return json.loads(lines[-1])
            else:
                return json.loads(path.read_text())
        except:
            return {}

    def get_endpoint_status(self) -> Dict:
        """Get status of all registered endpoints."""
        status = {}
        for name, endpoint in ENDPOINT_REGISTRY.items():
            ep_state = self.state.get("endpoints", {}).get(name, {})
            status[name] = {
                "name": endpoint.name,
                "type": endpoint.endpoint_type,
                "executions": ep_state.get("executions", 0),
                "successes": ep_state.get("successes", 0),
                "success_rate": (ep_state.get("successes", 0) / ep_state.get("executions", 1))
                               if ep_state.get("executions", 0) > 0 else 0,
            }
        return status

    def cycle_all_monitoring(self) -> Dict:
        """Run one cycle of all monitoring endpoints."""
        results = {}
        monitoring = ["reality_check", "helicopter", "trading_check"]

        for endpoint_name in monitoring:
            results[endpoint_name] = self.execute_endpoint(endpoint_name)

        return results

    def cycle_income_generation(self) -> Dict:
        """Run one cycle of income-generating endpoints."""
        results = {}
        income = ["outreach", "conversion"]

        for endpoint_name in income:
            results[endpoint_name] = self.execute_endpoint(endpoint_name)

        return results


def integrate_with_evolution():
    """Update evolution engine to use process endpoints."""
    from autonomous.evolution_engine import CAPABILITIES

    # Map capabilities to endpoints
    capability_to_endpoint = {
        "outreach": "outreach",
        "conversion": "conversion",
        "reality_check": "reality_check",
        "self_heal": "self_heal",
        "cost_audit": "cost_audit",
        "notify": "notify",
        "check_trading": "trading_check",
    }

    return capability_to_endpoint


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Process Endpoint Cycling")
    parser.add_argument("command", choices=["status", "execute", "cycle-monitor", "cycle-income"])
    parser.add_argument("--endpoint", help="Endpoint to execute")
    parser.add_argument("--message", help="Message for notify endpoint")

    args = parser.parse_args()

    cycler = ProcessCycler()

    if args.command == "status":
        print("\n🔄 PROCESS ENDPOINTS STATUS")
        print("=" * 60)
        status = cycler.get_endpoint_status()
        for name, info in status.items():
            rate = info['success_rate'] * 100
            print(f"  {name:20} | {info['type']:8} | {info['executions']:3} runs | {rate:.0f}% success")
        print(f"\nTotal cycles: {cycler.state.get('cycles', 0)}")

    elif args.command == "execute":
        if not args.endpoint:
            print("Error: --endpoint required")
            return
        context = {"message": args.message} if args.message else None
        result = cycler.execute_endpoint(args.endpoint, context)
        print(f"\n{'✅' if result['success'] else '❌'} {args.endpoint}")
        print(f"Output: {result.get('output', result.get('error', 'No output'))[:200]}")

    elif args.command == "cycle-monitor":
        print("\n🔄 Running monitoring cycle...")
        results = cycler.cycle_all_monitoring()
        for name, result in results.items():
            print(f"  {'✅' if result['success'] else '❌'} {name}")

    elif args.command == "cycle-income":
        print("\n💰 Running income generation cycle...")
        results = cycler.cycle_income_generation()
        for name, result in results.items():
            print(f"  {'✅' if result['success'] else '❌'} {name}")


if __name__ == "__main__":
    main()
