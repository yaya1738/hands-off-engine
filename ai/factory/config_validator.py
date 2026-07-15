from typing import Any, Dict, List


class FactoryConfigValidator:
    def __init__(
        self,
        required_sections=None,
    ):
        self.required_sections = (
            required_sections
            or []
        )
        self._errors: List[str] = []

    def validate(
        self,
        config: Dict[str, Any],
    ) -> bool:
        self._errors = []

        for section in self.required_sections:
            if section not in config:
                self._errors.append(
                    f"missing:{section}"
                )

        return len(self._errors) == 0

    def apply_defaults(
        self,
        config: Dict[str, Any],
        defaults: Dict[str, Any],
    ):
        for key, value in defaults.items():
            if key not in config:
                config[key] = value

        return config

    def errors(self):
        return self._errors
