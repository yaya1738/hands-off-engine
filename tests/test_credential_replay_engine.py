from autonomous.credentials.intelligence.replay_engine import (
    IntelligenceReplayEngine,
)


def test_replay():

    result = IntelligenceReplayEngine(
        "state/intelligence/test_archive.jsonl"
    ).replay()

    assert result["mode"] == "read_only"
