import json

from ai.factory.authority_gateway import FactoryAuthorityGateway

factory = FactoryAuthorityGateway()

result = factory.submit_goal(
    "Create a self-maintaining development ingestion layer"
)

print("STATE:")
print(result["state"])

request = result["development_request"]

print("\nGOAL STATUS:")
print(request["goal"]["status"])

print("\nAPPROVAL STATUS:")
print(request["approval"]["status"])

print("\nAUDIT COUNT:")
print(len(factory.runtime.improvement_audit.history()))

print("\nLAST AUDIT TYPE:")
print(
    factory.runtime.improvement_audit.history()[-1]["type"]
)
