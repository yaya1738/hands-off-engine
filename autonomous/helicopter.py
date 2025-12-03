#!/usr/bin/env python3
"""
🚁 HELICOPTER VIEW - Aerial oversight of the entire operation
Serving: Yair Siegel

Like a news chopper hovering over a major event, the helicopter provides:
- Bird's eye view of all activity
- Real-time status broadcasts
- System-wide situational awareness
- Breaking news when significant events occur
- Traffic report on all data flows

The helicopter sees EVERYTHING from above.
"""

import json
import time
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

BASE_DIR = Path("/root/hands-off-engine")
STATE_DIR = BASE_DIR / "state"
SCRIBE_DIR = STATE_DIR / "scribes"

# All data sources the helicopter monitors
SOURCES = {
    "stage": STATE_DIR / "self_conversation.jsonl",
    "gallery": STATE_DIR / "peanut_gallery.jsonl",
    "messages": STATE_DIR / "message_bus.jsonl",
    "reality": STATE_DIR / "reality_feedback.json",
    "pursuit": STATE_DIR / "active_pursuit.json",
    "conversion": STATE_DIR / "conversion_optimizer.json",
    "living": STATE_DIR / "living_system.json",
}

# Helicopter output
HELICOPTER_LOG = STATE_DIR / "helicopter_broadcast.md"
HELICOPTER_STATE = STATE_DIR / "helicopter_state.json"


