from ai.factory.integration_adapter_designer import (
    FactoryIntegrationAdapterDesigner,
)


def test_adapter_design():

    designer = FactoryIntegrationAdapterDesigner()

    result = designer.design_adapter(
        "evolution_cycle_adapter",
        "connect evolution monitoring to improvement cycles",
        [
            "receive opportunities",
            "translate requests",
            "track outcomes",
        ],
        [
            "evolution_monitor",
            "improvement_cycle",
        ],
    )

    assert result["designed"] is True


def test_validation():

    designer = FactoryIntegrationAdapterDesigner()

    designer.design_adapter(
        "test_adapter",
        "testing",
        [
            "connect",
        ],
    )

    assert designer.validate_adapter(
        "test_adapter"
    )["valid"] is True
