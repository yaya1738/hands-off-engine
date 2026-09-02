#!/usr/bin/env python3
"""Read-only system health diagnostics.

Legacy treatment execution is intentionally disabled.  Real remediation must
be submitted through FactoryAuthorityGateway so approval, policy, audit, and
execution controls remain centralized.
"""

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = BASE_DIR / "state"
DOCTOR_STATE = STATE_DIR / "doctor_state.json"
DIAGNOSIS_LOG = STATE_DIR / "diagnosis_log.jsonl"
TREATMENT_LOG = STATE_DIR / "treatment_log.jsonl"


@dataclass
class Symptom:
    component: str
    severity: str
    symptom: str
    details: str = ""


@dataclass
class Diagnosis:
    symptoms: List[Symptom]
    root_cause: str
    affected_systems: List[str]
    priority: int


@dataclass
class Treatment:
    diagnosis: str
    treatment: str
    command: str = ""
    manual_steps: List[str] = None
    executed: bool = False
    success: bool = False


class HealthDiagnostics:
    """Compatibility health doctor with no direct mutation authority."""

    def __init__(self):
        self.state = self._load_state()
        self.symptoms: List[Symptom] = []
        self.diagnoses: List[Diagnosis] = []
        self.treatments: List[Treatment] = []
        self._sensitive_data: Dict = {}

    def _load_state(self) -> Dict:
        if DOCTOR_STATE.exists():
            try:
                return json.loads(DOCTOR_STATE.read_text())
            except (OSError, json.JSONDecodeError):
                pass
        return {"examinations": 0, "issues_found": 0, "treatments_applied": 0, "last_exam": None}

    def _save_state(self):
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        DOCTOR_STATE.write_text(json.dumps(self.state, indent=2))

    def _log_diagnosis(self, diagnosis: Diagnosis):
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "root_cause": diagnosis.root_cause,
                 "priority": diagnosis.priority, "affected": diagnosis.affected_systems,
                 "symptoms": [asdict(s) for s in diagnosis.symptoms]}
        with DIAGNOSIS_LOG.open("a") as f:
            f.write(json.dumps(entry) + "\n")

    def _log_treatment(self, treatment: Treatment):
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "diagnosis": treatment.diagnosis,
                 "treatment": treatment.treatment, "executed": treatment.executed, "success": treatment.success}
        with TREATMENT_LOG.open("a") as f:
            f.write(json.dumps(entry) + "\n")

    def _state_check(self, name: str, filename: str, max_age: int) -> List[Symptom]:
        path = STATE_DIR / filename
        if not path.exists():
            return [Symptom(name, "warning", f"State file missing: {filename}")]
        age = datetime.now(timezone.utc).timestamp() - path.stat().st_mtime
        return [Symptom(name, "info", f"State file stale: {filename}", f"Age: {age/3600:.1f} hours")] if age > max_age else []

    def check_processes(self) -> List[Symptom]:
        """Process checks are unavailable without invoking an OS command."""
        return [Symptom("processes", "info", "Process health check requires privileged runtime telemetry",
                         "No subprocess execution is performed by this module")]

    def check_state_files(self):
        return (self._state_check("evolution_state", "evolution_state.json", 3600) +
                self._state_check("reality_feedback", "reality_feedback.json", 7200) +
                self._state_check("coordination", "coordination_state.json", 3600))

    def check_actuators(self) -> List[Symptom]:
        try:
            from autonomous.actuators import ActuatorHub
            status = ActuatorHub().status()
            result = []
            if not status.get("telegram", {}).get("configured"):
                result.append(Symptom("telegram", "warning", "Telegram actuator not configured"))
            if not status.get("polymarket", {}).get("healthy"):
                result.append(Symptom("polymarket", "warning", "Polymarket actuator unhealthy"))
            return result
        except Exception as e:
            return [Symptom("actuators", "critical", "Actuators module failed to load", str(e))]

    def check_finances(self):
        symptoms = []
        path = STATE_DIR / "reality_feedback.json"
        try:
            if path.exists():
                data = json.loads(path.read_text())
                balance, income = data.get("external_balance", 0), data.get("total_income", 0)
                if balance <= 0: symptoms.append(Symptom("finance", "critical", "Zero or negative balance", f"Balance: ${balance}"))
                elif balance < 10: symptoms.append(Symptom("finance", "warning", "Low balance", f"Balance: ${balance}"))
                if income == 0: symptoms.append(Symptom("income", "critical", "Zero income", "No revenue generated yet"))
        except (OSError, json.JSONDecodeError, TypeError):
            pass
        return symptoms

    def check_outreach_progress(self): return []
    def check_evolution_progress(self): return []
    def check_endpoints(self): return []
    def check_trading_positions(self): return []
    def check_disk_space(self):
        try:
            stat = os.statvfs("/")
            free_gb = stat.f_frsize * stat.f_bavail / (1024 ** 3)
            if free_gb < 1: return [Symptom("disk", "critical", "Disk space critical", f"Free: {free_gb:.1f} GB")]
            if free_gb < 5: return [Symptom("disk", "warning", "Disk space low", f"Free: {free_gb:.1f} GB")]
        except OSError: pass
        return []

    def check_memory(self): return []
    def check_network(self):
        return [Symptom("network", "info", "Network probe delegated to runtime telemetry",
                         "No direct ping subprocess is performed by this module")]
    def check_python_imports(self): return []
    def check_env_files(self): return []
    def check_financial_runway(self): return []
    def check_database_integrity(self): return []
    def check_secret_exposure(self): return []

    def check_wallet_balance(self):
        return [Symptom("wallet", "info", "Wallet balance probe delegated to privileged actuator telemetry",
                         "This diagnostic module does not acquire or retain wallet credentials")]

    def check_polymarket_positions(self):
        return [Symptom("polymarket", "info", "Position probe delegated to privileged actuator telemetry",
                         "This diagnostic module does not execute trading operations")]

    def check_api_credentials(self):
        return []

    def check_log_files(self):
        return []

    def check_git_status(self):
        return [Symptom("git", "info", "Git status probe delegated to runtime telemetry",
                         "No git subprocess execution is performed by this module")]

    def get_sensitive_summary(self) -> Dict:
        return {"wallet_usdc": "unknown", "wallet_address": "unknown", "polymarket": {},
                "runway_months": "unknown", "monthly_burn": 0, "income": 0,
                "credentials": {"openai": False, "telegram": False, "polymarket": False}}

    def full_examination(self) -> List[Symptom]:
        checks = [self.check_processes, self.check_state_files, self.check_actuators, self.check_finances,
                  self.check_outreach_progress, self.check_evolution_progress, self.check_disk_space,
                  self.check_memory, self.check_network, self.check_endpoints, self.check_cron_jobs,
                  self.check_log_files, self.check_git_status, self.check_python_imports, self.check_env_files,
                  self.check_trading_positions, self.check_wallet_balance, self.check_polymarket_positions,
                  self.check_api_credentials, self.check_financial_runway, self.check_database_integrity,
                  self.check_secret_exposure]
        self.symptoms = []
        for check in checks:
            try: self.symptoms.extend(check())
            except Exception: pass
        self.state["examinations"] = self.state.get("examinations", 0) + 1
        self.state["issues_found"] = self.state.get("issues_found", 0) + len(self.symptoms)
        self.state["last_exam"] = datetime.now(timezone.utc).isoformat()
        self._save_state()
        return self.symptoms

    def diagnose(self) -> List[Diagnosis]:
        if not self.symptoms: self.full_examination()
        diagnoses = []
        financial = [s for s in self.symptoms if s.component in ("finance", "income")]
        if financial:
            diagnoses.append(Diagnosis(financial, "No revenue generation - system not converting to income", ["outreach", "conversion", "trading"], 1))
        process_issues = [s for s in self.symptoms if s.component == "processes"]
        if process_issues:
            diagnoses.append(Diagnosis(process_issues, "Process health requires privileged runtime telemetry", ["processes"], 2))
        self.diagnoses = sorted(diagnoses, key=lambda d: d.priority)
        for d in self.diagnoses: self._log_diagnosis(d)
        return self.diagnoses

    def prescribe(self) -> List[Treatment]:
        if not self.diagnoses: self.diagnose()
        self.treatments = [Treatment(d.root_cause, "Submit remediation through FactoryAuthorityGateway", manual_steps=[
            "Create a bounded development/remediation request", "Obtain required approval", "Execute only through FactoryAuthorityGateway"
        ]) for d in self.diagnoses]
        return self.treatments

    def apply_treatment(self, treatment: Treatment, dry_run: bool = True) -> bool:
        """Never execute legacy treatments; route remediation through central authority."""
        treatment.executed = False
        treatment.success = False
        self._log_treatment(treatment)
        if dry_run:
            return True
        print("[FACTORY-AUTHORITY] Legacy HealthDiagnostics treatment execution is disabled; submit through FactoryAuthorityGateway.")
        return False

    def report(self) -> str:
        if not self.symptoms: self.full_examination()
        if not self.diagnoses: self.diagnose()
        if not self.treatments: self.prescribe()
        critical = sum(s.severity == "critical" for s in self.symptoms)
        warnings = sum(s.severity == "warning" for s in self.symptoms)
        return ("\n" + "=" * 60 + "\n🩺 SYSTEM MEDICAL REPORT\n" + "=" * 60 +
                f"\nExamination: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}" +
                f"\nCritical issues: {critical}\nWarnings: {warnings}\n" +
                "\n".join(f"  • {d.root_cause}" for d in self.diagnoses) + "\n")

    def check_cron_jobs(self):
        return [Symptom("scheduler", "info", "Cron inspection delegated to runtime telemetry",
                         "No crontab subprocess execution is performed by this module")]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Read-only System Doctor")
    parser.add_argument("command", choices=["examine", "diagnose", "prescribe", "report", "treat"])
    parser.add_argument("--apply", action="store_true", help="Deprecated: legacy treatment execution is disabled")
    args = parser.parse_args()
    doctor = HealthDiagnostics()
    if args.command == "examine": doctor.full_examination()
    elif args.command == "diagnose":
        for d in doctor.diagnose(): print(f"Priority {d.priority}: {d.root_cause}")
    elif args.command == "prescribe":
        for t in doctor.prescribe(): print(t.treatment)
    elif args.command == "report": print(doctor.report())
    elif args.command == "treat":
        doctor.full_examination(); doctor.diagnose(); doctor.prescribe()
        for t in doctor.treatments: doctor.apply_treatment(t, dry_run=not args.apply)


if __name__ == "__main__": main()
