from ai.factory.autonomous_state_memory import (
    FactoryAutonomousStateMemory,
)


def build():
    return FactoryAutonomousStateMemory()


def test_store_state():
    memory = build()

    result = memory.store_state(
        "mode",
        "ACTIVE",
    )

    assert result["stored"] is True


def test_retrieve_state():
    memory = build()

    memory.store_state(
        "mode",
        "ACTIVE",
    )

    result = memory.retrieve_state(
        "mode"
    )

    assert result["value"] == "ACTIVE"


def test_update_state():
    memory = build()

    result = memory.update_state(
        "mode",
        "OPTIMIZE",
    )

    assert result["updated"] is True


def test_query_history():
    memory = build()

    memory.store_state(
        "x",
        1,
    )

    assert len(memory.query_history()) == 1
