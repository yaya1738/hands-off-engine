from ai.factory.authority_gateway import FactoryAuthorityGateway

gateway = FactoryAuthorityGateway()

print(
    "TRACKER:",
    gateway.tracker is gateway.runtime.development_tracker
)

print(
    "APPROVAL:",
    gateway.approval is gateway.runtime.improvement_approval
)

print(
    "QUEUE:",
    gateway.queue is gateway.runtime.improvement_queue
)
