from ai.factory.optimization_connector import (
    FactoryOptimizationConnector,
)


def build():
    return FactoryOptimizationConnector()


def test_ingest_performance():
    connector = build()

    result = connector.ingest_performance(
        {
            "score": 1,
        }
    )

    assert result["ingested"] is True


def test_update_metrics():
    connector = build()

    connector.ingest_performance({})

    result = connector.update_metrics()

    assert result["performance_count"] == 1


def test_generate_signal():
    connector = build()

    connector.ingest_performance({})

    result = connector.generate_signal()

    assert result["signal"] == "OPTIMIZE"


def test_empty_signal():
    connector = build()

    result = connector.generate_signal()

    assert result["signal"] == "WAIT"


def test_history():
    connector = build()

    connector.update_metrics()

    assert len(connector.history()) == 1
