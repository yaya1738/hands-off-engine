from ai.factory.bootstrap import (
    FactoryBootstrap,
)


class FakeRuntime:
    def initialize(self):
        return {
            "status": "started",
        }


def test_create_factory():
    runtime = FakeRuntime()

    bootstrap = FactoryBootstrap(
        {
            "runtime_coordinator": runtime,
        }
    )

    result = bootstrap.create_factory()

    assert result is runtime


def test_start_factory():
    bootstrap = FactoryBootstrap(
        {
            "runtime_coordinator": FakeRuntime(),
        }
    )

    result = bootstrap.start_factory()

    assert result["status"] == "started"


def test_get_runtime():
    runtime = FakeRuntime()

    bootstrap = FactoryBootstrap(
        {
            "runtime_coordinator": runtime,
        }
    )

    bootstrap.create_factory()

    assert bootstrap.get_runtime() is runtime
