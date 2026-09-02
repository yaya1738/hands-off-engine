import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _source(path):
    return path.read_text()


def test_system_dashboard_has_no_process_execution():
    source = _source(ROOT / "autonomous/system_dashboard.py")
    tree = ast.parse(source)
    assert "subprocess" not in source
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in {"system", "popen"} for n in ast.walk(tree))


def test_meta_metrics_has_no_process_execution():
    source = _source(ROOT / "scripts/meta_metrics.py")
    tree = ast.parse(source)
    assert "subprocess" not in source
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in {"system", "popen"} for n in ast.walk(tree))


def test_dashboard_cron_path_fails_closed():
    namespace = {"__file__": str(ROOT / "autonomous/system_dashboard.py")}
    exec(compile(_source(ROOT / "autonomous/system_dashboard.py"), str(ROOT / "autonomous/system_dashboard.py"), "exec"), namespace)
    result = namespace["get_cron_status"]()
    assert result["total_jobs"] == "unknown"
    assert "FactoryAuthorityGateway" in result["error"]


def test_meta_metrics_history_fails_closed():
    namespace = {"__file__": str(ROOT / "scripts/meta_metrics.py")}
    exec(compile(_source(ROOT / "scripts/meta_metrics.py"), str(ROOT / "scripts/meta_metrics.py"), "exec"), namespace)
    assert namespace["get_recent_commits"]() == []
