from pathlib import Path

import tools.github_issue_autonomous_ingress as ingress


class FakeQueue:
    instances = []

    def __init__(self, root):
        self.tasks = []
        FakeQueue.instances.append(self)

    def get_all_tasks(self):
        return self.tasks

    def add_task(self, **kwargs):
        task = {"id": "github-task-1", **kwargs}
        self.tasks.append(task)
        return task["id"]


def test_ingest_accepts_only_authenticated_autonomous_issue_prefix(monkeypatch, tmp_path):
    monkeypatch.setattr(ingress, "AutonomousTaskQueue", FakeQueue)
    issues = [
        {"number": 1, "title": "ordinary issue", "body": "ignore", "user": {"login": "member"}},
        {"number": 2, "title": "[autonomous] inspect runtime", "body": "do it", "user": {"login": "member"}, "html_url": "https://github.com/x/y/issues/2"},
        {"number": 3, "title": "[AUTONOMOUS] ignored duplicate", "body": "already done", "user": {"login": "member"}},
        {"number": 4, "title": "[autonomous] pull request", "body": "ignore", "pull_request": {}, "user": {"login": "member"}},
    ]
    monkeypatch.setattr(ingress, "_request", lambda path, token: issues)
    calls = []
    monkeypatch.setattr(ingress, "_mutate", lambda path, token, payload: calls.append((path, payload)))

    count = ingress.ingest("owner/repo", "token", Path(tmp_path))

    assert count == 2
    queue = FakeQueue.instances[-1]
    assert [task["metadata"]["issue_number"] for task in queue.tasks] == [2, 3]
    assert all(task["source"] == "github_issue" for task in queue.tasks)
    assert len(calls) == 2


def test_duplicate_issue_is_not_ingested(monkeypatch, tmp_path):
    monkeypatch.setattr(ingress, "AutonomousTaskQueue", FakeQueue)
    issue = {"number": 7, "title": "[autonomous] repeat", "body": "x", "user": {"login": "member"}}
    monkeypatch.setattr(ingress, "_request", lambda path, token: [issue])
    monkeypatch.setattr(ingress, "_mutate", lambda *args: None)

    first = ingress.ingest("owner/repo", "token", Path(tmp_path))
    second = ingress.ingest("owner/repo", "token", Path(tmp_path))

    assert first == 1
    assert second == 1
