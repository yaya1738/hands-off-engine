from pathlib import Path


def test_autonomous_control_plane_has_no_regular_chatgpt_ui_dependency(monkeypatch, tmp_path):
    """The autonomous ingress/control path must remain importable without ChatGPT."""
    import sys

    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo))
    monkeypatch.setitem(sys.modules, "ai_nexus.provider_chatgpt", None)

    from tools.autonomy_liveness_supervisor import run_once

    assert callable(run_once)


def test_ai_runner_construction_is_independent_of_chatgpt(monkeypatch, tmp_path):
    import sys

    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo))
    monkeypatch.setitem(sys.modules, "ai_nexus.provider_chatgpt", None)

    from ai_nexus.runner import AIRunner

    runner = AIRunner(str(tmp_path / "tasks"), str(tmp_path / "output"))
    assert runner.providers == {}
