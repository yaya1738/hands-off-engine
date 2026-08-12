from ai.factory.development_execution_adapter import DevelopmentExecutionAdapter


class FakeSink:
    def __init__(self):
        self.requests = []

    def submit(self, request):
        self.requests.append(request)
        return {"accepted": True, "request_id": request["request_id"]}


def test_build_request_is_deterministic_and_requires_authorized_task_identity():
    adapter = DevelopmentExecutionAdapter()
    task = {"id": "task-1", "objective": "repair authority closure"}

    first = adapter.build_request(task)
    second = adapter.build_request(task)

    assert first == second
    assert first["task_id"] == "task-1"
    assert first["execution_mode"] == "external_coding_agent_pr"
    assert first["mutation_boundary"] == "isolated_branch"
    assert first["validation_required"] is True
    assert first["merge_policy"] == "factory_validation_required"


def test_build_request_rejects_missing_identity_or_objective():
    adapter = DevelopmentExecutionAdapter()

    try:
        adapter.build_request({"objective": "x"})
        assert False, "expected missing task identity to fail"
    except ValueError:
        pass

    try:
        adapter.build_request({"id": "task-1"})
        assert False, "expected missing objective to fail"
    except ValueError:
        pass


def test_execute_submits_only_through_explicit_sink():
    sink = FakeSink()
    adapter = DevelopmentExecutionAdapter(sink=sink)

    result = adapter.execute({"id": "task-2", "goal": "close execution loop"})

    assert result["status"] == "EXECUTION_REQUEST_SUBMITTED"
    assert len(sink.requests) == 1
    assert sink.requests[0]["task_id"] == "task-2"


def test_without_sink_never_claims_code_was_executed():
    adapter = DevelopmentExecutionAdapter()

    result = adapter.execute({"id": "task-3", "objective": "improve validation"})

    assert result["status"] == "EXECUTION_REQUEST_READY"
    assert result["handoff"] == "github_coding_agent"
    assert result["request"]["validation_required"] is True
