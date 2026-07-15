from typing import Any, Dict


class FactorySnapshotDiff:
    def compare(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any],
    ) -> Dict[str, Any]:

        changes = {}

        keys = set(before.keys()) | set(after.keys())

        for key in keys:
            old = before.get(key)
            new = after.get(key)

            if old != new:
                changes[key] = {
                    "before": old,
                    "after": new,
                }

        return changes

    def changed_fields(
        self,
        diff: Dict[str, Any],
    ):
        return list(diff.keys())

    def summarize(
        self,
        diff: Dict[str, Any],
    ):
        return {
            "changed_count": len(diff),
            "fields": list(diff.keys()),
        }
