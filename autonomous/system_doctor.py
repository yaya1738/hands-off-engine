#!/usr/bin/env python3
"""
🩺 SYSTEM DOCTOR - Diagnose, Prescribe, Heal
Serving: Yair Siegel

The doctor examines the system, identifies problems, and prescribes fixes.

EXAMINATION:
- Check all components health
- Verify connections work
- Test data flows
- Measure vital signs

DIAGNOSIS:
- Identify root causes
- Prioritize by severity
- Track recurring issues

PRESCRIPTION:
- Recommend fixes
- Execute treatments
- Monitor recovery
"""

import json
import subprocess
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict

BASE_DIR = Path("/root/hands-off-engine")
STATE_DIR = BASE_DIR / "state"

# Doctor state files
DOCTOR_STATE = STATE_DIR / "doctor_state.json"
DIAGNOSIS_LOG = STATE_DIR / "diagnosis_log.jsonl"
TREATMENT_LOG = STATE_DIR / "treatment_log.jsonl"


@dataclass
class Symptom:
    """A detected problem."""
    component: str
    severity: str  # critical, warning, info
    symptom: str
    details: str = ""


@dataclass
class Diagnosis:
    """Root cause analysis."""
    symptoms: List[Symptom]
    root_cause: str
    affected_systems: List[str]
    priority: int  # 1=highest


@dataclass
class Treatment:
    """Prescribed fix."""
    diagnosis: str
    treatment: str
    command: str = ""
    manual_steps: List[str] = None
    executed: bool = False
    success: bool = False


