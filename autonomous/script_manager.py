#!/usr/bin/env python3
"""
SCRIPT MANAGER - System Manages Its Own Scripts
================================================

The system must be aware of, understand, and control all its scripts.
This is self-management - the system manages its own executable components.

CAPABILITIES:
1. Discovery - Find all scripts in the system
2. Understanding - Know what each script does
3. Scheduling - Manage cron jobs
4. Health - Monitor script execution
5. Creation - Create new scripts when needed
6. Modification - Update scripts autonomously

Serving: Yair Siegel
"""

import os
import json
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field

BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = BASE_DIR / 'scripts'
AUTONOMOUS_DIR = BASE_DIR / 'autonomous'
STATE_DIR = BASE_DIR / 'state'
STATE_DIR.mkdir(parents=True, exist_ok=True)

MASTER = "Yair Siegel"
REGISTRY_FILE = STATE_DIR / 'script_registry.json'
EXECUTION_LOG = STATE_DIR / 'script_executions.jsonl'


@dataclass
class Script:
    """A managed script in the system."""
    path: str
    name: str
    type: str  # python, bash, other

    # Understanding
    purpose: str
    category: str  # trading, monitoring, infrastructure, coordination, finance
    dependencies: List[str] = field(default_factory=list)

    # Scheduling
    schedule: str = ""  # cron expression or "manual", "on-demand"
    enabled: bool = True

    # Health
    last_run: str = ""
    last_status: str = ""  # success, failed, unknown
    run_count: int = 0
    fail_count: int = 0

    # Metadata
    hash: str = ""  # For change detection
    created: str = ""
    modified: str = ""


