import ast
from pathlib import Path

import factory_artifact_registry
import factory_construction_organ_resolver
import factory_phase_transition_gate
from ai.factory.checkpoint_manager import FactoryCheckpointManager


FILES = [
    "factory_phase_transition_gate.py",
    "factory_artifact_registry.py",
    "factory_construction_organ_resolver.py",
    "ai/factory/checkpoint_manager.py",
]


def _executable_calls(path):
    tree = ast.parse(Path(path).read_text())
    calls = []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(ast.unparse(node))
        elif isinstance(node, ast.Call):
            calls.append(ast.unparse(node))
    return imports, calls


def test_remaining_boundaries_have_no_subprocess_import_or_call():
    for path in FILES:
        imports, calls = _executable_calls(path)
        assert not any("subprocess" in item for item in imports), path
        assert not any("subprocess." in item or ".Popen(" in item for item in calls), path


def test_phase_gate_fails_closed():
    assert "FACTORY-AUTHORITY" in factory_phase_transition_gate.run(["git", "status"])
    assert factory_phase_transition_gate.main() == 1


def test_artifact_registry_fails_closed_without_persistence():
    result = factory_artifact_registry.build_registry()
    assert result["authority_required"] is True
    assert "FACTORY-AUTHORITY" in result["message"]


def test_construction_resolver_does_not_launch_analyzer():
    result = factory_construction_organ_resolver.get_capability_report()
    assert result["authority_required"] is True
    assert result["capabilities"] == {}


def test_checkpoint_manager_fails_closed_for_workspace_inspection():
    result = FactoryCheckpointManager().evaluate()
    assert result["authority_required"] is True
    assert result["authority"] == "FactoryAuthorityGateway"
    assert result["action"] == "SUBMIT_WORKSPACE_INSPECTION"
