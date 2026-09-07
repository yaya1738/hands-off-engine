from pathlib import Path

def test_autonomous_control_plane_has_no_regular_chatgpt_ui_dependency(monkeypatch):
    import sys
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo))
    monkeypatch.setitem(sys.modules, "ai_nexus.provider_chatgpt", None)
    from tools.autonomy_liveness_supervisor import run_once
    assert callable(run_once)
