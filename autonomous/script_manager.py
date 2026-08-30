#!/usr/bin/env python3
"""Legacy script registry compatibility surface.

Execution and cron mutation are intentionally fail-closed. Runtime execution
must enter through FactoryAuthorityGateway; this module remains useful for
inventory, status, and compatibility reads without being an execution
authority.
"""

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
AUTONOMOUS_DIR = BASE_DIR / "autonomous"
STATE_DIR = BASE_DIR / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

MASTER = "Yair Siegel"
REGISTRY_FILE = STATE_DIR / "script_registry.json"
EXECUTION_LOG = STATE_DIR / "script_executions.jsonl"


@dataclass
class Script:
    path: str
    name: str
    type: str
    purpose: str
    category: str
    dependencies: List[str] = field(default_factory=list)
    schedule: str = ""
    enabled: bool = True
    last_run: str = ""
    last_status: str = ""
    run_count: int = 0
    fail_count: int = 0
    hash: str = ""
    created: str = ""
    modified: str = ""


class ScriptManager:
    """Inventory/status manager; not an execution authority."""

    def __init__(self):
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict:
        if REGISTRY_FILE.exists():
            try:
                return json.loads(REGISTRY_FILE.read_text())
            except Exception:
                pass
        return {"master": MASTER, "scripts": {}, "cron_jobs": [], "last_scan": None}

    def _save_registry(self):
        self.registry["last_updated"] = datetime.now(timezone.utc).isoformat()
        REGISTRY_FILE.write_text(json.dumps(self.registry, indent=2))

    def _get_file_hash(self, path: str) -> str:
        try:
            return hashlib.md5(Path(path).read_bytes()).hexdigest()[:12]
        except Exception:
            return ""

    def _infer_purpose(self, path: str, name: str) -> Tuple[str, str]:
        lower = name.lower()
        if any(x in lower for x in ["trade", "position", "market", "signal"]):
            category = "trading"
        elif any(x in lower for x in ["monitor", "health", "check", "watch"]):
            category = "monitoring"
        elif any(x in lower for x in ["scale", "provision", "bootstrap", "deploy"]):
            category = "infrastructure"
        elif any(x in lower for x in ["coordinate", "orchestrat", "agent"]):
            category = "coordination"
        elif any(x in lower for x in ["cost", "balance", "payment", "capital", "finance"]):
            category = "finance"
        elif any(x in lower for x in ["digest", "summary", "report", "notify"]):
            category = "reporting"
        else:
            category = "utility"
        purpose_map = {
            "position_monitor": "Monitor open trading positions",
            "capital_recovery": "Track capital recovery from positions",
            "payment_monitor": "Watch for incoming payments",
            "daily_digest": "Generate daily status summary",
            "healthcheck": "Check system health",
            "run_pipeline": "Execute main trading pipeline",
            "self_healing": "Automatically fix system issues",
            "coordination": "Coordinate between system components",
            "fetch_fresh_markets": "Get latest market data",
            "snapshot_system_state": "Capture system state",
        }
        purpose = next((v for k, v in purpose_map.items() if k in lower), "Unknown purpose")
        return purpose, category

    def discover_scripts(self) -> List[Script]:
        scripts: List[Script] = []
        for search_dir in [SCRIPTS_DIR, AUTONOMOUS_DIR, BASE_DIR / "trading", BASE_DIR / "finance"]:
            if not search_dir.exists():
                continue
            for pattern in ("*.py", "*.sh"):
                for path in search_dir.glob(pattern):
                    if path.name.startswith("__"):
                        continue
                    name = path.stem
                    script_type = "python" if path.suffix == ".py" else "bash"
                    purpose, category = self._infer_purpose(str(path), name)
                    existing = self.registry.get("scripts", {}).get(name, {})
                    script = Script(
                        path=str(path), name=name, type=script_type,
                        purpose=existing.get("purpose", purpose),
                        category=existing.get("category", category),
                        dependencies=existing.get("dependencies", []),
                        schedule=existing.get("schedule", "manual"),
                        enabled=existing.get("enabled", True),
                        last_run=existing.get("last_run", ""),
                        last_status=existing.get("last_status", "unknown"),
                        run_count=existing.get("run_count", 0),
                        fail_count=existing.get("fail_count", 0),
                        hash=self._get_file_hash(str(path)),
                        created=existing.get("created", datetime.now(timezone.utc).isoformat()),
                        modified=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                    )
                    scripts.append(script)
                    self.registry["scripts"][name] = asdict(script)
        self.registry["last_scan"] = datetime.now(timezone.utc).isoformat()
        self._save_registry()
        return scripts

    def get_cron_jobs(self) -> List[Dict]:
        """Read cron state without modifying the system."""
        try:
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return []
            jobs = []
            for line in result.stdout.splitlines():
                line = line.strip()
                parts = line.split()
                if not parts or line.startswith("#") or "=" in parts[0] or len(parts) < 6:
                    continue
                command = " ".join(parts[5:])
                script_name = next((Path(p).stem for p in command.split() if p.endswith((".py", ".sh"))), "")
                jobs.append({"schedule": " ".join(parts[:5]), "command": command, "script": script_name, "enabled": True})
            self.registry["cron_jobs"] = jobs
            self._save_registry()
            return jobs
        except Exception:
            return []

    def run_script(self, name: str, args: List[str] = None, timeout: int = 300) -> Tuple[bool, str]:
        """Fail closed; direct script execution is no longer permitted here."""
        return False, (
            f"ScriptManager direct execution is disabled for '{name}'. "
            "Route execution through FactoryAuthorityGateway."
        )

    def enable_script(self, name: str) -> bool:
        if name in self.registry.get("scripts", {}):
            self.registry["scripts"][name]["enabled"] = True
            self._save_registry()
            return True
        return False

    def disable_script(self, name: str) -> Tuple[bool, str]:
        if name in self.registry.get("scripts", {}):
            self.registry["scripts"][name]["enabled"] = False
            self._save_registry()
            return True, f"Disabled: {name}"
        return False, f"Script not found: {name}"

    def set_schedule(self, name: str, schedule: str) -> bool:
        if name in self.registry.get("scripts", {}):
            self.registry["scripts"][name]["schedule"] = schedule
            self._save_registry()
            return True
        return False

    def add_cron_job(self, script_name: str, schedule: str) -> Tuple[bool, str]:
        return False, "Direct cron mutation is disabled; use the approved runtime/deployment authority."

    def remove_cron_job(self, script_name: str) -> Tuple[bool, str]:
        return False, "Direct cron mutation is disabled; use the approved runtime/deployment authority."

    def get_status(self) -> Dict:
        scripts = self.registry.get("scripts", {})
        cron_jobs = self.get_cron_jobs()
        by_category: Dict[str, int] = {}
        for script in scripts.values():
            category = script.get("category", "unknown")
            by_category[category] = by_category.get(category, 0) + 1
        enabled = sum(1 for script in scripts.values() if script.get("enabled", True))
        return {
            "master": MASTER,
            "total_scripts": len(scripts),
            "enabled": enabled,
            "disabled": len(scripts) - enabled,
            "scheduled": sum(1 for s in scripts.values() if s.get("schedule") not in ["", "manual"]),
            "cron_jobs": len(cron_jobs),
            "last_failures": sum(1 for s in scripts.values() if s.get("last_status") == "failed"),
            "by_category": by_category,
            "last_scan": self.registry.get("last_scan"),
        }

    def get_script(self, name: str) -> Optional[Dict]:
        return self.registry.get("scripts", {}).get(name)

    def list_scripts(self, category: str = None, enabled_only: bool = False) -> List[Dict]:
        scripts = list(self.registry.get("scripts", {}).values())
        if category:
            scripts = [s for s in scripts if s.get("category") == category]
        if enabled_only:
            scripts = [s for s in scripts if s.get("enabled", True)]
        return sorted(scripts, key=lambda x: x.get("name", ""))


