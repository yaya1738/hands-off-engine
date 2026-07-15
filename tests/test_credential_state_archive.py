from autonomous.credentials.intelligence.state_archive import (
    IntelligenceStateArchive,
)


def test_archive():

    archive = IntelligenceStateArchive(
        "state/intelligence/test_archive.jsonl"
    )

    result = archive.archive(
        {
            "situation":
            "attention_required"
        },
        {
            "valid":
            True
        }
    )

    assert result["validated"] is True
    assert result["mode"] == "read_only"
