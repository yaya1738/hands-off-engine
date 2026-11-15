"""Regression tests for the self-healing agent's PR-promotion authority boundary."""
import importlib
import inspect
import logging
import re
from pathlib import Path
from unittest.mock import Mock, patch

with patch.object(logging, "FileHandler", lambda *a, **k: logging.NullHandler()):
    module = importlib.import_module("scripts.self_healing_agent")


def make_agent():
    agent = module.SelfHealingAgent.__new__(module.SelfHealingAgent)
    agent.state = {}
    agent.save_state = Mock()
    return agent


def test_arbitrary_promotion_finding_only_records_pending_human_review():
    agent = make_agent()
    issue = {
        "type": "unmerged_branches",
        "description": "6 agent branches need review",
        "severity": "high",
        "auto_fixable": True,
        "fix_action": "propose_human_review",
        "proposal_kind": "agent_branch_review",
    }

    with patch.object(module.subprocess, "run") as run:
        result = agent.attempt_fix(issue)

    assert result is None
    assert run.call_count == 0
    assert len(agent.state["pending_human_review"]) == 1
    proposal = agent.state["pending_human_review"][0]
    assert proposal["kind"] == "agent_branch_review"
    assert proposal["issue_type"] == "unmerged_branches"
    assert proposal["status"] == "pending_human_review"
    assert proposal["created_at"]
    agent.save_state.assert_called_once()


def test_duplicate_human_review_proposals_are_deduplicated():
    agent = make_agent()
    issue = {
        "type": "unmerged_branches",
        "description": "6 branches need review",
        "fix_action": "propose_human_review",
        "proposal_kind": "agent_branch_review",
    }
    agent.attempt_fix(issue)
    agent.attempt_fix(issue)

    assert len(agent.state["pending_human_review"]) == 1
    assert agent.save_state.call_count == 1


def test_legacy_mark_ready_execution_methods_are_absent():
    source = inspect.getsource(module.SelfHealingAgent)
    assert "trigger_mark_ready_workflow" not in source
    assert "_manually_mark_prs_ready" not in source
    assert "markPullRequestReadyForReview" not in source
    assert '"workflow", "run"' not in source
    assert "def _request_conflict_fixes" not in source


def test_mark_ready_workflow_requires_one_explicit_manual_pr():
    workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/mark-ready.yml").read_text()
    assert re.search(r"(?m)^  workflow_dispatch:", workflow)
    assert not re.search(r"(?m)^  pull_request:", workflow)
    assert re.search(r"(?ms)^      pr_number:.*?required: true", workflow)
    assert "process all open draft PRs" not in workflow
    assert "PR_NUM" in workflow
    assert workflow.count("markPullRequestReadyForReview") == 1
    assert "github.event_name == 'workflow_dispatch'" in workflow


def test_coordination_agent_only_queues_exact_draft_prs(tmp_path):
    with patch.object(logging, "FileHandler", lambda *a, **k: logging.NullHandler()):
        coordination = importlib.import_module("scripts.coordination_agent")
    coordination.AI_COORD_DIR = tmp_path
    agent = coordination.CoordinationAgent.__new__(coordination.CoordinationAgent)
    agent.agent_name = "coordination-agent"
    drafts = [
        {"number": n, "author": {"login": "copilot"}, "isDraft": True,
         "title": f"draft {n}", "headRefOid": f"sha-{n}", "url": f"https://github.com/x/y/pull/{n}"}
        for n in (11, 12, 13)
    ]
    drafts.append({"number": 14, "author": {"login": "human"}, "isDraft": True,
                   "title": "human", "headRefOid": "sha-14", "url": "https://example/14"})
    completed = Mock(returncode=0, stdout=__import__("json").dumps(drafts))
    with patch.object(coordination.subprocess, "run", return_value=completed) as run:
        added = agent.check_draft_pr_buildup()

    assert [item["pr_number"] for item in added] == [11, 12, 13]
    assert all(item["status"] == "pending_human_review" for item in added)
    assert run.call_count == 1
    assert run.call_args.args[0][:3] == ["gh", "pr", "list"]
    assert "workflow" not in run.call_args.args[0]
    queue = __import__("json").loads((tmp_path / "promotion_review_queue.json").read_text())
    assert [item["pr_number"] for item in queue["pending"]] == [11, 12, 13]


def test_coordination_agent_deduplicates_same_pr_head_proposal(tmp_path):
    with patch.object(logging, "FileHandler", lambda *a, **k: logging.NullHandler()):
        coordination = importlib.import_module("scripts.coordination_agent")
    coordination.AI_COORD_DIR = tmp_path
    agent = coordination.CoordinationAgent.__new__(coordination.CoordinationAgent)
    drafts = [
        {"number": n, "author": {"login": "copilot"}, "isDraft": True,
         "title": f"draft {n}", "headRefOid": f"sha-{n}", "url": f"https://github.com/x/y/pull/{n}"}
        for n in (21, 22, 23)
    ]
    completed = Mock(returncode=0, stdout=__import__("json").dumps(drafts))
    with patch.object(coordination.subprocess, "run", return_value=completed):
        assert len(agent.check_draft_pr_buildup()) == 3
        assert agent.check_draft_pr_buildup() == []
    queue = __import__("json").loads((tmp_path / "promotion_review_queue.json").read_text())
    assert len(queue["pending"]) == 3


def test_coordination_agent_has_no_workflow_dispatch_call():
    with patch.object(logging, "FileHandler", lambda *a, **k: logging.NullHandler()):
        coordination = importlib.import_module("scripts.coordination_agent")
    source = inspect.getsource(coordination.CoordinationAgent)
    assert '"workflow", "run"' not in source
    assert "workflow run" not in source
    assert "Mark Copilot PRs Ready for Review" not in source
