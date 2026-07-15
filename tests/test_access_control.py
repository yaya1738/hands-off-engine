from ai.factory.access_control import (
    FactoryAccessControl,
)


def build():
    return FactoryAccessControl()


def test_create_identity():
    manager = build()

    result = manager.create_identity(
        "agent",
        {}
    )

    assert result["created"] is True


def test_grant_permission():
    manager = build()

    result = manager.grant_permission(
        "agent",
        "execute",
    )

    assert result["granted"] is True


def test_check_permission():
    manager = build()

    result = manager.check_permission(
        "agent",
        "execute",
    )

    assert result["checked"] is True


def test_revoke_permission():
    manager = build()

    result = manager.revoke_permission(
        "agent",
        "execute",
    )

    assert result["revoked"] is True


def test_history():
    manager = build()

    manager.create_identity(
        "x",
        {}
    )

    assert len(manager.history()) == 1
