from ai.factory.local_agent_executor import FactoryLocalAgentExecutor


def test_unavailable_agent_is_explicit_and_bounded():
    result = FactoryLocalAgentExecutor().execute(
        {"objective": "test", "allowed_paths": ["tools/x.py"]}
    )
    assert result["status"] == "AGENT_UNAVAILABLE"
    assert result["allowed_paths"] == ["tools/x.py"]


def test_agent_receives_authorization_envelope():
    seen = {}

    def agent(envelope):
        seen.update(envelope)
        return {"status": "executed"}

    result = FactoryLocalAgentExecutor(agent).execute(
        {"objective": "test"}, workspace="/tmp/factory", allowed_paths=["tools/x.py"]
    )
    assert seen["workspace"] == "/tmp/factory"
    assert seen["allowed_paths"] == ["tools/x.py"]
    assert result["status"] == "executed"


def test_agent_output_must_be_structured():
    try:
        FactoryLocalAgentExecutor(lambda _: "unsafe").execute({"objective": "test"})
    except TypeError as exc:
        assert "dictionary" in str(exc)
    else:
        raise AssertionError("expected TypeError")
