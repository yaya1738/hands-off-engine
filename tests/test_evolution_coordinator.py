from ai.factory.evolution_coordinator import (
    FactoryEvolutionCoordinator,
)


class FakeOptimizer:
    def optimize(self, metrics):
        return {
            "action": "OPTIMIZE",
        }


def test_evaluate():
    coordinator = FactoryEvolutionCoordinator()

    result = coordinator.evaluate(
        {
            "success_rate": 1,
        }
    )

    assert result["metrics"]["success_rate"] == 1


def test_upgrade():
    coordinator = FactoryEvolutionCoordinator(
        optimizer=FakeOptimizer()
    )

    result = coordinator.upgrade(
        {
            "success_rate": 0.5,
        }
    )

    assert result["action"] == "OPTIMIZE"


def test_evolve():
    coordinator = FactoryEvolutionCoordinator(
        optimizer=FakeOptimizer()
    )

    result = coordinator.evolve(
        {
            "success_rate": 0.5,
        }
    )

    assert result["upgrade"]["action"] == "OPTIMIZE"


def test_history():
    coordinator = FactoryEvolutionCoordinator()

    coordinator.evaluate({})

    assert len(coordinator.history()) == 1
