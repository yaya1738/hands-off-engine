from ai.factory.execution_intelligence import FactoryExecutionIntelligence


def build():
    return FactoryExecutionIntelligence()


def test_create_execution():
    engine = build()
    result = engine.create_execution("job1", {})
    assert result["created"] is True


def test_start_execution():
    engine = build()
    engine.create_execution("job1", {})
    result = engine.start_execution("job1")
    assert result["started"] is True


def test_track_execution():
    engine = build()
    engine.create_execution("job1", {})
    result = engine.track_execution("job1")
    assert result["tracked"] is True


def test_complete_execution():
    engine = build()
    engine.create_execution("job1", {})
    result = engine.complete_execution("job1")
    assert result["completed"] is True


def test_history():
    engine = build()
    engine.create_execution("job1", {})
    assert len(engine.history()) == 1
