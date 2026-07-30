from ai.factory.routine_creation_controller import (
    FactoryRoutineCreationController,
)


def test_submit_and_process():

    controller = FactoryRoutineCreationController()

    result = controller.submit_requirement(
        {
            "name": "protocol_bootstrap",
            "purpose": "initialize protocols",
            "steps": [
                "discover",
                "register",
                "verify",
            ],
            "description": "create protocol bootstrap",
        }
    )

    assert result["submitted"] is True

    processed = controller.process_queue()

    assert processed["processed"] == 1
    assert processed["results"][0]["created"] is True


def test_status():

    controller = FactoryRoutineCreationController()

    assert controller.status()["queued"] == 0
