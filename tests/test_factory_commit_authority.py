from pathlib import Path
import ast

SOURCE_PATH = Path("tools/factory_commit.py")
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def test_legacy_commit_has_no_subprocess_import():
    imports = {a.name for n in ast.walk(TREE) if isinstance(n, ast.Import) for a in n.names}
    assert "subprocess" not in imports


def test_legacy_commit_fails_closed():
    namespace = {"__name__": "factory_commit_test", "__file__": str(SOURCE_PATH.resolve())}
    exec(compile(SOURCE, str(SOURCE_PATH), "exec"), namespace)
    result = namespace["run"](["git", "commit", "-m", "test"])
    assert result["disabled"] is True
    assert "FactoryAuthorityGateway" in result["error"]
    assert namespace["main"]()["next_step"] == "FactoryAuthorityGateway"
