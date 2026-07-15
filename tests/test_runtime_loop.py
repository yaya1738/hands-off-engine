from ai.factory.runtime_loop import (
    FactoryRuntimeLoop,
)


def build():
    return FactoryRuntimeLoop()


def test_start_cycle():
    runtime = build()

    result = runtime.start_cycle(
        {}
    )

    assert result["started"] is True


def test_run_cycle():
    runtime = build()

    result = runtime.run_cycle(
        {}
    )

    assert result["completed"] is True


def test_pause_cycle():
    runtime = build()

    result = runtime.pause_cycle()

    assert result["paused"] is True


def test_resume_cycle():
    runtime = build()

    result = runtime.resume_cycle()

    assert result["resumed"] is True


def test_history():
    runtime = build()

    runtime.start_cycle({})

    assert len(runtime.history()) == 1
