import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    "factory_self_repair_pipeline.py",
    "factory_builder_capability_discovery.py",
    "factory_constructor_repair_assistant.py",
    "autonomous/singularity_trigger.py",
    "autonomous/time_collapse.py",
    "scripts/realtime_coordination_service.py",
]


def _source(path):
    return (ROOT / path).read_text()


def test_legacy_execution_targets_have_no_process_or_shell_authority():
    for rel in TARGETS:
        tree = ast.parse(_source(rel))
        imports = [n.name for n in ast.walk(tree) if isinstance(n, ast.Import)]
        assert "subprocess" not in imports, rel
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {"system", "popen", "Popen", "check_call", "check_output"}, rel


def test_self_repair_and_discovery_fail_closed():
    ns = {"__file__": str(ROOT / "factory_self_repair_pipeline.py")}
    exec(compile(_source("factory_self_repair_pipeline.py"), "factory_self_repair_pipeline.py", "exec"), ns)
    assert ns["run_tool"](["python", "tool"])["authority_required"] is True
    assert ns["run_pipeline"]("goal")["disabled"] is True

    ns = {"__file__": str(ROOT / "factory_builder_capability_discovery.py")}
    exec(compile(_source("factory_builder_capability_discovery.py"), "factory_builder_capability_discovery.py", "exec"), ns)
    assert ns["run"]()["disabled"] is True


def test_constructor_repair_singularity_and_time_collapse_are_disabled():
    ns = {"__file__": str(ROOT / "factory_constructor_repair_assistant.py")}
    exec(compile(_source("factory_constructor_repair_assistant.py"), "factory_constructor_repair_assistant.py", "exec"), ns)
    assert ns["main"]() is False

    ns = {"__file__": str(ROOT / "autonomous/singularity_trigger.py")}
    exec(compile(_source("autonomous/singularity_trigger.py"), "singularity_trigger.py", "exec"), ns)
    assert ns["execute_singularity"]()[0].startswith("[FACTORY-AUTHORITY]")
    assert ns["save_state"]({}) is False

    ns = {"__file__": str(ROOT / "autonomous/time_collapse.py")}
    exec(compile(_source("autonomous/time_collapse.py"), "time_collapse.py", "exec"), ns)
    assert ns["collapse_timeline"]()["disabled"] is True


def test_coordination_webhook_fails_closed():
    ns = {"__file__": str(ROOT / "scripts/realtime_coordination_service.py")}
    exec(compile(_source("scripts/realtime_coordination_service.py"), "realtime_coordination_service.py", "exec"), ns)
    assert ns["CoordinationWebhook"].message_callback is None
