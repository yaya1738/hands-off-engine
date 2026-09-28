from security.human_capability_registry import HumanCapabilityRegistry, can_communicate


def test_david_and_carol_are_communication_only():
    registry = HumanCapabilityRegistry()

    for identity in ("David Kaplan", "Carol Kaplan"):
        assert registry.capabilities_for(identity) == {"communicate"}
        assert registry.allowed(identity, "communicate")
        assert not registry.allowed(identity, "execute")
        assert not registry.allowed(identity, "trade")
        assert not registry.allowed(identity, "approve")


def test_unknown_human_defaults_to_no_capability():
    registry = HumanCapabilityRegistry()
    assert registry.capabilities_for("Unknown Person") == frozenset()
    assert not can_communicate("Unknown Person")


def test_private_configuration_can_extend_only_explicitly():
    registry = HumanCapabilityRegistry(
        {"david_kaplan": {"capabilities": ["communicate"]}}
    )
    assert registry.capabilities_for("David Kaplan") == {"communicate"}
