from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

candidates = []

for name in dir(r):
    low = name.lower()
    if any(x in low for x in [
        "verify",
        "validation",
        "outcome",
        "result",
        "assessment",
        "improvement"
    ]):
        candidates.append(name)

print({
    "status": "ANALYZED",
    "native_candidates": candidates,
    "next_action": (
        "CONNECT_NATIVE_VERIFICATION"
        if candidates
        else "DISCOVER_VERIFICATION_OWNER"
    )
})
