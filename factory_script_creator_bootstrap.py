import json
import subprocess
import os


SEARCH_TERMS = [
    "script creator",
    "code generator",
    "artifact creator",
    "development executor",
    "file generator",
    "builder",
]


def search_factory():
    results = []

    for term in SEARCH_TERMS:
        try:
            r = subprocess.run(
                [
                    "grep",
                    "-R",
                    term,
                    "ai/factory",
                    "-n"
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if r.stdout:
                results.append({
                    "term": term,
                    "matches": r.stdout.splitlines()[:10]
                })

        except Exception as e:
            results.append({
                "term": term,
                "error": str(e)
            })

    return results


def classify(results):
    text = json.dumps(results).lower()

    if (
        "generate" in text
        or "create_file" in text
        or "artifact" in text
        or "builder" in text
    ):
        return "existing_script_creator_possible"

    return "no_script_creator_found"


def run():
    discovery = search_factory()

    return {
        "component": "factory_script_creator_bootstrap",
        "discovery": discovery,
        "decision": classify(discovery),
        "next_action": (
            "route_request_to_existing_creator"
            if classify(discovery) == "existing_script_creator_possible"
            else "manual_script_creation_required"
        )
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