_manager: Optional[ScriptManager] = None


def get_script_manager() -> ScriptManager:
    global _manager
    if _manager is None:
        _manager = ScriptManager()
    return _manager


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Script Manager - inventory/status compatibility surface")
    parser.add_argument("command", choices=["discover", "list", "status", "run", "enable", "disable", "cron-list", "cron-add", "cron-remove", "show"])
    parser.add_argument("--name")
    parser.add_argument("--category")
    parser.add_argument("--schedule")
    parser.add_argument("--args", nargs="*")
    args = parser.parse_args()
    manager = get_script_manager()
    if args.command == "discover":
        for script in manager.discover_scripts():
            print(f"[{script.category}] {script.name} ({script.type})")
    elif args.command == "list":
        for script in manager.list_scripts(category=args.category):
            print(script["name"])
    elif args.command == "status":
        print(json.dumps(manager.get_status(), indent=2))
    elif args.command == "run":
        if not args.name:
            print("Error: --name required")
            return
        success, output = manager.run_script(args.name, args.args)
        print(output)
        if not success:
            raise SystemExit(1)
    elif args.command == "enable":
        print("Enabled" if manager.enable_script(args.name) else "Script not found")
    elif args.command == "disable":
        print(manager.disable_script(args.name)[1])
    elif args.command == "cron-list":
        print(json.dumps(manager.get_cron_jobs(), indent=2))
    elif args.command == "cron-add":
        print(manager.add_cron_job(args.name, args.schedule)[1])
    elif args.command == "cron-remove":
        print(manager.remove_cron_job(args.name)[1])
    elif args.command == "show":
        script = manager.get_script(args.name)
        print(json.dumps(script, indent=2) if script else f"Script not found: {args.name}")


if __name__ == "__main__":
    main()
