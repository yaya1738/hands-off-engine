from ai.factory.authority_gateway import FactoryAuthorityGateway

gateway = FactoryAuthorityGateway()

print(
    "PIPELINE SAME:",
    gateway.pipeline is gateway.runtime.development_pipeline
)
