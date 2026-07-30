from typing import Any, Dict, List


class FactoryChangeScopeAnalyzer:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def analyze(
        self,
        classified_changes: List[Dict[str, Any]],
    ):
        categories = {}
        names = []

        for item in classified_changes:
            category = item.get(
                "category",
                "UNKNOWN",
            )

            categories.setdefault(
                category,
                0,
            )

            categories[category] += 1

            names.append(
                item.get("file", "")
            )

        migration_count = categories.get(
            "MIGRATION_SCRIPT",
            0,
        )

        capability_count = categories.get(
            "FACTORY_CAPABILITY",
            0,
        )

        test_count = categories.get(
            "TEST_ARTIFACT",
            0,
        )

        tool_count = categories.get(
            "DEVELOPMENT_TOOL",
            0,
        )

        if (
            capability_count > 0
            and migration_count <= 15
        ):
            scope = "COHERENT"

            action = "READY_FOR_CHECKPOINT"

        elif migration_count > 15:
            scope = "MIXED"

            action = "SPLIT_CHECKPOINT"

        else:
            scope = "REVIEW"

            action = "INVESTIGATE_SCOPE"

        result = {
            "scope": scope,
            "action": action,
            "component_counts": categories,
            "change_count": len(names),
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