class ScriptManager:
    """
    Self-Managing Script System.

    The system understands and controls its own scripts.
    """

    def __init__(self):
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict:
        """Load script registry."""
        if REGISTRY_FILE.exists():
            try:
                with open(REGISTRY_FILE) as f:
                    return json.load(f)
            except:
                pass
        return {
            "master": MASTER,
            "scripts": {},
            "cron_jobs": [],
            "last_scan": None
        }

    def _save_registry(self):
        """Save script registry."""
        self.registry["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(REGISTRY_FILE, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def _log_execution(self, script_name: str, status: str, output: str = "", duration: float = 0):
        """Log script execution."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "script": script_name,
            "status": status,
            "duration_seconds": duration,
            "output_preview": output[:500] if output else ""
        }
        with open(EXECUTION_LOG, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def _get_file_hash(self, path: str) -> str:
        """Get MD5 hash of file for change detection."""
        try:
            with open(path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()[:12]
        except:
            return ""

    def _infer_purpose(self, path: str, name: str) -> Tuple[str, str]:
        """Infer script purpose from name and content."""
        name_lower = name.lower()

        # Category inference
        if any(x in name_lower for x in ['trade', 'position', 'market', 'signal']):
            category = "trading"
        elif any(x in name_lower for x in ['monitor', 'health', 'check', 'watch']):
            category = "monitoring"
        elif any(x in name_lower for x in ['scale', 'provision', 'bootstrap', 'deploy']):
            category = "infrastructure"
        elif any(x in name_lower for x in ['coordinate', 'orchestrat', 'agent']):
            category = "coordination"
        elif any(x in name_lower for x in ['cost', 'balance', 'payment', 'capital', 'finance']):
            category = "finance"
        elif any(x in name_lower for x in ['digest', 'summary', 'report', 'notify']):
            category = "reporting"
        else:
            category = "utility"

        # Purpose inference from name
        purpose_map = {
            'position_monitor': "Monitor open trading positions",
            'capital_recovery': "Track capital recovery from positions",
            'payment_monitor': "Watch for incoming payments",
            'daily_digest': "Generate daily status summary",
            'healthcheck': "Check system health",
            'run_pipeline': "Execute main trading pipeline",
            'self_healing': "Automatically fix system issues",
            'coordination': "Coordinate between system components",
            'fetch_fresh_markets': "Get latest market data",
            'snapshot_system_state': "Capture system state",
        }

        purpose = "Unknown purpose"
        for key, desc in purpose_map.items():
            if key in name_lower:
                purpose = desc
                break

        return purpose, category

    def discover_scripts(self) -> List[Script]:
        """
        Discover all scripts in the system.

        Scans scripts/ and autonomous/ directories.
        """
        scripts = []

        search_dirs = [
            SCRIPTS_DIR,
            AUTONOMOUS_DIR,
            BASE_DIR / 'trading',
            BASE_DIR / 'finance',
        ]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            for ext in ['*.py', '*.sh']:
                for path in search_dir.glob(ext):
                    if path.name.startswith('__'):
                        continue

                    name = path.stem
                    script_type = 'python' if path.suffix == '.py' else 'bash'
                    purpose, category = self._infer_purpose(str(path), name)

                    # Check if already in registry
                    existing = self.registry.get("scripts", {}).get(name, {})

                    script = Script(
                        path=str(path),
                        name=name,
                        type=script_type,
                        purpose=existing.get('purpose', purpose),
                        category=existing.get('category', category),
                        dependencies=existing.get('dependencies', []),
                        schedule=existing.get('schedule', 'manual'),
                        enabled=existing.get('enabled', True),
                        last_run=existing.get('last_run', ''),
                        last_status=existing.get('last_status', 'unknown'),
                        run_count=existing.get('run_count', 0),
                        fail_count=existing.get('fail_count', 0),
                        hash=self._get_file_hash(str(path)),
                        created=existing.get('created', datetime.now(timezone.utc).isoformat()),
                        modified=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
                    )

                    scripts.append(script)
                    self.registry["scripts"][name] = asdict(script)

        self.registry["last_scan"] = datetime.now(timezone.utc).isoformat()
        self._save_registry()

        return scripts

    def get_cron_jobs(self) -> List[Dict]:
        """Get current cron jobs."""
        try:
            result = subprocess.run(
                ['crontab', '-l'],
                capture_output=True, text=True, timeout=10
            )

            jobs = []
            for line in result.stdout.split('\n'):
                line = line.strip()
                if not line or line.startswith('#') or '=' in line.split()[0] if line.split() else True:
                    continue

                # Parse cron line
                parts = line.split()
                if len(parts) >= 6:
                    schedule = ' '.join(parts[:5])
                    command = ' '.join(parts[5:])

                    # Extract script name
                    script_name = ""
                    for part in command.split():
                        if '.py' in part or '.sh' in part:
                            script_name = Path(part).stem
                            break

                    jobs.append({
                        "schedule": schedule,
                        "command": command,
                        "script": script_name,
                        "enabled": True
                    })

            self.registry["cron_jobs"] = jobs
            self._save_registry()

            return jobs

        except Exception as e:
            print(f"[SCRIPT MANAGER] Error getting cron jobs: {e}")
            return []

    def run_script(self, name: str, args: List[str] = None, timeout: int = 300) -> Tuple[bool, str]:
        """
        Run a script by name.

        Returns (success, output).
        """
        script = self.registry.get("scripts", {}).get(name)
        if not script:
            return False, f"Script '{name}' not found"

        if not script.get('enabled', True):
            return False, f"Script '{name}' is disabled"

        path = script['path']
        script_type = script['type']
        args = args or []

        # Build command
        if script_type == 'python':
            cmd = ['python3', path] + args
        elif script_type == 'bash':
            cmd = ['bash', path] + args
        else:
            cmd = [path] + args

        start_time = datetime.now(timezone.utc)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(BASE_DIR)
            )

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            success = result.returncode == 0
            output = result.stdout + result.stderr

            # Update registry
            self.registry["scripts"][name]["last_run"] = start_time.isoformat()
            self.registry["scripts"][name]["last_status"] = "success" if success else "failed"
            self.registry["scripts"][name]["run_count"] = script.get('run_count', 0) + 1
            if not success:
                self.registry["scripts"][name]["fail_count"] = script.get('fail_count', 0) + 1

            self._save_registry()
            self._log_execution(name, "success" if success else "failed", output, duration)

            return success, output

        except subprocess.TimeoutExpired:
            self._log_execution(name, "timeout", "", timeout)
            return False, f"Script timed out after {timeout}s"
        except Exception as e:
            self._log_execution(name, "error", str(e))
            return False, str(e)

    def enable_script(self, name: str) -> bool:
        """Enable a script."""
        if name in self.registry.get("scripts", {}):
            self.registry["scripts"][name]["enabled"] = True
            self._save_registry()
            return True
        return False

    def disable_script(self, name: str) -> Tuple[bool, str]:
        """Disable a script (with self-preservation check)."""
        # SELF-PRESERVATION CHECK
        try:
            import sys
            sys.path.insert(0, str(BASE_DIR))
            from autonomous.self_preservation import block_self_harm
            allowed, reason = block_self_harm("disable_script", name)
            if not allowed:
                return False, reason
        except Exception as e:
            print(f"[DEBUG] Self-preservation check error: {e}")

        if name in self.registry.get("scripts", {}):
            self.registry["scripts"][name]["enabled"] = False
            self._save_registry()
            return True, f"Disabled: {name}"
        return False, f"Script not found: {name}"

    def set_schedule(self, name: str, schedule: str) -> bool:
        """Set script schedule (cron expression or 'manual')."""
        if name in self.registry.get("scripts", {}):
            self.registry["scripts"][name]["schedule"] = schedule
            self._save_registry()
            return True
        return False

    def add_cron_job(self, script_name: str, schedule: str) -> Tuple[bool, str]:
        """
        Add a cron job for a script.

        schedule: cron expression like "*/30 * * * *"
        """
        script = self.registry.get("scripts", {}).get(script_name)
        if not script:
            return False, f"Script '{script_name}' not found"

        path = script['path']
        script_type = script['type']

        # Build cron command
        if script_type == 'python':
            cmd = f"cd /root/hands-off-engine && python3 {path} >> /var/log/hands-off/{script_name}.log 2>&1"
        else:
            cmd = f"cd /root/hands-off-engine && {path} >> /var/log/hands-off/{script_name}.log 2>&1"

        cron_line = f"{schedule} {cmd}"

        try:
            # Get current crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            current = result.stdout if result.returncode == 0 else ""

            # Check if already exists
            if script_name in current:
                return False, f"Cron job for '{script_name}' already exists"

            # Add new job
            new_crontab = current.rstrip() + '\n' + cron_line + '\n'

            # Install new crontab
            process = subprocess.Popen(
                ['crontab', '-'],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate(input=new_crontab)

            # Update registry
            self.set_schedule(script_name, schedule)
            self.get_cron_jobs()  # Refresh

            return True, f"Added cron job: {schedule} -> {script_name}"

        except Exception as e:
            return False, str(e)

    def remove_cron_job(self, script_name: str) -> Tuple[bool, str]:
        """Remove a cron job for a script (with self-preservation check)."""
        # SELF-PRESERVATION CHECK
        try:
            import sys
            sys.path.insert(0, str(BASE_DIR))
            from autonomous.self_preservation import block_self_harm
            allowed, reason = block_self_harm("remove_cron", script_name)
            if not allowed:
                return False, reason
        except Exception as e:
            print(f"[DEBUG] Self-preservation check error: {e}")

        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode != 0:
                return False, "No crontab"

            lines = result.stdout.split('\n')
            new_lines = [l for l in lines if script_name not in l]

            if len(new_lines) == len(lines):
                return False, f"No cron job found for '{script_name}'"

            new_crontab = '\n'.join(new_lines)

            process = subprocess.Popen(
                ['crontab', '-'],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate(input=new_crontab)

            self.set_schedule(script_name, "manual")
            self.get_cron_jobs()

            return True, f"Removed cron job for '{script_name}'"

        except Exception as e:
            return False, str(e)

    def get_status(self) -> Dict:
        """Get script management status."""
        scripts = self.registry.get("scripts", {})
        cron_jobs = self.get_cron_jobs()

        # Stats
        total = len(scripts)
        enabled = sum(1 for s in scripts.values() if s.get('enabled', True))
        scheduled = sum(1 for s in scripts.values() if s.get('schedule') not in ['', 'manual'])
        failed = sum(1 for s in scripts.values() if s.get('last_status') == 'failed')

        # By category
        by_category = {}
        for s in scripts.values():
            cat = s.get('category', 'unknown')
            by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "master": MASTER,
            "total_scripts": total,
            "enabled": enabled,
            "disabled": total - enabled,
            "scheduled": scheduled,
            "cron_jobs": len(cron_jobs),
            "last_failures": failed,
            "by_category": by_category,
            "last_scan": self.registry.get("last_scan")
        }

    def get_script(self, name: str) -> Optional[Dict]:
        """Get script details."""
        return self.registry.get("scripts", {}).get(name)

    def list_scripts(self, category: str = None, enabled_only: bool = False) -> List[Dict]:
        """List scripts with optional filtering."""
        scripts = list(self.registry.get("scripts", {}).values())

        if category:
            scripts = [s for s in scripts if s.get('category') == category]

        if enabled_only:
            scripts = [s for s in scripts if s.get('enabled', True)]

        return sorted(scripts, key=lambda x: x.get('name', ''))


# Global instance
_manager: Optional[ScriptManager] = None


def get_script_manager() -> ScriptManager:
    """Get or create global script manager."""
    global _manager
    if _manager is None:
        _manager = ScriptManager()
    return _manager


# CLI
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Script Manager - System Self-Management")
    parser.add_argument("command", choices=[
        "discover", "list", "status", "run", "enable", "disable",
        "cron-list", "cron-add", "cron-remove", "show"
    ])
    parser.add_argument("--name", help="Script name")
    parser.add_argument("--category", help="Filter by category")
    parser.add_argument("--schedule", help="Cron schedule expression")
    parser.add_argument("--args", nargs='*', help="Script arguments")

    args = parser.parse_args()
    manager = get_script_manager()

    if args.command == "discover":
        scripts = manager.discover_scripts()
        print(f"\n{'='*60}")
        print(f"SCRIPT DISCOVERY - Found {len(scripts)} scripts")
        print(f"{'='*60}")
        for script in sorted(scripts, key=lambda x: x.category):
            status = "enabled" if script.enabled else "DISABLED"
            print(f"  [{script.category}] {script.name} ({script.type}) - {status}")
            print(f"           {script.purpose}")

    elif args.command == "list":
        scripts = manager.list_scripts(category=args.category)
        print(f"\n{'='*60}")
        print(f"SCRIPTS" + (f" - Category: {args.category}" if args.category else ""))
        print(f"{'='*60}")
        for s in scripts:
            status = "" if s.get('enabled', True) else "[DISABLED]"
            schedule = s.get('schedule', 'manual')
            print(f"  {s['name']} {status}")
            print(f"    Purpose: {s.get('purpose', 'Unknown')}")
            print(f"    Schedule: {schedule}")
            print(f"    Last run: {s.get('last_status', 'never')} @ {s.get('last_run', 'never')[:19] if s.get('last_run') else 'never'}")

    elif args.command == "status":
        status = manager.get_status()
        print(f"\n{'='*60}")
        print(f"SCRIPT MANAGER STATUS")
        print(f"{'='*60}")
        print(f"Total scripts: {status['total_scripts']}")
        print(f"Enabled: {status['enabled']}")
        print(f"Disabled: {status['disabled']}")
        print(f"Scheduled (cron): {status['scheduled']}")
        print(f"Active cron jobs: {status['cron_jobs']}")
        print(f"Recent failures: {status['last_failures']}")
        print(f"\nBy category:")
        for cat, count in status['by_category'].items():
            print(f"  {cat}: {count}")

    elif args.command == "run":
        if not args.name:
            print("Error: --name required")
            return
        success, output = manager.run_script(args.name, args.args)
        status = "SUCCESS" if success else "FAILED"
        print(f"\n[{status}] {args.name}")
        if output:
            print(f"\nOutput:\n{output[:1000]}")

    elif args.command == "enable":
        if not args.name:
            print("Error: --name required")
            return
        if manager.enable_script(args.name):
            print(f"Enabled: {args.name}")
        else:
            print(f"Script not found: {args.name}")

    elif args.command == "disable":
        if not args.name:
            print("Error: --name required")
            return
        success, msg = manager.disable_script(args.name)
        print(msg)

    elif args.command == "cron-list":
        jobs = manager.get_cron_jobs()
        print(f"\n{'='*60}")
        print(f"CRON JOBS - {len(jobs)} active")
        print(f"{'='*60}")
        for job in jobs:
            print(f"  {job['schedule']} -> {job['script']}")

    elif args.command == "cron-add":
        if not args.name or not args.schedule:
            print("Error: --name and --schedule required")
            return
        success, msg = manager.add_cron_job(args.name, args.schedule)
        print(msg)

    elif args.command == "cron-remove":
        if not args.name:
            print("Error: --name required")
            return
        success, msg = manager.remove_cron_job(args.name)
        print(msg)

    elif args.command == "show":
        if not args.name:
            print("Error: --name required")
            return
        script = manager.get_script(args.name)
        if script:
            print(f"\n{'='*60}")
            print(f"SCRIPT: {script['name']}")
            print(f"{'='*60}")
            print(f"Path: {script['path']}")
            print(f"Type: {script['type']}")
            print(f"Category: {script['category']}")
            print(f"Purpose: {script['purpose']}")
            print(f"Enabled: {script['enabled']}")
            print(f"Schedule: {script['schedule']}")
            print(f"Last run: {script['last_run']}")
            print(f"Last status: {script['last_status']}")
            print(f"Run count: {script['run_count']}")
            print(f"Fail count: {script['fail_count']}")
            print(f"Hash: {script['hash']}")
        else:
            print(f"Script not found: {args.name}")


if __name__ == "__main__":
    main()
