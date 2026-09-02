from pathlib import Path


TARGET = Path("factory_milestone_gate.py")


def test_milestone_gate_has_no_direct_execution_or_mutation():
    source = TARGET.read_text()
    forbidden = (
        "import subprocess",
        "subprocess.",
        "git add",
        "git commit",
        "os.system",
        "os.popen",
        "os.remove",
        "shutil.move",
    )
    assert not any(token in source for token in forbidden)
    assert "FactoryAuthorityGateway" in source


def test_milestone_gate_is_verification_only():
    namespace = {}
    exec(compile(TARGET.read_text(), str(TARGET), "exec"), namespace)
    assert namespace["MILESTONE"] == "factory-runtime-reporting-restored-20260717"
    assert callable(namespace["check_files"])
    assert callable(namespace["check_markers"])
