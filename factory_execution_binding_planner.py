from pathlib import Path
import json


INPUT = Path("factory_execution_integration_discovery.json")
OUTPUT = Path("factory_execution_binding_plan.json")


PREFERRED_WORDS = [
    "improvement",
    "pipeline",
    "submit",
    "execute",
    "dispatch",
    "orchestr",
    "run",
]


def score_candidate(candidate):
    score = 0

    for match in candidate.get("matches", []):
        keyword = match.get("keyword", "")

        if keyword in PREFERRED_WORDS:
            score += 1

    return score


def build_plan(data):
    candidates = data.get(
        "execution_candidates",
        []
    )

    ranked = []

    for candidate in candidates:
        ranked.append(
            {
                "file": candidate.get("file"),
                "classes": candidate.get("classes", []),
                "methods": candidate.get("methods", []),
                "matches": candidate.get("matches", []),
                "score": score_candidate(candidate),
            }
        )

    ranked.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    return {
        "recommended_targets": ranked[:10],
        "selection_rule": (
            "highest execution relevance score"
        ),
        "requires_validation": True,
    }


def main():
    data = json.loads(
        INPUT.read_text()
    )

    result = build_plan(data)

    OUTPUT.write_text(
        json.dumps(
            result,
            indent=2,
        )
    )

    print("Execution binding plan complete")
    print(
        json.dumps(
            result,
            indent=2,
        )[:5000]
    )


if __name__ == "__main__":
    main()
