from ai.factory.telemetry import FactoryTelemetry


def test_telemetry_counts_results():
    telemetry = FactoryTelemetry()

    telemetry.record({"status": "SUCCESS"})
    telemetry.record({"status": "FAILED"})

    result = telemetry.stats()

    assert result["total"] == 2
    assert result["success"] == 1
    assert result["failed"] == 1
