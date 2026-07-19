from ai.factory.authority_gateway import FactoryAuthorityGateway

gateway = FactoryAuthorityGateway()

print(
    "GATEWAY == RUNTIME:",
    gateway.registry is gateway.runtime.artifact_registry
)

print(
    "PIPELINE == RUNTIME:",
    gateway.pipeline.artifact_registry is gateway.runtime.artifact_registry
)

print(
    "COMPLETION == GATEWAY:",
    gateway.completion.registry is gateway.registry
)
