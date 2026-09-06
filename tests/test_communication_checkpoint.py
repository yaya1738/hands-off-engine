from pathlib import Path


def test_checkpoint_mentions_required_properties():
    text = Path("docs/COMMUNICATION_CHECKPOINT.md").read_text(encoding="utf-8")
    for phrase in (
        "authenticated inbound human messages",
        "durable inbound/outbound correlation IDs",
        "human input is genuinely required",
        "existing authority and approval boundaries",
    ):
        assert phrase in text
