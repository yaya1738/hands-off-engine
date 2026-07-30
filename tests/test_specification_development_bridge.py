from ai.factory.specification_development_bridge import (
    FactorySpecificationDevelopmentBridge,
)


def test_creates_development_request():

    bridge = FactorySpecificationDevelopmentBridge()

    result = bridge.create_development_request(
        {
            "name": "runtime_lifecycle_coordinator",
            "purpose": "coordinate runtime lifecycle",
            "responsibilities": [
                "startup",
                "shutdown",
            ],
            "dependencies": [
                "factory_runtime",
            ],
        }
    )

    assert result["created"] is True
    assert (
        result["request"]["status"]
        == "DEVELOPMENT_REQUEST_CREATED"
    )


def test_validates_request():

    bridge = FactorySpecificationDevelopmentBridge()

    result = bridge.validate_request(
        {
            "component": "test",
            "purpose": "testing",
            "responsibilities": [
                "execute",
            ],
        }
    )

    assert result["valid"] is True


def test_preserves_implementation_metadata():
    bridge = FactorySpecificationDevelopmentBridge()

    result = bridge.create_development_request(
        {
            "name": "metadata_test",
            "purpose": "test metadata propagation",
            "responsibilities": [
                "execute",
            ],
            "dependencies": [
                "factory_runtime",
            ],
            "integration_points": [
                "submit_development_request",
            ],
            "interfaces": [
                "specification",
                "task",
            ],
            "verification_criteria": [
                "metadata survives bridge",
            ],
            "failure_modes": [
                "missing metadata",
            ],
        }
    )

    request = result["request"]

    assert request["integration_points"] == [
        "submit_development_request",
    ]
    assert request["interfaces"] == [
        "specification",
        "task",
    ]
    assert request["verification_criteria"] == [
        "metadata survives bridge",
    ]
    assert request["failure_modes"] == [
        "missing metadata",
    ]
