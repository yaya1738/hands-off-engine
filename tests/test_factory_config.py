from ai.factory.config import (
    FactoryConfig,
)


def test_missing_config(tmp_path):
    config = FactoryConfig(
        str(tmp_path / "config.json")
    )

    result = config.load()

    assert result == {}


def test_load_config(tmp_path):
    path = tmp_path / "config.json"

    path.write_text(
        '{"runtime":{"tick":60}}'
    )

    config = FactoryConfig(
        str(path)
    )

    result = config.load()

    assert result["runtime"]["tick"] == 60


def test_defaults():
    config = FactoryConfig()

    config.set_default(
        "enabled",
        True,
    )

    assert config.get("enabled") is True


def test_validate():
    config = FactoryConfig()

    config.load()

    assert config.validate() is True
