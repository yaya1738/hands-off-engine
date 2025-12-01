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

    def full_examination(self) -> List[Symptom]:
        """Run all checks and collect symptoms."""
        print("\n🩺 SYSTEM DOCTOR - Full Examination")
        print("=" * 50)

        all_symptoms = []

        checks = [
            ("Processes", self.check_processes),
            ("State Files", self.check_state_files),
            ("Actuators", self.check_actuators),
            ("Finances", self.check_finances),
            ("Endpoints", self.check_endpoints),
            ("Disk Space", self.check_disk_space),
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
