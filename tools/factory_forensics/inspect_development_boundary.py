from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

findings = [
    {
        "objective": "address low success rate",
        "source": "autonomous_improvement",
        "priority": 1
    },
    {
        "objective": "address low improvement impact",
        "source": "autonomous_improvement",
        "priority": 1
    }
]

print({
    "findings": findings,
    "types": [type(x).__name__ for x in findings]
})

print(
    r.development_pipeline.run_development_cycle(findings)
)
