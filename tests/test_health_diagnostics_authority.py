import ast
from pathlib import Path


SOURCE = Path("autonomous/health_diagnostics.py").read_text()
TREE = ast.parse(SOURCE)


def test_health_diagnostics_has_no_process_execution():
    forbidden = {"subprocess", "os.system", "os.popen"}
    names = set()
    for node in ast.walk(TREE):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                names.add(node.func.attr)
    assert "subprocess" not in names
    assert "system" not in names
    assert "popen" not in names


def test_apply_treatment_fails_closed_without_dry_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import importlib.util
    spec = importlib.util.spec_from_file_location("health_diagnostics", Path.cwd().parent / "missing.py")
    # Load the repository module directly so the test remains independent of package setup.
    source = SOURCE
    namespace = {"__name__": "health_diagnostics_test"}
    exec(compile(source, "autonomous/health_diagnostics.py", "exec"), namespace)
    doctor = namespace["HealthDiagnostics"]()
    treatment = namespace["Treatment"]("test", "test remediation", command="rm -rf /")
    assert doctor.apply_treatment(treatment, dry_run=False) is False
    assert treatment.executed is False
    assert treatment.success is False
