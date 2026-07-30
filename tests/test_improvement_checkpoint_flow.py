
from ai.factory.runtime import FactoryRuntime


def test_improvement_cycle_to_checkpoint_flow():
    runtime = FactoryRuntime()

    runtime.run_improvement_cycle(
        {
            "success": True,
            "impact": 0.5,
        }
    )

    checkpoint = runtime.run_checkpoint_cycle()

    assert isinstance(checkpoint, dict)
    assert "action" in checkpoint


def test_checkpoint_audit_component_available():
    runtime = FactoryRuntime()

    assert hasattr(
        runtime,
        "improvement_audit",
    )
