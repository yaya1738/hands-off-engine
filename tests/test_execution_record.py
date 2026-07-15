from ai.factory.execution_record import ExecutionRecord


def test_execution_success():
    record = ExecutionRecord(
        task_id="factory-001",
    )

    record.succeed("tests passed")

    assert record.status == "SUCCESS"
    assert "tests passed" in record.outputs


def test_execution_failure():
    record = ExecutionRecord(
        task_id="factory-002",
    )

    record.fail("pytest failed")

    assert record.status == "FAILED"
    assert "pytest failed" in record.outputs
