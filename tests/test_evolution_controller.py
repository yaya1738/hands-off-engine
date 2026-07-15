from ai.factory.evolution_controller import (
    FactoryEvolutionController,
)


def build():
    return FactoryEvolutionController()


def test_evaluate():
    controller = build()

    result = controller.evaluate_change(
        {
            "type": "OPTIMIZATION",
        }
    )

    assert result["evaluated"] is True


def test_approve():
    controller = build()

    result = controller.approve(
        {}
    )

    assert result["approved"] is True


def test_apply():
    controller = build()

    result = controller.apply(
        {}
    )

    assert result["status"] == "APPLIED"
    assert result["version"] == 1


def test_rollback():
    controller = build()

    controller.apply({})

    result = controller.rollback()

    assert result["status"] == "ROLLED_BACK"


def test_history():
    controller = build()

    controller.evaluate_change({})

    assert len(controller.history()) == 1
