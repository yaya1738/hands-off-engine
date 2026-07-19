from pathlib import Path
import json


INPUT = Path("factory_reporting_entrypoints.json")
OUTPUT = Path("factory_reporting_authority_plan.json")


SCORES = {
    "FactoryRuntime": {
        "report": 5,
        "status": 4,
        "history": 2,
    },
    "FactoryControlPlane": {
        "health": 5,
        "history": 2,
    },
    "FactoryAPI": {
        "dashboard": 3,
        "status": 3,
        "history": 1,
    },
    "FactoryCLI": {
        "status": 2,
        "history": 1,
    },
    "FactoryDashboard": {
        "snapshot": 3,
    },
}


def score_component(component, methods):
    score = 0
    reasons = []

    for method in methods:
        for keyword, value in SCORES.get(
            component,
            {},
        ).items():
            if keyword in method.lower():
                score += value
                reasons.append(
                    {
                        "method": method,
                        "score": value,
                    }
                )

    return score, reasons


def build_plan(data):
    ranked = []

    for entry in data.get(
        "entrypoints",
        [],
    ):
        for component in entry.get(
            "classes",
            [],
        ):
            score, reasons = score_component(
                component,
                entry.get(
                    "methods",
                    [],
                ),
            )

            if score:
                ranked.append(
                    {
                        "component": component,
                        "file": entry.get("file"),
                        "score": score,
                        "reasons": reasons,
                    }
                )

    ranked.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    return {
        "recommended_authority": (
            ranked[0]
            if ranked
            else None
        ),
        "ranked_candidates": ranked,
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

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
