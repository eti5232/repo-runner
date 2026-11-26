"""בדיקות לביטול ריצה. לא דורשות Docker."""
from types import SimpleNamespace

import pytest

from reporunner import cancel, nodes
from reporunner.source import SourceError


class FakeBox:
    """מחליף את הקונטיינר: רושם אם נמחק, ומדמה עצירה שקרתה בזמן השכפול."""

    last = None

    def __init__(self, *args, **kwargs):
        self.name, self.stopped = "reporunner-test", False
        FakeBox.last = self

    def start(self):
        pass

    def stop(self):
        self.stopped = True

    def clone_project(self, url, commit=None):
        cancel._cancelled.add("t-1")  # המשתמשת לחצה "עצור" באמצע


def test_a_run_cancelled_while_cloning_does_not_leave_its_container(monkeypatch):
    monkeypatch.setattr(nodes, "Sandbox", FakeBox)
    monkeypatch.setattr(cancel, "current_thread_id", lambda: "t-1")
    monkeypatch.setattr(cancel, "_cancelled", set())
    with pytest.raises(SourceError, match="בוטלה"):
        nodes.clone_repo({"source": "https://github.com/user/project"})
    assert FakeBox.last.stopped


def test_cancel_removes_only_the_containers_of_that_run(monkeypatch):
    removed, seen = [], {}

    def containers(all, filters):
        seen.update(filters)
        return [SimpleNamespace(remove=lambda force: removed.append(force))]

    client = SimpleNamespace(containers=SimpleNamespace(list=containers))
    monkeypatch.setattr(cancel.docker, "from_env", lambda: client)
    monkeypatch.setattr(cancel, "_cancelled", set())
    assert cancel.cancel("abc") == 1
    assert seen == {"label": "reporunner.thread=abc"}
    assert cancel.is_cancelled("abc") and not cancel.is_cancelled("other")


def test_outside_a_graph_there_is_no_thread_id():
    assert cancel.current_thread_id() is None
