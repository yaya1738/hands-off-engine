from ai.factory.control_plane import (
    FactoryControlPlane,
)


class FakeRuntime:
    def run_once(self, metrics):
        return {
            "cycle": 1,
        }


class FakeState:
    def checkpoint(self, state):
        return {
            "saved": True,
        }


def test_start():
    plane = FactoryControlPlane()

    result = plane.start()

    assert result["status"] == "STARTED"


def test_cycle():
    plane = FactoryControlPlane(
        runtime=FakeRuntime(),
        state=FakeState(),
    )

    result = plane.cycle(
        {
            "success_rate": 1,
        }
    )

    assert result["runtime"]["cycle"] == 1


def test_shutdown():
    plane = FactoryControlPlane()

    plane.start()

    result = plane.shutdown()

    assert result["status"] == "STOPPED"


def test_status():
    plane = FactoryControlPlane()

    plane.start()

    assert plane.status()["running"] is True
