from autonomous.system_doctor import SystemDoctor, Treatment
import autonomous.system_doctor as doctor_module


def test_apply_flag_cannot_execute_shell_treatment(monkeypatch):
    doctor = SystemDoctor.__new__(SystemDoctor)
    doctor.state = {"treatments_applied": 0}
    treatment = Treatment(
        diagnosis="test",
        treatment="run a command",
        command="touch /tmp/system-doctor-must-not-run",
    )

    def forbidden_run(*args, **kwargs):
        raise AssertionError("SystemDoctor must not execute shell treatments")

    monkeypatch.setattr(doctor_module.subprocess, "run", forbidden_run)

    assert doctor.apply_treatment(treatment, dry_run=False) is False
    assert treatment.executed is False
    assert treatment.success is False
    assert doctor.state["treatments_applied"] == 0


def test_dry_run_treatment_remains_non_executing(monkeypatch):
    doctor = SystemDoctor.__new__(SystemDoctor)
    doctor.state = {"treatments_applied": 0}
    treatment = Treatment(
        diagnosis="test",
        treatment="preview a command",
        command="echo preview-only",
    )

    def forbidden_run(*args, **kwargs):
        raise AssertionError("Dry run must not execute")

    monkeypatch.setattr(doctor_module.subprocess, "run", forbidden_run)

    assert doctor.apply_treatment(treatment, dry_run=True) is True
    assert treatment.executed is False
    assert doctor.state["treatments_applied"] == 0
