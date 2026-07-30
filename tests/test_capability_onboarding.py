from ai.factory.capability_onboarding import (
    FactoryCapabilityOnboarding,
)


def test_onboard_capability():

    system = FactoryCapabilityOnboarding()

    result = system.onboard(
        "workflow_orchestrator",
        "FactoryRuntime",
        [
            "register_step",
            "execute_workflow",
        ],
    )

    assert result["registered"] is True


def test_verify_capability():

    system = FactoryCapabilityOnboarding()

    system.onboard(
        "test",
        "runtime",
        ["step"],
    )

    result = system.verify("test")

    assert result["verified"] is True
