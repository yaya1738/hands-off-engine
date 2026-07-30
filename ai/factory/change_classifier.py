from typing import Any, Dict, List


class FactoryChangeClassifier:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def classify(self, files: List[str]):
        classified = []
        unknown = []

        for file in files:
            path = file.strip()

            if path.startswith("ai/factory/"):
                category = "FACTORY_CAPABILITY"

            elif path.startswith("tests/"):
                category = "TEST_ARTIFACT"

            elif path.startswith("tools/"):
                category = "DEVELOPMENT_TOOL"

            elif (
                path.startswith("apply_")
                or path.startswith("update_")
                or path.startswith("integrate_")
            ):
                category = "MIGRATION_SCRIPT"

            else:
                category = "UNKNOWN"
                unknown.append(path)

            classified.append(
                {
                    "file": path,
                    "category": category,
                }
            )

        result = {
            "classified": classified,
            "unknown": unknown,
            "status": (
                "CLASSIFIED"
                if not unknown
                else "UNKNOWN_FILES"
            ),
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
