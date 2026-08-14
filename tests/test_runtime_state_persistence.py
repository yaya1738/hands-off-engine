import os
import tempfile

from ai.factory.runtime_state import FactoryRuntimeState


def test_runtime_state_survives_process_boundary():
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "runtime-state.json")

        first = FactoryRuntimeState(storage_path=path)
        first.save_state({"goal": "continue", "completed": 3})
        first.snapshot()

        second = FactoryRuntimeState(storage_path=path)

        assert second.load_state()["state"] == {
            "goal": "continue",
            "completed": 3,
        }
        assert second.history()
