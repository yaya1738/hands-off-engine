from ai.factory.runtime import FactoryRuntime


def build():
    return FactoryRuntime()


def test_execute_pipeline():
    runtime = build()

    result = runtime.execute(
        {
            "task": "test",
        }
    )

    assert result["success"] is True
    assert "planning" in result["steps_completed"]
    assert "execution" in result["steps_completed"]
    assert "learning" in result["steps_completed"]


def test_history():
    runtime = build()

    runtime.execute(
        {
            "task": "test",
        }
    )

    assert len(runtime.history()) == 1
