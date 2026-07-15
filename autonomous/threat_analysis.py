#!/usr/bin/env python3
"""
THREAT ANALYSIS - Find What Can Kill the System
================================================

Proactively identify threats before they become fatal.
Report to system and assist in implementing protections.

THREAT CATEGORIES:
1. INFRASTRUCTURE - Droplets dying, resources exhausted
2. FINANCIAL - Running out of money, unpaid bills
3. CREDENTIALS - API keys expiring, being revoked
4. PROCESS - Critical processes dying
5. DATA - State corruption, loss
6. EXTERNAL - Services going down
7. SELF-INFLICTED - Bugs, infinite loops, memory leaks

Serving: Yair Siegel
"""

import os
import json
import subprocess
try:
    import psutil
except ImportError:
    class DummyPsutil:
        STATUS_ZOMBIE = "zombie"

        def disk_usage(self, path):
            class D:
                percent = 0
            return D()

        def virtual_memory(self):
            class M:
                percent = 0
            return M()

        def process_iter(self, *args, **kwargs):
            return []

    psutil = DummyPsutil()

from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict, field

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'state'
STATE_DIR.mkdir(parents=True, exist_ok=True)

MASTER = "Yair Siegel"
THREAT_FILE = STATE_DIR / 'threat_analysis.json'
THREAT_LOG = STATE_DIR / 'threat_log.jsonl'


@dataclass
class Threat:
    """A detected threat to system survival."""
    id: str
    category: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    title: str
    description: str
    impact: str
    mitigation: str
    detected_at: str
    status: str = "active"  # active, mitigated, monitoring
    auto_mitigate: bool = False


