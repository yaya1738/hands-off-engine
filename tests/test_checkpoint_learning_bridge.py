
from ai.factory.runtime import FactoryRuntime


def test_checkpoint_can_feed_learning():
    runtime = FactoryRuntime()

    checkpoint = runtime.run_checkpoint_cycle()

    assert isinstance(checkpoint, dict)
    assert "action" in checkpoint

    learning = runtime.learning

    assert hasattr(
        learning,
        "record_experience"
    )
