from ai.factory.authority_gateway import FactoryAuthorityGateway

gateway = FactoryAuthorityGateway()

runtime = gateway.runtime

print(
    "RUNTIME HAS COMPLETION:",
    hasattr(runtime, "completion")
)

if hasattr(runtime, "completion"):
    print(
        "SAME OBJECT:",
        runtime.completion is gateway.completion
    )
