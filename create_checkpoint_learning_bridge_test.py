from pathlib import Path

p = Path("tests/test_checkpoint_learning_bridge.py")

p.write_text(
'''
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
'''
)

print("CHECKPOINT_LEARNING_BRIDGE_TEST_CREATED")
