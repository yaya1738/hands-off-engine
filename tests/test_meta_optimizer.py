from ai.factory.meta_optimizer import FactoryMetaOptimizer


def build():
    return FactoryMetaOptimizer()


def test_score():
    engine = build()
    assert engine.score_improvement({})["scored"] is True


def test_compare():
    engine = build()
    assert engine.compare_strategies([])["compared"] is True


def test_select():
    engine = build()
    assert engine.select_best_action([])["selected"] is True


def test_roi():
    engine = build()
    assert engine.measure_roi({})["measured"] is True


def test_history():
    engine = build()
    engine.score_improvement({})
    assert len(engine.history()) == 1
