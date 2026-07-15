from ai.factory.result_collector import (
    FactoryResultCollector,
)


def test_collect():
    collector = FactoryResultCollector()

    result = collector.collect(
        {
            "action": "RECOVER",
            "status": "RECOVERED",
        }
    )

    assert result["action"] == "RECOVER"


def test_summary():
    collector = FactoryResultCollector()

    collector.collect(
        {
            "status": "COMPLETED",
        }
    )

    collector.collect(
        {
            "status": "FAILED",
        }
    )

    summary = collector.summarize()

    assert summary["total"] == 2
    assert summary["completed"] == 1


def test_history():
    collector = FactoryResultCollector()

    collector.collect(
        {
            "status": "COMPLETED",
        }
    )

    assert len(collector.history()) == 1