class SystemDoctor:
    """
    🩺 The doctor that keeps the system healthy.
    """

    def __init__(self):
        self.state = self._load_state()
        self.symptoms: List[Symptom] = []
        self.diagnoses: List[Diagnosis] = []
        self.treatments: List[Treatment] = []
        self._sensitive_data: Dict = {}  # Privileged data collected during examination

    def _load_state(self) -> Dict:
        if DOCTOR_STATE.exists():
            return json.loads(DOCTOR_STATE.read_text())
        return {
            "examinations": 0,
            "issues_found": 0,
            "treatments_applied": 0,
            "last_exam": None,
        }

    def _save_state(self):
        DOCTOR_STATE.write_text(json.dumps(self.state, indent=2))

    def _log_diagnosis(self, diagnosis: Diagnosis):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "root_cause": diagnosis.root_cause,
            "priority": diagnosis.priority,
            "affected": diagnosis.affected_systems,
            "symptoms": [asdict(s) for s in diagnosis.symptoms],
        }
        with open(DIAGNOSIS_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _log_treatment(self, treatment: Treatment):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "diagnosis": treatment.diagnosis,
            "treatment": treatment.treatment,
            "executed": treatment.executed,
            "success": treatment.success,
        }
        with open(TREATMENT_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")

    # ═══════════════════════════════════════════════════════════
    # EXAMINATION - Check vital signs
    # ═══════════════════════════════════════════════════════════

    def check_processes(self) -> List[Symptom]:
        """Check if critical processes are running."""
        symptoms = []
        critical_processes = [
            ("evolution_engine", "evolution_engine.py"),
            ("coordination", "coordination_agent.py"),
            ("self_healing", "self_healing_agent.py"),
        ]

        for name, pattern in critical_processes:
            try:
                result = subprocess.run(
                    ["pgrep", "-f", pattern],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode != 0:
                    symptoms.append(Symptom(
                        component=name,
                        severity="warning",
                        symptom=f"{name} process not running",
                        details=f"Pattern: {pattern}"
                    ))
            except:
                pass

        return symptoms

    def check_state_files(self) -> List[Symptom]:
        """Check if critical state files exist and are recent."""
        symptoms = []
        critical_files = [
            ("evolution_state", "evolution_state.json", 3600),  # 1 hour
            ("reality_feedback", "reality_feedback.json", 7200),  # 2 hours
            ("coordination", "coordination_state.json", 3600),
        ]

        now = datetime.now(timezone.utc).timestamp()

        for name, filename, max_age in critical_files:
            filepath = STATE_DIR / filename
            if not filepath.exists():
                symptoms.append(Symptom(
                    component=name,
                    severity="warning",
                    symptom=f"State file missing: {filename}",
                ))
            else:
                age = now - filepath.stat().st_mtime
                if age > max_age:
                    symptoms.append(Symptom(
                        component=name,
                        severity="info",
                        symptom=f"State file stale: {filename}",
                        details=f"Age: {age/3600:.1f} hours"
                    ))

        return symptoms

    def check_actuators(self) -> List[Symptom]:
        """Check if actuators are functional."""
        symptoms = []

        try:
            from autonomous.actuators import ActuatorHub
            hub = ActuatorHub()
            status = hub.status()

            if not status.get("telegram", {}).get("configured"):
                symptoms.append(Symptom(
                    component="telegram",
                    severity="warning",
                    symptom="Telegram actuator not configured",
                ))

            if not status.get("polymarket", {}).get("healthy"):
                symptoms.append(Symptom(
                    component="polymarket",
                    severity="warning",
                    symptom="Polymarket actuator unhealthy",
                ))

        except Exception as e:
            symptoms.append(Symptom(
                component="actuators",
                severity="critical",
                symptom="Actuators module failed to load",
                details=str(e)
            ))

        return symptoms

    def check_finances(self) -> List[Symptom]:
        """Check financial health."""
        symptoms = []

        reality_file = STATE_DIR / "reality_feedback.json"
        if reality_file.exists():
            try:
                data = json.loads(reality_file.read_text())
                balance = data.get("external_balance", 0)
                income = data.get("total_income", 0)

                if balance <= 0:
                    symptoms.append(Symptom(
                        component="finance",
                        severity="critical",
                        symptom="Zero or negative balance",
                        details=f"Balance: ${balance}"
                    ))
                elif balance < 10:
                    symptoms.append(Symptom(
                        component="finance",
                        severity="warning",
                        symptom="Low balance",
                        details=f"Balance: ${balance}"
                    ))

                if income == 0:
                    symptoms.append(Symptom(
                        component="income",
                        severity="critical",
                        symptom="Zero income",
                        details="No revenue generated yet"
                    ))

            except:
                pass

        return symptoms

    def check_endpoints(self) -> List[Symptom]:
        """Check endpoint health from registry."""
        symptoms = []

        registry_file = STATE_DIR / "endpoint_registry.json"
        if registry_file.exists():
            try:
                data = json.loads(registry_file.read_text())
                endpoints = data.get("endpoints", {})

                for name, stats in endpoints.items():
                    executions = stats.get("executions", 0)
                    successes = stats.get("successes", 0)

                    if executions > 5:
                        rate = successes / executions
                        if rate < 0.5:
                            symptoms.append(Symptom(
                                component=f"endpoint_{name}",
                                severity="warning",
                                symptom=f"Low success rate: {name}",
                                details=f"{rate*100:.0f}% success ({successes}/{executions})"
                            ))

            except:
                pass

        return symptoms

    def check_disk_space(self) -> List[Symptom]:
        """Check disk space."""
        symptoms = []

        try:
            stat = os.statvfs("/")
            free_gb = (stat.f_frsize * stat.f_bavail) / (1024**3)

            if free_gb < 1:
                symptoms.append(Symptom(
                    component="disk",
                    severity="critical",
                    symptom="Disk space critical",
                    details=f"Free: {free_gb:.1f} GB"
                ))
            elif free_gb < 5:
                symptoms.append(Symptom(
                    component="disk",
                    severity="warning",
                    symptom="Disk space low",
                    details=f"Free: {free_gb:.1f} GB"
                ))

        except:
            pass

        return symptoms

    def check_cron_jobs(self) -> List[Symptom]:
        """Check if scheduled jobs are configured."""
        symptoms = []

        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                symptoms.append(Symptom(
                    component="scheduler",
                    severity="warning",
                    symptom="No cron jobs configured",
                    details="System may not run autonomously"
                ))
            else:
                lines = [l for l in result.stdout.split('\n') if l.strip() and not l.startswith('#')]
                if len(lines) < 3:
                    symptoms.append(Symptom(
                        component="scheduler",
                        severity="info",
                        symptom=f"Only {len(lines)} cron jobs active",
                        details="Consider adding more automation"
                    ))
        except:
            pass

        return symptoms

    def check_log_files(self) -> List[Symptom]:
        """Check log file health."""
        symptoms = []
        log_dir = Path("/var/log/hands-off")

        if not log_dir.exists():
            symptoms.append(Symptom(
                component="logging",
                severity="warning",
                symptom="Log directory missing",
                details=str(log_dir)
            ))
            return symptoms

        # Check for oversized logs
        for log_file in log_dir.glob("*.log"):
            try:
                size_mb = log_file.stat().st_size / (1024 * 1024)
                if size_mb > 100:
                    symptoms.append(Symptom(
                        component="logging",
                        severity="warning",
                        symptom=f"Large log file: {log_file.name}",
                        details=f"Size: {size_mb:.1f} MB"
                    ))
            except:
                pass

        return symptoms

    def check_git_status(self) -> List[Symptom]:
        """Check git repository health."""
        symptoms = []

        try:
            # Check for uncommitted changes
            result = subprocess.run(
                ["git", "-C", str(BASE_DIR), "status", "--porcelain"],
                capture_output=True, text=True, timeout=10
            )
            if result.stdout.strip():
                lines = len(result.stdout.strip().split('\n'))
                if lines > 50:
                    symptoms.append(Symptom(
                        component="git",
                        severity="warning",
                        symptom=f"{lines} uncommitted changes",
                        details="Consider committing or cleaning"
                    ))

            # Check if ahead of remote
            result = subprocess.run(
                ["git", "-C", str(BASE_DIR), "status", "-sb"],
                capture_output=True, text=True, timeout=10
            )
            if "ahead" in result.stdout:
                symptoms.append(Symptom(
                    component="git",
                    severity="info",
                    symptom="Unpushed commits",
                    details="Local ahead of remote"
                ))

        except:
            pass

        return symptoms

    def check_memory(self) -> List[Symptom]:
        """Check memory usage."""
        symptoms = []

        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = {}
                for line in f:
                    parts = line.split(':')
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = parts[1].strip().split()[0]
                        meminfo[key] = int(val)

            total = meminfo.get('MemTotal', 1)
            available = meminfo.get('MemAvailable', 0)
            used_pct = ((total - available) / total) * 100

            if used_pct > 90:
                symptoms.append(Symptom(
                    component="memory",
                    severity="critical",
                    symptom="Memory usage critical",
                    details=f"Used: {used_pct:.0f}%"
                ))
            elif used_pct > 80:
                symptoms.append(Symptom(
                    component="memory",
                    severity="warning",
                    symptom="Memory usage high",
                    details=f"Used: {used_pct:.0f}%"
                ))

        except:
            pass

        return symptoms

    def check_network(self) -> List[Symptom]:
        """Check network connectivity."""
        symptoms = []

        endpoints = [
            ("telegram", "api.telegram.org"),
            ("polymarket", "clob.polymarket.com"),
            ("github", "github.com"),
        ]

        for name, host in endpoints:
            try:
                result = subprocess.run(
                    ["ping", "-c", "1", "-W", "3", host],
                    capture_output=True, timeout=5
                )
                if result.returncode != 0:
                    symptoms.append(Symptom(
                        component=f"network_{name}",
                        severity="warning",
                        symptom=f"Cannot reach {name}",
                        details=f"Host: {host}"
                    ))
            except:
                pass

        return symptoms

    def check_python_imports(self) -> List[Symptom]:
        """Check if critical Python modules are importable."""
        symptoms = []

        critical_modules = [
            ("py_clob_client", "Polymarket trading"),
            ("requests", "HTTP requests"),
            ("dotenv", "Environment loading"),
        ]

        for module, purpose in critical_modules:
            try:
                __import__(module)
            except ImportError:
                symptoms.append(Symptom(
                    component=f"python_{module}",
                    severity="warning",
                    symptom=f"Module not installed: {module}",
                    details=f"Required for: {purpose}"
                ))

        return symptoms

    def check_env_files(self) -> List[Symptom]:
        """Check environment file health."""
        symptoms = []

        env_files = [
            (".env", ["OPENAI_API_KEY"]),
            (".env.polymarket", ["POLYMARKET_PRIVATE_KEY", "POLYMARKET_FUNDER_ADDRESS"]),
        ]

        for filename, required_keys in env_files:
            filepath = BASE_DIR / filename
            if not filepath.exists():
                symptoms.append(Symptom(
                    component="env",
                    severity="warning",
                    symptom=f"Missing env file: {filename}",
                ))
            else:
                content = filepath.read_text()
                for key in required_keys:
                    if key not in content:
                        symptoms.append(Symptom(
                            component="env",
                            severity="warning",
                            symptom=f"Missing key in {filename}",
                            details=f"Key: {key}"
                        ))

        return symptoms

    # ═══════════════════════════════════════════════════════════
    # SENSITIVE DATA ACCESS - Privileged health checks
    # ═══════════════════════════════════════════════════════════

    def check_wallet_balance(self) -> List[Symptom]:
        """Check actual wallet balance on Polygon."""
        symptoms = []

        try:
            from dotenv import load_dotenv
            load_dotenv(BASE_DIR / ".env.polymarket")

            wallet_address = os.environ.get("POLYMARKET_FUNDER_ADDRESS")
            if not wallet_address:
                symptoms.append(Symptom(
                    component="wallet",
                    severity="critical",
                    symptom="No wallet address configured",
                ))
                return symptoms

            # Check USDC balance via Polygon RPC
            import urllib.request
            import json as json_module

            rpc_url = "https://polygon-rpc.com"
            # USDC contract on Polygon
            usdc_contract = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

            # balanceOf(address) call
            data = {
                "jsonrpc": "2.0",
                "method": "eth_call",
                "params": [{
                    "to": usdc_contract,
                    "data": f"0x70a08231000000000000000000000000{wallet_address[2:]}"
                }, "latest"],
                "id": 1
            }

            req = urllib.request.Request(
                rpc_url,
                data=json_module.dumps(data).encode(),
                headers={"Content-Type": "application/json"}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json_module.loads(response.read())
                if "result" in result:
                    balance_wei = int(result["result"], 16)
                    balance_usdc = balance_wei / 1e6  # USDC has 6 decimals

                    # Store in sensitive data
                    self._sensitive_data["wallet_usdc"] = balance_usdc
                    self._sensitive_data["wallet_address"] = wallet_address

                    if balance_usdc < 1:
                        symptoms.append(Symptom(
                            component="wallet",
                            severity="critical",
                            symptom="Wallet nearly empty",
                            details=f"USDC: ${balance_usdc:.2f}"
                        ))
                    elif balance_usdc < 10:
                        symptoms.append(Symptom(
                            component="wallet",
                            severity="warning",
                            symptom="Low wallet balance",
                            details=f"USDC: ${balance_usdc:.2f}"
                        ))

        except Exception as e:
            symptoms.append(Symptom(
                component="wallet",
                severity="warning",
                symptom="Could not check wallet balance",
                details=str(e)[:100]
            ))

        return symptoms

    def check_polymarket_positions(self) -> List[Symptom]:
        """Check actual Polymarket positions and their value."""
        symptoms = []

        try:
            from autonomous.actuators import ActuatorHub
            hub = ActuatorHub()

            if not hub.polymarket.trader:
                symptoms.append(Symptom(
                    component="polymarket",
                    severity="warning",
                    symptom="Polymarket trader not initialized",
                ))
                return symptoms

            # Get positions
            positions = []
            try:
                # Check for gamma API or positions
                pm = hub.polymarket
                if hasattr(pm, 'get_positions'):
                    positions = pm.get_positions()
            except:
                pass

            # Get open orders
            orders = hub.polymarket.get_open_orders()

            # Get trades
            trades = hub.polymarket.get_trades()

            # Store sensitive data
            self._sensitive_data["polymarket"] = {
                "positions": len(positions),
                "open_orders": len(orders),
                "trades": len(trades),
                "recent_trades": trades[-5:] if trades else [],
            }

            # Calculate exposure
            total_exposure = sum(float(o.get("size", 0)) for o in orders)
            if total_exposure > 100:
                symptoms.append(Symptom(
                    component="polymarket",
                    severity="info",
                    symptom=f"High trading exposure",
                    details=f"Open orders: ${total_exposure:.2f}"
                ))

        except Exception as e:
            symptoms.append(Symptom(
                component="polymarket",
                severity="warning",
                symptom="Could not check Polymarket positions",
                details=str(e)[:100]
            ))

        return symptoms

    def check_api_credentials(self) -> List[Symptom]:
        """Validate API credentials work (without exposing them)."""
        symptoms = []

        # Check OpenAI
        try:
            from dotenv import load_dotenv
            load_dotenv(BASE_DIR / ".env")

            openai_key = os.environ.get("OPENAI_API_KEY", "")
            if openai_key:
                # Just validate format
                if not openai_key.startswith("sk-"):
                    symptoms.append(Symptom(
                        component="api_openai",
                        severity="warning",
                        symptom="OpenAI key format invalid",
                    ))
                else:
                    self._sensitive_data["openai_configured"] = True
            else:
                symptoms.append(Symptom(
                    component="api_openai",
                    severity="warning",
                    symptom="OpenAI API key not configured",
                ))

        except:
            pass

        # Check Telegram
        try:
            tg_env = Path("/root/hands-off/state/tg/bots/handsoff.env")
            if tg_env.exists():
                content = tg_env.read_text()
                if "BOT_TOKEN=" in content:
                    self._sensitive_data["telegram_configured"] = True
                else:
                    symptoms.append(Symptom(
                        component="api_telegram",
                        severity="warning",
                        symptom="Telegram bot token missing",
                    ))
            else:
                symptoms.append(Symptom(
                    component="api_telegram",
                    severity="warning",
                    symptom="Telegram config file not found",
                ))
        except:
            pass

        # Check Polymarket credentials
        try:
            from dotenv import load_dotenv
            load_dotenv(BASE_DIR / ".env.polymarket")

            pk = os.environ.get("POLYMARKET_PRIVATE_KEY", "")
            if pk and pk.startswith("0x") and len(pk) == 66:
                self._sensitive_data["polymarket_configured"] = True
            else:
                symptoms.append(Symptom(
                    component="api_polymarket",
                    severity="warning",
                    symptom="Polymarket private key format invalid",
                ))
        except:
            pass

        return symptoms

    def check_financial_runway(self) -> List[Symptom]:
        """Calculate financial runway based on burn rate."""
        symptoms = []

        try:
            # Get current balance
            wallet_balance = self._sensitive_data.get("wallet_usdc", 0)

            # Load finance hub data
            finance_file = BASE_DIR / "finance" / "finance_hub.json"
            if finance_file.exists():
                data = json.loads(finance_file.read_text())
                monthly_burn = data.get("monthly_burn", 0)
                income = data.get("income", {}).get("total", 0)

                net_burn = monthly_burn - income
                if net_burn > 0 and wallet_balance > 0:
                    runway_months = wallet_balance / net_burn
                    self._sensitive_data["runway_months"] = runway_months

                    if runway_months < 1:
                        symptoms.append(Symptom(
                            component="runway",
                            severity="critical",
                            symptom="Less than 1 month runway",
                            details=f"Runway: {runway_months:.1f} months"
                        ))
                    elif runway_months < 3:
                        symptoms.append(Symptom(
                            component="runway",
                            severity="warning",
                            symptom="Short runway",
                            details=f"Runway: {runway_months:.1f} months"
                        ))

                self._sensitive_data["monthly_burn"] = monthly_burn
                self._sensitive_data["income"] = income

        except Exception as e:
            pass

        return symptoms

    def check_database_integrity(self) -> List[Symptom]:
        """Check state file integrity and corruption."""
        symptoms = []

        critical_state_files = [
            "evolution_state.json",
            "reality_feedback.json",
            "doctor_state.json",
            "endpoint_registry.json",
        ]

        for filename in critical_state_files:
            filepath = STATE_DIR / filename
            if filepath.exists():
                try:
                    content = filepath.read_text()
                    json.loads(content)  # Validate JSON
                except json.JSONDecodeError:
                    symptoms.append(Symptom(
                        component="database",
                        severity="critical",
                        symptom=f"Corrupted state file: {filename}",
                        details="Invalid JSON"
                    ))
                except Exception as e:
                    symptoms.append(Symptom(
                        component="database",
                        severity="warning",
                        symptom=f"Cannot read state file: {filename}",
                        details=str(e)[:50]
                    ))

        return symptoms

    def check_secret_exposure(self) -> List[Symptom]:
        """Check for accidentally exposed secrets in logs or state."""
        symptoms = []

        secret_patterns = [
            (r"sk-[a-zA-Z0-9]{20,}", "OpenAI key"),
            (r"0x[a-fA-F0-9]{64}", "Private key"),
            (r"ghp_[a-zA-Z0-9]{36}", "GitHub token"),
        ]

        import re

        # Check log files
        log_dir = Path("/var/log/hands-off")
        if log_dir.exists():
            for log_file in log_dir.glob("*.log"):
                try:
                    content = log_file.read_text()[-10000:]  # Last 10KB
                    for pattern, name in secret_patterns:
                        if re.search(pattern, content):
                            symptoms.append(Symptom(
                                component="security",
                                severity="critical",
                                symptom=f"Potential {name} exposure in logs",
                                details=f"File: {log_file.name}"
                            ))
                except:
                    pass

        # Check state files for secrets
        for state_file in STATE_DIR.glob("*.json"):
            try:
                content = state_file.read_text()
                for pattern, name in secret_patterns:
                    if re.search(pattern, content):
                        symptoms.append(Symptom(
                            component="security",
                            severity="critical",
                            symptom=f"Potential {name} in state file",
                            details=f"File: {state_file.name}"
                        ))
            except:
                pass

        return symptoms

    def get_sensitive_summary(self) -> Dict:
        """Get summary of sensitive data collected during examination."""
        return {
            "wallet_usdc": self._sensitive_data.get("wallet_usdc", "unknown"),
            "wallet_address": self._sensitive_data.get("wallet_address", "unknown")[:10] + "..." if self._sensitive_data.get("wallet_address") else "unknown",
            "polymarket": self._sensitive_data.get("polymarket", {}),
            "runway_months": self._sensitive_data.get("runway_months", "unknown"),
            "monthly_burn": self._sensitive_data.get("monthly_burn", 0),
            "income": self._sensitive_data.get("income", 0),
            "credentials": {
                "openai": self._sensitive_data.get("openai_configured", False),
                "telegram": self._sensitive_data.get("telegram_configured", False),
                "polymarket": self._sensitive_data.get("polymarket_configured", False),
            },
        }

    def check_evolution_progress(self) -> List[Symptom]:
        """Check if evolution engine is making progress."""
        symptoms = []

        evolution_file = STATE_DIR / "evolution_state.json"
        if evolution_file.exists():
            try:
                data = json.loads(evolution_file.read_text())
                cycles = data.get("cycles", 0)
                actions = data.get("actions_taken", 0)

                if cycles > 0:
                    success_rate = actions / cycles
                    if success_rate < 0.5:
                        symptoms.append(Symptom(
                            component="evolution",
                            severity="warning",
                            symptom="Low evolution success rate",
                            details=f"{success_rate*100:.0f}% actions succeed"
                        ))

                last_action = data.get("last_action", {})
                if last_action:
                    last_time = last_action.get("timestamp", "")
                    if last_time:
                        try:
                            last_dt = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
                            age_hours = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
                            if age_hours > 2:
                                symptoms.append(Symptom(
                                    component="evolution",
                                    severity="warning",
                                    symptom="Evolution engine stale",
                                    details=f"Last action: {age_hours:.1f} hours ago"
                                ))
                        except:
                            pass

            except:
                pass

        return symptoms

    def check_trading_positions(self) -> List[Symptom]:
        """Check trading position health."""
        symptoms = []

        try:
            from autonomous.actuators import ActuatorHub
            hub = ActuatorHub()

            if hub.polymarket.trader:
                orders = hub.polymarket.get_open_orders()
                if len(orders) > 20:
                    symptoms.append(Symptom(
                        component="trading",
                        severity="info",
                        symptom=f"Many open orders: {len(orders)}",
                        details="Consider consolidating"
                    ))

        except:
            pass

        return symptoms

    def check_outreach_progress(self) -> List[Symptom]:
        """Check outreach effectiveness."""
        symptoms = []

        pursuit_file = STATE_DIR / "active_pursuit.json"
        if pursuit_file.exists():
            try:
                data = json.loads(pursuit_file.read_text())
                total = data.get("total_actions", 0)
                income = data.get("income_generated", 0)
                outreach = data.get("outreach_sent", 0)

                if outreach > 50 and income == 0:
                    symptoms.append(Symptom(
                        component="outreach",
                        severity="warning",
                        symptom="Outreach not converting",
                        details=f"{outreach} sent, $0 income"
                    ))

            except:
                pass

        return symptoms

    def full_examination(self) -> List[Symptom]:
        """Run all checks and collect symptoms."""
        print("\n🩺 SYSTEM DOCTOR - Full Examination")
        print("=" * 50)

        all_symptoms = []

        checks = [
            # Core System
            ("Processes", self.check_processes),
            ("State Files", self.check_state_files),
            ("Actuators", self.check_actuators),
            # Business Health
            ("Finances", self.check_finances),
            ("Outreach Progress", self.check_outreach_progress),
            ("Evolution Progress", self.check_evolution_progress),
            # Infrastructure
            ("Disk Space", self.check_disk_space),
            ("Memory", self.check_memory),
            ("Network", self.check_network),
            # Operations
            ("Endpoints", self.check_endpoints),
            ("Cron Jobs", self.check_cron_jobs),
            ("Log Files", self.check_log_files),
            # Development
            ("Git Status", self.check_git_status),
            ("Python Imports", self.check_python_imports),
            ("Env Files", self.check_env_files),
            # Trading
            ("Trading Positions", self.check_trading_positions),
            # Sensitive Data Access (privileged)
            ("Wallet Balance", self.check_wallet_balance),
            ("Polymarket Positions", self.check_polymarket_positions),
            ("API Credentials", self.check_api_credentials),
            ("Financial Runway", self.check_financial_runway),
            ("Database Integrity", self.check_database_integrity),
            ("Secret Exposure", self.check_secret_exposure),
        ]

        for name, check_fn in checks:
            print(f"\n  Checking {name}...")
            symptoms = check_fn()
            all_symptoms.extend(symptoms)

            for s in symptoms:
                icon = "🔴" if s.severity == "critical" else "🟡" if s.severity == "warning" else "🔵"
                print(f"    {icon} {s.symptom}")

        self.symptoms = all_symptoms
        self.state["examinations"] += 1
        self.state["last_exam"] = datetime.now(timezone.utc).isoformat()
        self.state["issues_found"] += len(all_symptoms)
        self._save_state()

        print(f"\n  Total symptoms: {len(all_symptoms)}")
        return all_symptoms

    # ═══════════════════════════════════════════════════════════
    # DIAGNOSIS - Identify root causes
    # ═══════════════════════════════════════════════════════════

    def diagnose(self) -> List[Diagnosis]:
        """Analyze symptoms and identify root causes."""
        if not self.symptoms:
            self.full_examination()

        diagnoses = []

        # Group symptoms by component
        by_component = {}
        for s in self.symptoms:
            base = s.component.split("_")[0]
            if base not in by_component:
                by_component[base] = []
            by_component[base].append(s)

        # Financial diagnosis
        financial = [s for s in self.symptoms if s.component in ("finance", "income")]
        if financial:
            diagnoses.append(Diagnosis(
                symptoms=financial,
                root_cause="No revenue generation - system not converting to income",
                affected_systems=["outreach", "conversion", "trading"],
                priority=1
            ))

        # Process diagnosis
        process_issues = [s for s in self.symptoms if "process" in s.symptom.lower()]
        if process_issues:
            diagnoses.append(Diagnosis(
                symptoms=process_issues,
                root_cause="Critical processes not running",
                affected_systems=[s.component for s in process_issues],
                priority=2
            ))

        # Actuator diagnosis
        actuator_issues = [s for s in self.symptoms if s.component in ("telegram", "polymarket", "actuators")]
        if actuator_issues:
            diagnoses.append(Diagnosis(
                symptoms=actuator_issues,
                root_cause="Real-world action capability impaired",
                affected_systems=["actuators", "evolution_engine"],
                priority=2
            ))

        # Infrastructure diagnosis
        infra_issues = [s for s in self.symptoms if s.component == "disk"]
        if infra_issues:
            diagnoses.append(Diagnosis(
                symptoms=infra_issues,
                root_cause="Infrastructure resource constraints",
                affected_systems=["all"],
                priority=1
            ))

        self.diagnoses = sorted(diagnoses, key=lambda d: d.priority)

        for d in self.diagnoses:
            self._log_diagnosis(d)

        return self.diagnoses

    # ═══════════════════════════════════════════════════════════
    # TREATMENT - Prescribe and apply fixes
    # ═══════════════════════════════════════════════════════════

    def prescribe(self) -> List[Treatment]:
        """Generate treatments for diagnoses."""
        if not self.diagnoses:
            self.diagnose()

        treatments = []

        for diagnosis in self.diagnoses:
            if "revenue" in diagnosis.root_cause.lower() or "income" in diagnosis.root_cause.lower():
                treatments.append(Treatment(
                    diagnosis=diagnosis.root_cause,
                    treatment="Focus evolution engine on income-generating actions",
                    manual_steps=[
                        "Review conversion optimizer experiments",
                        "Check outreach targets",
                        "Verify trading signals",
                    ]
                ))

            elif "process" in diagnosis.root_cause.lower():
                for s in diagnosis.symptoms:
                    treatments.append(Treatment(
                        diagnosis=diagnosis.root_cause,
                        treatment=f"Restart {s.component} process",
                        command=f"PYTHONPATH=/root/hands-off-engine python3 /root/hands-off-engine/scripts/{s.component}.py &"
                    ))

            elif "actuator" in diagnosis.root_cause.lower():
                treatments.append(Treatment(
                    diagnosis=diagnosis.root_cause,
                    treatment="Verify actuator credentials and connectivity",
                    command="PYTHONPATH=/root/hands-off-engine python3 /root/hands-off-engine/autonomous/actuators.py"
                ))

            elif "disk" in diagnosis.root_cause.lower():
                treatments.append(Treatment(
                    diagnosis=diagnosis.root_cause,
                    treatment="Clean up old logs and state files",
                    command="find /root/hands-off-engine/logs -name '*.log' -mtime +7 -delete"
                ))

        self.treatments = treatments
        return treatments

    def apply_treatment(self, treatment: Treatment, dry_run: bool = True) -> bool:
        """Apply a treatment."""
        print(f"\n💊 Applying treatment: {treatment.treatment}")

        if treatment.command:
            if dry_run:
                print(f"   [DRY RUN] Would execute: {treatment.command}")
                return True
            else:
                try:
                    result = subprocess.run(
                        treatment.command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=60,
                        cwd=str(BASE_DIR)
                    )
                    treatment.executed = True
                    treatment.success = result.returncode == 0
                    self._log_treatment(treatment)
                    self.state["treatments_applied"] += 1
                    self._save_state()
                    print(f"   {'✅ Success' if treatment.success else '❌ Failed'}")
                    return treatment.success
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    return False

        if treatment.manual_steps:
            print("   Manual steps required:")
            for step in treatment.manual_steps:
                print(f"     • {step}")

        return True

    def report(self) -> str:
        """Generate a full medical report."""
        if not self.symptoms:
            self.full_examination()
        if not self.diagnoses:
            self.diagnose()
        if not self.treatments:
            self.prescribe()

        report = []
        report.append("\n" + "=" * 60)
        report.append("🩺 SYSTEM MEDICAL REPORT")
        report.append("=" * 60)
        report.append(f"Examination: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

        # Vital signs
        report.append("\n📊 VITAL SIGNS")
        report.append("-" * 40)
        critical = len([s for s in self.symptoms if s.severity == "critical"])
        warnings = len([s for s in self.symptoms if s.severity == "warning"])
        report.append(f"  Critical issues: {critical}")
        report.append(f"  Warnings: {warnings}")

        # Sensitive Data Summary
        if self._sensitive_data:
            report.append("\n🔐 SENSITIVE DATA (Privileged Access)")
            report.append("-" * 40)
            sensitive = self.get_sensitive_summary()
            if sensitive.get("wallet_usdc") != "unknown":
                report.append(f"  Wallet USDC: ${sensitive['wallet_usdc']:.2f}" if isinstance(sensitive['wallet_usdc'], (int, float)) else f"  Wallet USDC: {sensitive['wallet_usdc']}")
            if sensitive.get("wallet_address"):
                report.append(f"  Wallet: {sensitive['wallet_address']}")
            if sensitive.get("runway_months") != "unknown":
                report.append(f"  Runway: {sensitive['runway_months']:.1f} months" if isinstance(sensitive['runway_months'], (int, float)) else f"  Runway: {sensitive['runway_months']}")
            report.append(f"  Monthly Burn: ${sensitive.get('monthly_burn', 0)}")
            report.append(f"  Income: ${sensitive.get('income', 0)}")
            creds = sensitive.get("credentials", {})
            report.append(f"  Credentials: OpenAI={'✓' if creds.get('openai') else '✗'} Telegram={'✓' if creds.get('telegram') else '✗'} Polymarket={'✓' if creds.get('polymarket') else '✗'}")
            pm = sensitive.get("polymarket", {})
            if pm:
                report.append(f"  Polymarket: {pm.get('positions', 0)} positions, {pm.get('open_orders', 0)} orders, {pm.get('trades', 0)} trades")

        # Symptoms
        if self.symptoms:
            report.append("\n🔍 SYMPTOMS")
            report.append("-" * 40)
            for s in self.symptoms:
                icon = "🔴" if s.severity == "critical" else "🟡" if s.severity == "warning" else "🔵"
                report.append(f"  {icon} [{s.component}] {s.symptom}")
                if s.details:
                    report.append(f"     └─ {s.details}")

        # Diagnoses
        if self.diagnoses:
            report.append("\n🔬 DIAGNOSES")
            report.append("-" * 40)
            for i, d in enumerate(self.diagnoses, 1):
                report.append(f"  {i}. {d.root_cause}")
                report.append(f"     Affects: {', '.join(d.affected_systems)}")
                report.append(f"     Priority: {'HIGH' if d.priority == 1 else 'MEDIUM' if d.priority == 2 else 'LOW'}")

        # Treatments
        if self.treatments:
            report.append("\n💊 PRESCRIBED TREATMENTS")
            report.append("-" * 40)
            for t in self.treatments:
                report.append(f"  • {t.treatment}")
                if t.command:
                    report.append(f"    Command: {t.command[:60]}...")

        report.append("\n" + "=" * 60)

        return "\n".join(report)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="🩺 System Doctor")
    parser.add_argument("command", choices=["examine", "diagnose", "prescribe", "report", "treat"])
    parser.add_argument("--apply", action="store_true", help="Actually apply treatments (not dry run)")

    args = parser.parse_args()

    doctor = SystemDoctor()

    if args.command == "examine":
        doctor.full_examination()

    elif args.command == "diagnose":
        doctor.full_examination()
        diagnoses = doctor.diagnose()
        print("\n🔬 DIAGNOSES:")
        for d in diagnoses:
            print(f"  Priority {d.priority}: {d.root_cause}")

    elif args.command == "prescribe":
        doctor.full_examination()
        doctor.diagnose()
        treatments = doctor.prescribe()
        print("\n💊 TREATMENTS:")
        for t in treatments:
            print(f"  • {t.treatment}")

    elif args.command == "report":
        print(doctor.report())

    elif args.command == "treat":
        doctor.full_examination()
        doctor.diagnose()
        doctor.prescribe()
        print("\n💉 APPLYING TREATMENTS...")
        for t in doctor.treatments:
            doctor.apply_treatment(t, dry_run=not args.apply)


if __name__ == "__main__":
    main()
