from ai.factory.authority_gateway import FactoryAuthorityGateway

gateway = FactoryAuthorityGateway()

print("AUTHORITY PATH")
print("=" * 30)

print("GATEWAY RUNTIME SAME:")
print(
    gateway.runtime.development_pipeline is
    gateway.pipeline
)

print("GATEWAY REGISTRY SAME:")
print(
    gateway.registry is
    gateway.runtime.artifact_registry
)

result = gateway.submit_goal(
    "authority path verification"
)

print("STATE:")
print(result.get("state"))

print("AUDIT COUNT:")
print(
    len(
        gateway.runtime.improvement_audit.history()
    )
)

print("DONE")
