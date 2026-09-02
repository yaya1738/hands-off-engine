import ast
import importlib
from pathlib import Path


FILES = [
    "factory_lifecycle_authority_probe.py",
    "factory_review_authority_resolver.py",
    "factory_workflow_executor.py",
    "tools/factory_forensics/local_agent.py",
]


def source(path):
    return (Path(__file__).resolve().parents[1] / path).read_text()


def test_legacy_probe_tools_have_no_direct_process_execution():
    for path in FILES:
        text = source(path)
        tree = ast.parse(text)
        assert "import subprocess" not in text
        assert "subprocess." not in text
        assert not any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"system", "popen"}
            for node in ast.walk(tree)
        )


def test_lifecycle_and_review_probes_fail_closed():
    lifecycle = importlib.import_module("factory_lifecycle_authority_probe")
    review = importlib.import_module("factory_review_authority_resolver")

    lifecycle_result = lifecycle.run()
    review_result = review.run()

    assert lifecycle_result["disabled"] is True
    assert lifecycle_result["next_step"] == "FactoryAuthorityGateway"
    assert "FactoryAuthorityGateway" in lifecycle_result["error"]
    assert review_result["disabled"] is True
    assert review_result["next_step"] == "FactoryAuthorityGateway"


def test_workflow_executor_planning_is_non_mutating():
    executor = importlib.import_module("factory_workflow_executor")
    result = executor.record_workflow_result("example", True)
    assert result["persisted"] is False
    assert result["authority_required"] is True
    assert result["next_step"] == "FactoryAuthorityGateway"


def test_local_agent_execution_fails_closed():
    agent = importlib.import_module("tools.factory_forensics.local_agent")
    task = agent.BoundedTask("allowed.py", frozenset({"allowed.py"}), "pass\n")

    try:
        agent.run_ollama("test-model", "probe")
    except RuntimeError as exc:
        assert "FactoryAuthorityGateway" in str(exc)
    else:
        raise AssertionError("legacy Ollama execution did not fail closed")

    try:
        agent.execute_bounded_edit("test-model", task)
    except RuntimeError as exc:
        assert "FactoryAuthorityGateway" in str(exc)
    else:
        raise AssertionError("legacy bounded edit did not fail closed")

    assert agent.prove_local_execution("test-model") is False
