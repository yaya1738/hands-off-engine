from ai.factory.access_control import (
    FactoryAccessControl,
)


def build():
    return FactoryAccessControl()


def test_register_identity():
    access = build()

    result = access.register_identity(
        "agent",
        {}
    )

    assert result["registered"] is True


def test_grant_permission():
    access = build()

    result = access.grant_permission(
        "agent",
        "execute",
    )

    assert result["granted"] is True


def test_check_permission():
    access = build()

    access.grant_permission(
        "agent",
        "execute",
    )

    result = access.check_permission(
        "agent",
        "execute",
    )

    assert result["allowed"] is True


def test_revoke_permission():
    access = build()

    result = access.revoke_permission(
        "agent",
        "execute",
    )

    assert result["revoked"] is True


def test_history():
    access = build()

    access.register_identity(
        "agent",
        {}
    )

    assert len(access.history()) == 1
