from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

decision = {
    "decision": "IMPROVE"
}

print(r.action_router.route(decision))
