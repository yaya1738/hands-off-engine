from ai.factory.autonomous_supervisor import (
    FactoryAutonomousSupervisor,
)


def build():
    return FactoryAutonomousSupervisor(
        {
            "runtime": True,
            "learning": True,
        }
    )


def test_health():
    supervisor = build()

    result = supervisor.check_health()

    assert result["healthy"] is True


def test_inspect_pipeline():
    supervisor = build()

    result = supervisor.inspect_pipeline()

    assert result["pipeline_checked"] is True


def test_detect_issues():
    supervisor = build()

    result = supervisor.detect_issues()

    assert result["issues_found"] is False


def test_coordinate_recovery():
    supervisor = build()

    result = supervisor.coordinate_recovery(
        {}
    )

    assert result["recovery_coordinated"] is True


def test_history():
    supervisor = build()

    supervisor.check_health()

    assert len(supervisor.history()) == 1
