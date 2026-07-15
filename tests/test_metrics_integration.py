from ai.factory.metrics_integration import (
    FactoryMetricsIntegration,
)


class FakeMetrics:
    def __init__(self):
        self.data = {}

    def increment(self, key):
        self.data[key] = self.data.get(
            key,
            0,
        ) + 1

        return {
            key: self.data[key],
        }

    def snapshot(self):
        return self.data


def build():
    return FactoryMetricsIntegration(
        FakeMetrics()
    )


def test_cycle():
    integration = build()

    result = integration.on_cycle()

    assert result["cycles"] == 1


def test_success():
    integration = build()

    result = integration.on_success()

    assert result["successes"] == 1


def test_failure():
    integration = build()

    result = integration.on_failure()

    assert result["failures"] == 1


def test_snapshot():
    integration = build()

    integration.on_cycle()

    result = integration.snapshot()

    assert result["cycles"] == 1


def test_history():
    integration = build()

    integration.on_cycle()

    assert len(integration.history()) == 1
