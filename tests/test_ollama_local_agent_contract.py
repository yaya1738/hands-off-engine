import json

from ai.factory.ollama_local_agent import OllamaLocalAgent


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps({"response": "bounded result"}).encode()


def test_prompt_contains_authorization_boundary():
    prompt = OllamaLocalAgent._prompt(
        {"objective": "improve tests"}, ["tests/example.py"]
    )
    assert "improve tests" in prompt
    assert "tests/example.py" in prompt
    assert "authorized paths" in prompt.lower()


def test_adapter_returns_structured_agent_result(monkeypatch):
    def fake_urlopen(request, timeout):
        assert request.full_url.endswith("/api/generate")
        assert timeout == 300
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = OllamaLocalAgent()({
        "task": {"objective": "improve tests"},
        "workspace": "/tmp/factory",
        "allowed_paths": ["tests/example.py"],
    })
    assert result["status"] == "agent_completed"
    assert result["response"] == "bounded result"
