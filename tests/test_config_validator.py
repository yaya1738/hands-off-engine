from ai.factory.config_validator import (
    FactoryConfigValidator,
)


def test_valid_config():
    validator = FactoryConfigValidator(
        [
            "runtime",
            "scheduler",
        ]
    )

    result = validator.validate(
        {
            "runtime": {},
            "scheduler": {},
        }
    )

    assert result is True
    assert validator.errors() == []


def test_invalid_config():
    validator = FactoryConfigValidator(
        [
            "runtime",
            "scheduler",
        ]
    )

    result = validator.validate(
        {
            "runtime": {},
        }
    )

    assert result is False
    assert "missing:scheduler" in validator.errors()


def test_apply_defaults():
    validator = FactoryConfigValidator()

    config = validator.apply_defaults(
        {},
        {
            "enabled": True,
        },
    )

    assert config["enabled"] is True
