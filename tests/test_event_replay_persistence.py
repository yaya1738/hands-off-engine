import os
import tempfile

from ai.factory.event_replay import FactoryEventReplay


def test_event_replay_survives_process_boundary():
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "events.jsonl")

        first = FactoryEventReplay(storage_path=path)
        first.store_event({"type": "goal_completed", "goal": "continue"})

        second = FactoryEventReplay(storage_path=path)

        assert second.query_events("goal_completed")["events"] == [
            {"type": "goal_completed", "goal": "continue"}
        ]