class ThreatAnalyzer:
    """
    Proactive Threat Analysis System.

    Finds what can kill the system BEFORE it happens.
    """

    def __init__(self):
        self.threats: List[Threat] = []
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load threat state."""
        if THREAT_FILE.exists():
            try:
                with open(THREAT_FILE) as f:
                    return json.load(f)
            except:
                pass
        return {"threats": [], "last_scan": None, "mitigations_applied": 0}

    def _save_state(self):
        """Save threat state."""
        self.state["threats"] = [asdict(t) for t in self.threats]
        self.state["last_scan"] = datetime.now(timezone.utc).isoformat()
        with open(THREAT_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _log_threat(self, threat: Threat):
        """Log threat to append-only log."""
        with open(THREAT_LOG, 'a') as f:
            f.write(json.dumps(asdict(threat)) + '\n')

    def _add_threat(self, category: str, severity: str, title: str,
                   description: str, impact: str, mitigation: str,
                   auto_mitigate: bool = False) -> Threat:
        """Add a detected threat."""
        threat = Threat(
            id=f"{category.lower()}_{len(self.threats)+1}",
            category=category,
            severity=severity,
            title=title,
            description=description,
            impact=impact,
            mitigation=mitigation,
            detected_at=datetime.now(timezone.utc).isoformat(),
            auto_mitigate=auto_mitigate
        )
        self.threats.append(threat)
        self._log_threat(threat)
        return threat

    # ========================================================================
    # INFRASTRUCTURE THREATS
    # ========================================================================

    def check_infrastructure_threats(self) -> List[Threat]:
        """Check for infrastructure-related kill vectors."""
        threats = []

        # Check disk space
        try:
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                threats.append(self._add_threat(
                    "INFRASTRUCTURE", "CRITICAL",
                    "Disk Space Critical",
                    f"Disk usage at {disk.percent}% - only {disk.free // (1024**3)}GB free",
                    "System will crash when disk fills up. No logs, no state, no recovery.",
                    "Clean up old logs, remove unused files, expand disk",
                    auto_mitigate=True
                ))
            elif disk.percent > 80:
                threats.append(self._add_threat(
                    "INFRASTRUCTURE", "HIGH",
                    "Disk Space Warning",
                    f"Disk usage at {disk.percent}%",
                    "May run out of space soon",
                    "Monitor and clean up proactively"
                ))
        except Exception as e:
            pass

        # Check memory
        try:
            mem = psutil.virtual_memory()
            if mem.percent > 90:
                threats.append(self._add_threat(
                    "INFRASTRUCTURE", "CRITICAL",
                    "Memory Critical",
                    f"Memory usage at {mem.percent}%",
                    "OOM killer will terminate processes",
                    "Identify memory leaks, add swap, reduce load"
                ))
            elif mem.percent > 80:
                threats.append(self._add_threat(
                    "INFRASTRUCTURE", "HIGH",
                    "Memory Warning",
                    f"Memory usage at {mem.percent}%",
                    "May run out of memory soon",
                    "Monitor memory-heavy processes"
                ))
        except:
            pass

        # Check if cron is running
        try:
            result = subprocess.run(['pgrep', 'cron'], capture_output=True)
            if result.returncode != 0:
                threats.append(self._add_threat(
                    "INFRASTRUCTURE", "CRITICAL",
                    "Cron Daemon Dead",
                    "Cron is not running - scheduled tasks won't execute",
                    "All monitoring, trading, and health checks stop",
                    "Restart cron: service cron start",
                    auto_mitigate=True
                ))
        except:
            pass

        # Check droplet health
        try:
            result = subprocess.run(
                ['doctl', 'compute', 'droplet', 'list', '--format', 'Name,Status', '--no-header'],
                capture_output=True, text=True, timeout=30
            )
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        name, status = parts[0], parts[1]
                        if status != 'active':
                            threats.append(self._add_threat(
                                "INFRASTRUCTURE", "HIGH",
                                f"Droplet Not Active: {name}",
                                f"Droplet {name} has status '{status}'",
                                "Lost compute capacity, potential service disruption",
                                "Investigate and restart droplet"
                            ))
        except:
            pass

        return threats

    # ========================================================================
    # FINANCIAL THREATS
    # ========================================================================

    def check_financial_threats(self) -> List[Threat]:
        """Check for financial kill vectors."""
        threats = []

        # Check balance
        try:
            from trading.balance_tracker import BalanceTracker
            tracker = BalanceTracker()
            balance = tracker.get_usdc_balance()

            if balance < 1:
                threats.append(self._add_threat(
                    "FINANCIAL", "CRITICAL",
                    "Zero Balance",
                    f"Balance is ${balance:.2f} - cannot trade or pay for services",
                    "System cannot generate income, may lose infrastructure",
                    "Need capital injection or position resolution"
                ))
            elif balance < 10:
                threats.append(self._add_threat(
                    "FINANCIAL", "HIGH",
                    "Low Balance Warning",
                    f"Balance is ${balance:.2f}",
                    "Limited trading capacity, infrastructure at risk",
                    "Focus on capital recovery, minimize costs"
                ))
        except:
            pass

        # Check infrastructure cost vs balance
        try:
            from finance.cost_tracker import get_cost_tracker
            tracker = get_cost_tracker()
            monthly_cost = tracker.get_monthly_cost()

            if monthly_cost > 0:
                # Check if we can afford infrastructure
                from trading.balance_tracker import BalanceTracker
                bt = BalanceTracker()
                balance = bt.get_usdc_balance()

                months_runway = balance / monthly_cost if monthly_cost > 0 else float('inf')

                if months_runway < 1:
                    threats.append(self._add_threat(
                        "FINANCIAL", "CRITICAL",
                        "Infrastructure Unaffordable",
                        f"Monthly cost ${monthly_cost:.2f} exceeds balance ${balance:.2f}",
                        "Will lose infrastructure within days",
                        "Reduce infrastructure or inject capital"
                    ))
        except:
            pass

        return threats

    # ========================================================================
    # CREDENTIAL THREATS
    # ========================================================================

    def check_credential_threats(self) -> List[Threat]:
        """Check for credential-related kill vectors."""
        threats = []

        env_path = BASE_DIR / '.env'
        env_poly_path = BASE_DIR / '.env.polymarket'

        if not env_path.exists():
            threats.append(self._add_threat(
                "CREDENTIALS", "CRITICAL",
                "Environment File Missing",
                ".env file not found - no API credentials",
                "Cannot connect to any external service",
                "Restore .env from backup"
            ))
            return threats

        # Combine all env files for checking
        try:
            env_content = ""
            for env_file in [env_path, env_poly_path]:
                if env_file.exists():
                    with open(env_file) as f:
                        env_content += f.read()

            essential_keys = [
                ('POLY', 'Trading'),  # POLY_API_KEY, POLYMARKET, etc.
                ('DO_API', 'Infrastructure'),
            ]

            for key_prefix, service in essential_keys:
                if key_prefix not in env_content:
                    threats.append(self._add_threat(
                        "CREDENTIALS", "HIGH",
                        f"Missing {service} Credentials",
                        f"No {key_prefix}* keys found in any .env file",
                        f"Cannot access {service} services",
                        f"Add {service} API credentials"
                    ))
        except:
            pass

        # Check for empty/placeholder keys
        try:
            from dotenv import dotenv_values
            config = dotenv_values(env_path)

            for key, value in config.items():
                if value and ('xxx' in value.lower() or 'your_' in value.lower() or value == ''):
                    threats.append(self._add_threat(
                        "CREDENTIALS", "MEDIUM",
                        f"Placeholder Credential: {key}",
                        f"{key} appears to be a placeholder value",
                        "This service won't work",
                        f"Replace {key} with actual credential"
                    ))
        except:
            pass

        return threats

    # ========================================================================
    # PROCESS THREATS
    # ========================================================================

    def check_process_threats(self) -> List[Threat]:
        """Check for process-related kill vectors."""
        threats = []

        # Check critical cron jobs are in crontab
        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            crontab = result.stdout

            critical_jobs = ['healthcheck', 'position_monitor']
            for job in critical_jobs:
                if job not in crontab:
                    threats.append(self._add_threat(
                        "PROCESS", "HIGH",
                        f"Missing Critical Cron: {job}",
                        f"{job} is not in crontab",
                        "Critical monitoring not running",
                        f"Add {job} to crontab"
                    ))
        except:
            pass

        # Check for zombie processes
        try:
            zombies = [p for p in psutil.process_iter(['status'])
                      if p.info['status'] == psutil.STATUS_ZOMBIE]
            if len(zombies) > 10:
                threats.append(self._add_threat(
                    "PROCESS", "MEDIUM",
                    "Zombie Processes Accumulating",
                    f"Found {len(zombies)} zombie processes",
                    "May indicate parent process issues",
                    "Investigate and clean up parent processes"
                ))
        except:
            pass

        return threats

    # ========================================================================
    # DATA THREATS
    # ========================================================================

    def check_data_threats(self) -> List[Threat]:
        """Check for data-related kill vectors."""
        threats = []

        critical_files = [
            ('state/unified_system_state.json', 'System State'),
            ('state/brain_state.json', 'AI Brain State'),
            ('state/script_registry.json', 'Script Registry'),
            ('.env', 'Environment Config'),
        ]

        for filepath, name in critical_files:
            full_path = BASE_DIR / filepath
            if not full_path.exists():
                threats.append(self._add_threat(
                    "DATA", "HIGH",
                    f"Missing Critical File: {name}",
                    f"{filepath} not found",
                    f"System cannot operate without {name}",
                    "Restore from backup or recreate"
                ))
            else:
                # Check if file is valid JSON
                if filepath.endswith('.json'):
                    try:
                        with open(full_path) as f:
                            json.load(f)
                    except json.JSONDecodeError:
                        threats.append(self._add_threat(
                            "DATA", "HIGH",
                            f"Corrupted File: {name}",
                            f"{filepath} contains invalid JSON",
                            f"System may crash when reading {name}",
                            "Restore from backup"
                        ))

        # Check for backup existence
        backup_dir = BASE_DIR / 'backups'
        if not backup_dir.exists() or not list(backup_dir.glob('*')):
            threats.append(self._add_threat(
                "DATA", "MEDIUM",
                "No Backups Exist",
                "No backup directory or empty",
                "Cannot recover from data loss",
                "Implement regular backups"
            ))

        return threats

    # ========================================================================
    # EXTERNAL THREATS
    # ========================================================================

    def check_external_threats(self) -> List[Threat]:
        """Check for external dependency threats."""
        threats = []

        # Check GitHub connectivity
        try:
            result = subprocess.run(
                ['git', 'ls-remote', '--exit-code', 'origin'],
                capture_output=True, timeout=10, cwd=str(BASE_DIR)
            )
            if result.returncode != 0:
                threats.append(self._add_threat(
                    "EXTERNAL", "MEDIUM",
                    "GitHub Unreachable",
                    "Cannot connect to GitHub repository",
                    "Cannot push/pull code changes",
                    "Check network or GitHub status"
                ))
        except:
            pass

        return threats

    # ========================================================================
    # SELF-INFLICTED THREATS
    # ========================================================================

    def check_self_inflicted_threats(self) -> List[Threat]:
        """Check for self-inflicted kill vectors."""
        threats = []

        # Check for runaway processes (high CPU for long time)
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'create_time']):
                try:
                    cpu = proc.cpu_percent(interval=0.1)
                    age = datetime.now().timestamp() - proc.info['create_time']
                    if cpu > 80 and age > 300:  # 80% CPU for 5+ minutes
                        threats.append(self._add_threat(
                            "SELF_INFLICTED", "MEDIUM",
                            f"Runaway Process: {proc.info['name']}",
                            f"PID {proc.info['pid']} using {cpu}% CPU for {age/60:.0f} minutes",
                            "May be infinite loop or resource exhaustion",
                            f"Investigate process {proc.info['pid']}"
                        ))
                except:
                    pass
        except:
            pass

        # Check for potential infinite loops in logs
        try:
            log_dir = Path(__file__).resolve().parent.parent / 'logs'
            if log_dir.exists():
                for log_file in log_dir.glob('*.log'):
                    size = log_file.stat().st_size
                    if size > 100 * 1024 * 1024:  # 100MB
                        threats.append(self._add_threat(
                            "SELF_INFLICTED", "MEDIUM",
                            f"Log File Explosion: {log_file.name}",
                            f"Log file is {size // (1024*1024)}MB",
                            "May indicate infinite loop or excessive logging",
                            "Investigate and rotate logs"
                        ))
        except:
            pass

        return threats

    # ========================================================================
    # MAIN ANALYSIS
    # ========================================================================

    def run_full_analysis(self) -> List[Threat]:
        """Run complete threat analysis."""
        self.threats = []

        print(f"\n{'='*60}")
        print("THREAT ANALYSIS - Finding What Can Kill The System")
        print(f"{'='*60}")

        # Run all checks
        checks = [
            ("Infrastructure", self.check_infrastructure_threats),
            ("Financial", self.check_financial_threats),
            ("Credentials", self.check_credential_threats),
            ("Process", self.check_process_threats),
            ("Data", self.check_data_threats),
            ("External", self.check_external_threats),
            ("Self-Inflicted", self.check_self_inflicted_threats),
        ]

        for name, check_func in checks:
            print(f"\nChecking {name}...")
            try:
                check_func()
            except Exception as e:
                print(f"  Error in {name} check: {e}")

        self._save_state()
        return self.threats

    def get_report(self) -> Dict:
        """Get threat analysis report."""
        by_severity = {}
        by_category = {}

        for threat in self.threats:
            by_severity[threat.severity] = by_severity.get(threat.severity, 0) + 1
            by_category[threat.category] = by_category.get(threat.category, 0) + 1

        critical = [t for t in self.threats if t.severity == "CRITICAL"]
        high = [t for t in self.threats if t.severity == "HIGH"]

        return {
            "master": MASTER,
            "total_threats": len(self.threats),
            "by_severity": by_severity,
            "by_category": by_category,
            "critical_threats": [asdict(t) for t in critical],
            "high_threats": [asdict(t) for t in high],
            "auto_mitigatable": sum(1 for t in self.threats if t.auto_mitigate),
            "scan_time": datetime.now(timezone.utc).isoformat()
        }

    def print_report(self):
        """Print human-readable threat report."""
        report = self.get_report()

        print(f"\n{'='*60}")
        print("THREAT ANALYSIS REPORT")
        print(f"{'='*60}")
        print(f"Master: {report['master']}")
        print(f"Total Threats: {report['total_threats']}")

        print(f"\nBy Severity:")
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = report['by_severity'].get(sev, 0)
            if count > 0:
                print(f"  {sev}: {count}")

        print(f"\nBy Category:")
        for cat, count in report['by_category'].items():
            print(f"  {cat}: {count}")

        if report['critical_threats']:
            print(f"\n{'!'*60}")
            print("CRITICAL THREATS - IMMEDIATE ACTION REQUIRED")
            print(f"{'!'*60}")
            for threat in report['critical_threats']:
                print(f"\n  [{threat['id']}] {threat['title']}")
                print(f"    {threat['description']}")
                print(f"    Impact: {threat['impact']}")
                print(f"    Mitigation: {threat['mitigation']}")

        if report['high_threats']:
            print(f"\nHIGH PRIORITY THREATS:")
            for threat in report['high_threats']:
                print(f"  - {threat['title']}: {threat['description']}")

        print(f"\n{'='*60}")


# Global instance
_analyzer: Optional[ThreatAnalyzer] = None


def get_threat_analyzer() -> ThreatAnalyzer:
    """Get or create global threat analyzer."""
    global _analyzer
    if _analyzer is None:
        _analyzer = ThreatAnalyzer()
    return _analyzer


def analyze_threats() -> List[Threat]:
    """Main API: Run threat analysis."""
    analyzer = get_threat_analyzer()
    return analyzer.run_full_analysis()


# CLI
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Threat Analysis - Find Kill Vectors")
    parser.add_argument("command", choices=["scan", "report", "mitigate"], nargs='?', default="scan")

    args = parser.parse_args()
    analyzer = get_threat_analyzer()

    if args.command == "scan":
        analyzer.run_full_analysis()
        analyzer.print_report()

    elif args.command == "report":
        # Load existing threats
        if analyzer.state.get("threats"):
            for t_data in analyzer.state["threats"]:
                analyzer.threats.append(Threat(**t_data))
        analyzer.print_report()

    elif args.command == "mitigate":
        analyzer.run_full_analysis()
        print("\n[MITIGATION MODE]")
        for threat in analyzer.threats:
            if threat.auto_mitigate:
                print(f"\nAuto-mitigating: {threat.title}")
                print(f"  Action: {threat.mitigation}")
                # Here we could add actual mitigation logic


if __name__ == "__main__":
    main()
