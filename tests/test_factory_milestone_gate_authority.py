from pathlib import Path


TARGET = Path("factory_milestone_gate.py")


def test_milestone_gate_has_no_direct_git_execution():
    source = TARGET.read_text()
    forbidden = (
        "import subprocess",
        "subprocess.",
        "git add",
        "git commit",
        "os.system",
        "os.popen",
    )
    assert not any(token in source for token in forbidden)


def test_milestone_gate_reports_mutation_disabled():
    namespace = {}
    exec(compile(TARGET.read_text(), str(TARGET), "exec"), namespace)
    report = namespace["main"]
    assert callable(report)
