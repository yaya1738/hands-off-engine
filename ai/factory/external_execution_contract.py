"""Stable contract for autonomous Factory development handoff."""

from typing import Any, Dict


REQUIRED_REQUEST_FIELDS = (
    "request_id",
    "task_id",
    "objective",
    "task",
    "execution_mode",
    "mutation_boundary",
    "validation_required",
    "merge_policy",
    "authority",
)


def validate_execution_request(request: Dict[str, Any]) -> Dict[str, Any]:
    missing = [field for field in REQUIRED_REQUEST_FIELDS if field not in request]
    if missing:
        raise ValueError("missing execution request fields: " + ", ".join(missing))

    if request["execution_mode"] != "external_coding_agent_pr":
        raise ValueError("unsupported execution mode")
    if request["mutation_boundary"] != "isolated_branch":
        raise ValueError("mutation must occur on an isolated branch")
    if request["validation_required"] is not True:
        raise ValueError("validation is mandatory")
    if request["merge_policy"] != "factory_validation_required":
        raise ValueError("Factory validation must remain the merge gate")

    return request
