from ai.factory.authority_gateway import FactoryAuthorityGateway

gateway = FactoryAuthorityGateway()

result = gateway.submit_goal(
    "end to end authority consolidation test"
)

runtime = gateway.runtime

print("GATEWAY STATE:", result.get("state"))

print(
    "TRACKER COUNT:",
    len(runtime.development_tracker.history())
)

print(
    "APPROVAL COUNT:",
    len(runtime.improvement_approval.history())
)

print(
    "QUEUE COUNT:",
    len(runtime.improvement_queue.history())
)

print(
    "ARTIFACT COUNT:",
    len(runtime.artifact_registry.list_artifacts())
)

print(
    "AUDIT COUNT:",
    len(runtime.improvement_audit.history())
)
