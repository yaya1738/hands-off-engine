import ast
from pathlib import Path

import factory_completion_adapter_builder_request
import factory_completion_bridge_builder_request
import factory_introspection_capability_router
import factory_review_authority_builder_request
import factory_script_creator_capability_router


FILES = [
    "factory_review_authority_builder_request.py",
    "factory_script_creator_capability_router.py",
    "factory_completion_bridge_builder_request.py",
    "factory_completion_adapter_builder_request.py",
    "factory_introspection_capability_router.py",
]


def test_router_helpers_have_no_subprocess_imports_or_calls():
    for path in FILES:
        tree = ast.parse(Path(path).read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                assert "subprocess" not in ast.unparse(node), path
            if isinstance(node, ast.Call):
                text = ast.unparse(node)
                assert "subprocess." not in text, path
                assert ".Popen(" not in text, path


def test_builder_requests_fail_closed():
    for module in (
        factory_review_authority_builder_request,
        factory_completion_bridge_builder_request,
        factory_completion_adapter_builder_request,
    ):
        result = module.run()
        assert result["authority"] == "FactoryAuthorityGateway"
        assert result.get("construction_request", result.get("result", result.get("lifecycle")))["authority_required"] is True


def test_capability_routers_fail_closed():
    creator = factory_script_creator_capability_router.run_capability_analyzer()
    introspection = factory_introspection_capability_router.run_forensic_engine()
    assert creator["authority_required"] is True
    assert introspection["authority_required"] is True
