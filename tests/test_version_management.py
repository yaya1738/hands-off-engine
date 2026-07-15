from ai.factory.version_management import (
    FactoryVersionManagement,
)


def build():
    return FactoryVersionManagement()


def test_create_version():
    manager = build()

    result = manager.create_version(
        "v1",
        {}
    )

    assert result["created"] is True


def test_compare_versions():
    manager = build()

    result = manager.compare_versions(
        "v1",
        "v2",
    )

    assert result["compared"] is True


def test_rollback_version():
    manager = build()

    result = manager.rollback_version(
        "v1"
    )

    assert result["rolled_back"] is True


def test_promote_version():
    manager = build()

    result = manager.promote_version(
        "v2"
    )

    assert result["promoted"] is True


def test_history():
    manager = build()

    manager.create_version(
        "v1",
        {}
    )

    assert len(manager.history()) == 1