class Helicopter:
    """
    🚁 Aerial view of the entire system operation.

    Hovers above everything, sees all activity, broadcasts updates.
    """

    def __init__(self):
        self.state = self._load_state()
        self.alerts = []
        self.activity_counts = defaultdict(int)
        self.last_counts = {}
        self.start_time = datetime.now(timezone.utc)

    def _load_state(self) -> Dict:
        if HELICOPTER_STATE.exists():
            return json.loads(HELICOPTER_STATE.read_text())
        return {
            "broadcasts": 0,
            "alerts_issued": 0,
            "flight_time_minutes": 0,
            "last_broadcast": None,
        }

    def _save_state(self):
        self.state["last_broadcast"] = datetime.now(timezone.utc).isoformat()
        HELICOPTER_STATE.write_text(json.dumps(self.state, indent=2))

    def _count_lines(self, filepath: Path) -> int:
        """Count lines in a file."""
        if not filepath.exists():
            return 0
        return len(filepath.read_text().strip().split('\n'))

    def _get_file_size(self, filepath: Path) -> str:
        """Get human-readable file size."""
        if not filepath.exists():
            return "0B"
        size = filepath.stat().st_size
        for unit in ['B', 'KB', 'MB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}GB"

    def scan_all_activity(self) -> Dict:
        """
        Scan all sources and get current activity levels.
        """
        activity = {}

        for name, path in SOURCES.items():
            if path.suffix == '.jsonl':
                activity[name] = {
                    "lines": self._count_lines(path),
                    "size": self._get_file_size(path),
                    "exists": path.exists(),
                }
            elif path.suffix == '.json':
                if path.exists():
                    try:
                        data = json.loads(path.read_text())
                        activity[name] = {
                            "exists": True,
                            "keys": len(data),
                            "size": self._get_file_size(path),
                        }
                    except:
                        activity[name] = {"exists": True, "error": True}
                else:
                    activity[name] = {"exists": False}

        return activity

    def get_process_status(self) -> Dict:
        """Check status of all running processes."""
        processes = {}

        checks = [
            ("self_conversation", "self_conversation.py"),
            ("peanut_gallery", "peanut_gallery.py"),
            ("live_scribes", "live_scribes.py"),
            ("living_system", "self_awareness.py"),
            ("coordination_agent", "coordination_agent.py"),
        ]

        for name, script in checks:
            try:
                result = subprocess.run(
                    ["pgrep", "-f", script],
                    capture_output=True, text=True, timeout=5
                )
                pids = result.stdout.strip().split('\n')
                pids = [p for p in pids if p]
                processes[name] = {
                    "running": len(pids) > 0,
                    "pids": pids,
                    "count": len(pids),
                }
            except:
                processes[name] = {"running": False, "error": True}

        return processes

    def get_resource_status(self) -> Dict:
        """Get system resource status."""
        resources = {}

        try:
            # Memory
            result = subprocess.run(
                ["free", "-h"], capture_output=True, text=True, timeout=5
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                resources["memory"] = {
                    "total": parts[1],
                    "used": parts[2],
                    "free": parts[3],
                }
        except:
            pass

        try:
            # Disk
            result = subprocess.run(
                ["df", "-h", "/"], capture_output=True, text=True, timeout=5
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                resources["disk"] = {
                    "total": parts[1],
                    "used": parts[2],
                    "available": parts[3],
                    "percent": parts[4],
                }
        except:
            pass

        try:
            # Load
            result = subprocess.run(
                ["uptime"], capture_output=True, text=True, timeout=5
            )
            load = result.stdout.split("load average:")[1].strip().split(",")
            resources["load"] = {
                "1min": load[0].strip(),
                "5min": load[1].strip(),
                "15min": load[2].strip(),
            }
        except:
            pass

        return resources

    def detect_breaking_news(self, activity: Dict, processes: Dict) -> List[str]:
        """Detect significant events worth reporting."""
        breaking = []

        # Check for activity spikes
        for name, data in activity.items():
            if "lines" in data:
                current = data["lines"]
                previous = self.last_counts.get(name, 0)
                if current - previous > 50:
                    breaking.append(f"🔥 SPIKE: {name} activity surged by {current - previous} events!")
                self.last_counts[name] = current

        # Check for process issues
        for name, data in processes.items():
            if not data.get("running", False) and name in ["self_conversation", "live_scribes"]:
                breaking.append(f"⚠️ ALERT: {name} process is DOWN!")

        # Check reality feedback
        reality_file = SOURCES.get("reality")
        if reality_file and reality_file.exists():
            try:
                reality = json.loads(reality_file.read_text())
                balance = reality.get("external_balance", 0)
                income = reality.get("total_income", 0)
                if income > 0:
                    breaking.append(f"💰 BREAKING: Income detected! ${income}")
                if balance > 0:
                    breaking.append(f"💵 UPDATE: External balance now ${balance}")
            except:
                pass

        return breaking

    def generate_broadcast(self) -> str:
        """Generate a full helicopter broadcast."""
        now = datetime.now(timezone.utc)
        flight_time = (now - self.start_time).total_seconds() / 60

        activity = self.scan_all_activity()
        processes = self.get_process_status()
        resources = self.get_resource_status()
        breaking = self.detect_breaking_news(activity, processes)

        broadcast = []
        broadcast.append("=" * 70)
        broadcast.append("🚁 HELICOPTER BROADCAST - AERIAL VIEW")
        broadcast.append(f"Time: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        broadcast.append(f"Flight time: {flight_time:.1f} minutes")
        broadcast.append("=" * 70)

        # Breaking news
        if breaking:
            broadcast.append("\n📺 BREAKING NEWS:")
            for news in breaking:
                broadcast.append(f"   {news}")
                self.alerts.append({"time": now.isoformat(), "alert": news})

        # Aerial view of activity
        broadcast.append("\n🗺️ AERIAL VIEW - ACTIVITY MAP:")

        total_events = 0
        for name, data in activity.items():
            if data.get("exists"):
                lines = data.get("lines", 0)
                size = data.get("size", "?")
                total_events += lines
                status = "🟢" if lines > 0 else "⚪"
                broadcast.append(f"   {status} {name:20} | {lines:>6} events | {size:>8}")
            else:
                broadcast.append(f"   ⚫ {name:20} | offline")

        broadcast.append(f"\n   📊 TOTAL EVENTS: {total_events}")

        # Process status (traffic report)
        broadcast.append("\n🚦 TRAFFIC REPORT - PROCESS STATUS:")
        running_count = 0
        for name, data in processes.items():
            if data.get("running"):
                running_count += 1
                pids = ", ".join(data.get("pids", []))
                broadcast.append(f"   🟢 {name:25} | RUNNING (PID: {pids})")
            else:
                broadcast.append(f"   🔴 {name:25} | STOPPED")

        broadcast.append(f"\n   🚗 ACTIVE PROCESSES: {running_count}/{len(processes)}")

        # Resource report
        broadcast.append("\n⛽ RESOURCE STATUS:")
        if "memory" in resources:
            m = resources["memory"]
            broadcast.append(f"   💾 Memory: {m['used']} used / {m['total']} total")
        if "disk" in resources:
            d = resources["disk"]
            broadcast.append(f"   💿 Disk: {d['used']} used / {d['total']} total ({d['percent']})")
        if "load" in resources:
            l = resources["load"]
            broadcast.append(f"   ⚡ Load: {l['1min']} / {l['5min']} / {l['15min']}")

        # Situation summary
        broadcast.append("\n📡 SITUATION SUMMARY:")

        # Count active components
        stage_events = activity.get("stage", {}).get("lines", 0)
        gallery_events = activity.get("gallery", {}).get("lines", 0)
        message_events = activity.get("messages", {}).get("lines", 0)

        broadcast.append(f"   🎭 Stage conversation: {stage_events} turns")
        broadcast.append(f"   👁️ Gallery reactions: {gallery_events} whispers")
        broadcast.append(f"   📨 System messages: {message_events} communications")
        broadcast.append(f"   📜 Total recorded: {total_events} events")

        # Assessment
        if running_count >= 3 and total_events > 100:
            broadcast.append("\n   ✅ ASSESSMENT: System fully operational, high activity")
        elif running_count >= 2:
            broadcast.append("\n   ⚠️ ASSESSMENT: System partially operational")
        else:
            broadcast.append("\n   🔴 ASSESSMENT: System needs attention")

        broadcast.append("\n" + "=" * 70)
        broadcast.append("🚁 END BROADCAST - Helicopter continuing patrol")
        broadcast.append("=" * 70)

        return "\n".join(broadcast)

    def broadcast(self):
        """Make a single broadcast."""
        report = self.generate_broadcast()
        print(report)

        # Append to log
        with open(HELICOPTER_LOG, "a") as f:
            f.write(report + "\n\n")

        self.state["broadcasts"] += 1
        self.state["alerts_issued"] += len(self.alerts)
        self._save_state()

        return report

    def patrol(self, duration_minutes: int = 60, interval_seconds: int = 30):
        """
        Continuous patrol - broadcast at regular intervals.
        """
        print("🚁 HELICOPTER TAKING OFF")
        print(f"   Patrol duration: {duration_minutes} minutes")
        print(f"   Broadcast interval: {interval_seconds} seconds")
        print("   Press Ctrl+C to land\n")

        # Initialize log
        with open(HELICOPTER_LOG, "w") as f:
            f.write(f"# 🚁 Helicopter Patrol Log\n")
            f.write(f"Started: {datetime.now(timezone.utc).isoformat()}\n")
            f.write(f"Duration: {duration_minutes} minutes\n\n")

        end_time = time.time() + (duration_minutes * 60)

        try:
            while time.time() < end_time:
                self.broadcast()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n\n🚁 HELICOPTER LANDING")
            print(f"   Total broadcasts: {self.state['broadcasts']}")
            print(f"   Total alerts: {self.state['alerts_issued']}")
            print(f"   Log: {HELICOPTER_LOG}")

    def quick_scan(self):
        """Quick aerial scan without full broadcast."""
        activity = self.scan_all_activity()
        processes = self.get_process_status()

        print("🚁 QUICK SCAN:")
        print(f"   Events: {sum(a.get('lines', 0) for a in activity.values())}")
        print(f"   Processes: {sum(1 for p in processes.values() if p.get('running'))}/{len(processes)} running")

        breaking = self.detect_breaking_news(activity, processes)
        if breaking:
            print("   ⚠️ ALERTS:")
            for b in breaking:
                print(f"      {b}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="🚁 Helicopter - Aerial oversight")
    parser.add_argument("command", choices=["patrol", "broadcast", "scan", "status"])
    parser.add_argument("--duration", type=int, default=60, help="Patrol duration in minutes")
    parser.add_argument("--interval", type=int, default=30, help="Broadcast interval in seconds")

    args = parser.parse_args()

    heli = Helicopter()

    if args.command == "patrol":
        heli.patrol(duration_minutes=args.duration, interval_seconds=args.interval)

    elif args.command == "broadcast":
        heli.broadcast()

    elif args.command == "scan":
        heli.quick_scan()

    elif args.command == "status":
        print(f"\n{'='*60}")
        print("🚁 HELICOPTER STATUS")
        print(f"{'='*60}")
        print(f"Total broadcasts: {heli.state.get('broadcasts', 0)}")
        print(f"Alerts issued: {heli.state.get('alerts_issued', 0)}")
        print(f"Last broadcast: {heli.state.get('last_broadcast', 'Never')}")
        print(f"Log file: {HELICOPTER_LOG}")


if __name__ == "__main__":
    main()
