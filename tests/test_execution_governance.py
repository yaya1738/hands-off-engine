from ai.factory.execution_governance import (
    FactoryExecutionGovernance,
)


class FakeRisk:
    def check_constraints(self, action):
        return {
            "within_constraints": True,
        }

    def approve(self, action):
        return {
            "approved": True,
        }


def fake_executor(action):
    return {
        "status": "EXECUTED",
    }


def build():
    return FactoryExecutionGovernance(
        risk_manager=FakeRisk(),
        executor=fake_executor,
    )


def test_submit():
    governance = build()

    result = governance.submit({})

    assert result["submitted"] is True


def test_validate():
    governance = build()

    result = governance.validate({})

    assert result["within_constraints"] is True


def test_authorize():
    governance = build()

    result = governance.authorize({})

    assert result["approved"] is True


def test_execute():
    governance = build()

    result = governance.execute({})

    assert result["status"] == "EXECUTED"


def test_history():
    governance = build()

    governance.submit({})

    assert len(governance.history()) == 1
