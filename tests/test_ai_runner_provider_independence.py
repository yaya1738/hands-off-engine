import importlib.util
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[1]
def test_runner_module_has_no_eager_chatgpt_import():
    source = (REPO_ROOT / "ai_nexus" / "runner.py").read_text(encoding="utf-8")
    assert "from ai_nexus.provider_chatgpt import" not in source
def test_runner_constructs_without_loading_any_provider(tmp_path):
    spec = importlib.util.spec_from_file_location("isolated_ai_runner", REPO_ROOT / "ai_nexus" / "runner.py")
    module = importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(module)
    runner = module.AIRunner(str(tmp_path / "tasks"), str(tmp_path / "output"))
    assert runner.providers == {}
